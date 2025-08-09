package com.webrepl.kotlin

import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.cors.routing.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.slf4j.LoggerFactory
import java.io.ByteArrayOutputStream
import java.io.PrintStream
import java.time.Instant
import java.util.*
import javax.script.ScriptEngineManager
import javax.script.SimpleBindings

private val logger = LoggerFactory.getLogger("KotlinREPL")
const val SESSION_MANAGER_URL = "http://session-manager:8000"

class KotlinREPLServer {
    private val httpClient = HttpClient(CIO)
    private val scriptEngine = ScriptEngineManager().getEngineByExtension("kts")
    private val json = Json { ignoreUnknownKeys = true }
    
    // In-memory session storage for Kotlin variables (since serialization is complex)
    private val sessionBindings = mutableMapOf<String, SimpleBindings>()

    private suspend fun getSessionBindings(sessionId: String): SimpleBindings {
        return sessionBindings.getOrPut(sessionId) { SimpleBindings() }
    }

    private suspend fun saveSessionBindings(sessionId: String, bindings: SimpleBindings) {
        // Store in local memory
        sessionBindings[sessionId] = bindings
        
        try {
            // Also notify the session manager that we had activity
            httpClient.put("$SESSION_MANAGER_URL/sessions/$sessionId/environment") {
                contentType(ContentType.Application.Json)
                setBody("""{"language": "kotlin", "serialized_data": "memory-stored"}""")
            }
        } catch (e: Exception) {
            logger.warn("Failed to notify session manager: ${e.message}")
        }
    }

    private suspend fun verifySessionLanguage(sessionId: String): Boolean {
        return try {
            val response = httpClient.get("$SESSION_MANAGER_URL/sessions/$sessionId")
            if (response.status == HttpStatusCode.OK) {
                val responseText = response.bodyAsText()
                val jsonElement = json.parseToJsonElement(responseText)
                jsonElement.jsonObject["language"]?.jsonPrimitive?.content == "kotlin"
            } else {
                false
            }
        } catch (e: Exception) {
            logger.warn("Failed to verify session language: ${e.message}")
            false
        }
    }

    private suspend fun notifySessionManager(sessionId: String) {
        try {
            httpClient.put("$SESSION_MANAGER_URL/sessions/$sessionId/activity?language=kotlin")
        } catch (e: Exception) {
            logger.warn("Failed to notify session manager: ${e.message}")
        }
    }

    fun configureRouting(application: Application) {
        application.routing {
            get("/") {
                call.respondText("Kotlin REPL API is running", ContentType.Application.Json)
            }

            get("/health") {
                call.respondText("""{
                    "status": "ok",
                    "language": "kotlin",
                    "version": "2.0.0",
                    "stateless": true,
                    "timestamp": "${Instant.now()}"
                }""", ContentType.Application.Json)
            }

            post("/execute/{sessionId}") {
                val sessionId = call.parameters["sessionId"] ?: ""
                logger.info("Executing code for session ${sessionId.take(8)}...")

                try {
                    // Parse the request body manually
                    val requestText = call.receiveText()
                    val requestJson = json.parseToJsonElement(requestText)
                    val code = requestJson.jsonObject["code"]?.jsonPrimitive?.content
                    
                    if (code.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, """{
                            "output": "",
                            "error": "Code cannot be empty",
                            "errorType": "validation_error"
                        }""")
                        return@post
                    }

                    // Get session bindings (simplified)
                    val bindings = getSessionBindings(sessionId)

                    // Capture output
                    val outputStream = ByteArrayOutputStream()
                    val printStream = PrintStream(outputStream)
                    val originalOut = System.out
                    val originalErr = System.err

                    var result: Any? = null
                    var executionError: String? = null

                    try {
                        System.setOut(printStream)
                        System.setErr(printStream)

                        // Execute the Kotlin code
                        result = scriptEngine?.eval(code, bindings)

                        // Save updated bindings
                        saveSessionBindings(sessionId, bindings)
                        notifySessionManager(sessionId)

                    } catch (e: Exception) {
                        executionError = e.message
                        logger.warn("Execution error in session ${sessionId.take(8)}: ${e.message}")
                    } finally {
                        System.setOut(originalOut)
                        System.setErr(originalErr)
                        printStream.close()
                    }

                    val output = outputStream.toString()
                    var responseOutput = output

                    // If there's a result and no console output, show the result
                    if (result != null && output.trim().isEmpty()) {
                        responseOutput = result.toString() + "\n"
                    }

                    call.respondText("""{
                        "output": "${responseOutput.replace("\"", "\\\"").replace("\n", "\\n")}",
                        "error": ${if (executionError != null) "\"${executionError.replace("\"", "\\\"")}\"" else "null"},
                        "errorType": ${if (executionError != null) "\"execution_error\"" else "null"}
                    }""", ContentType.Application.Json)

                } catch (e: Exception) {
                    logger.error("Server error: ${e.message}")
                    call.respond(HttpStatusCode.InternalServerError, """{
                        "output": "",
                        "error": "Internal server error: ${e.message}",
                        "errorType": "server_error"
                    }""")
                }
            }

            post("/reset/{sessionId}") {
                val sessionId = call.parameters["sessionId"] ?: ""
                logger.info("Resetting session ${sessionId.take(8)}...")

                try {
                    // Clear our local session bindings first
                    sessionBindings.remove(sessionId)
                    
                    val response = httpClient.delete("$SESSION_MANAGER_URL/sessions/$sessionId/environment")
                    when (response.status) {
                        HttpStatusCode.OK -> {
                            call.respondText("""{
                                "message": "Namespace reset successfully",
                                "sessionId": "$sessionId"
                            }""", ContentType.Application.Json)
                        }
                        HttpStatusCode.NotFound -> {
                            call.respond(HttpStatusCode.NotFound, """{
                                "error": "Session $sessionId not found",
                                "errorType": "session_error"
                            }""")
                        }
                        else -> {
                            call.respond(HttpStatusCode.InternalServerError, """{
                                "error": "Failed to reset session environment",
                                "errorType": "server_error"
                            }""")
                        }
                    }
                } catch (e: Exception) {
                    logger.error("Reset error: ${e.message}")
                    call.respond(HttpStatusCode.ServiceUnavailable, """{
                        "error": "Session manager unavailable",
                        "errorType": "server_error"
                    }""")
                }
            }
        }
    }
}

fun main() {
    logger.info("Starting Kotlin REPL API v2.0.0...")
    
    embeddedServer(Netty, port = 8000, host = "0.0.0.0") {
        install(CORS) {
            if (System.getenv("ENVIRONMENT") == "production") {
                allowHost("localhost:8080")
            } else {
                anyHost()
            }
            allowMethod(HttpMethod.Post)
            allowMethod(HttpMethod.Get)
            allowHeader(HttpHeaders.ContentType)
        }

        val server = KotlinREPLServer()
        server.configureRouting(this)
        
    }.start(wait = true)
}