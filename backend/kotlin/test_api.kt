#!/usr/bin/env kotlin

@file:DependsOn("io.ktor:ktor-client-core:2.3.7")
@file:DependsOn("io.ktor:ktor-client-cio:2.3.7") 
@file:DependsOn("io.ktor:ktor-client-content-negotiation:2.3.7")
@file:DependsOn("io.ktor:ktor-serialization-kotlinx-json:2.3.7")
@file:DependsOn("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")

import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.util.*

@Serializable
data class CodeRequest(val code: String)

@Serializable
data class CodeResponse(
    val output: String = "",
    val error: String? = null,
    val errorType: String? = null,
    val sessionInfo: Map<String, String>? = null
)

@Serializable
data class HealthResponse(
    val status: String,
    val language: String,
    val version: String,
    val stateless: Boolean,
    val timestamp: String
)

@Serializable
data class ResetResponse(
    val message: String,
    val sessionId: String
)

class KotlinAPITest {
    private val client = HttpClient(CIO) {
        install(ContentNegotiation) {
            json()
        }
    }
    private val baseUrl = "http://localhost:8000"
    private val json = Json { ignoreUnknownKeys = true }

    fun runTests() = runBlocking {
        println("🧪 Running Kotlin REPL API tests...")
        var passed = 0
        var failed = 0

        // Test 1: Health check
        try {
            println("\n📋 Test 1: Health check")
            val response = client.get("$baseUrl/health")
            val health = json.decodeFromString<HealthResponse>(response.bodyAsText())
            
            assert(response.status == HttpStatusCode.OK) { "Expected 200, got ${response.status}" }
            assert(health.status == "ok") { "Expected status 'ok', got '${health.status}'" }
            assert(health.language == "kotlin") { "Expected language 'kotlin', got '${health.language}'" }
            
            println("✅ Health check passed")
            passed++
        } catch (e: Exception) {
            println("❌ Health check failed: ${e.message}")
            failed++
        }

        val sessionId = UUID.randomUUID().toString()

        // Test 2: Simple expression
        try {
            println("\n📋 Test 2: Simple expression")
            val response = client.post("$baseUrl/execute/$sessionId") {
                contentType(ContentType.Application.Json)
                setBody(CodeRequest("2 + 2"))
            }
            val result = json.decodeFromString<CodeResponse>(response.bodyAsText())
            
            assert(response.status == HttpStatusCode.OK) { "Expected 200, got ${response.status}" }
            assert(result.output.trim() == "4") { "Expected '4', got '${result.output.trim()}'" }
            assert(result.error == null) { "Expected no error, got '${result.error}'" }
            
            println("✅ Simple expression passed")
            passed++
        } catch (e: Exception) {
            println("❌ Simple expression failed: ${e.message}")
            failed++
        }

        // Test 3: Print statement
        try {
            println("\n📋 Test 3: Print statement")
            val response = client.post("$baseUrl/execute/$sessionId") {
                contentType(ContentType.Application.Json)
                setBody(CodeRequest("println(\"Hello, World!\")"))
            }
            val result = json.decodeFromString<CodeResponse>(response.bodyAsText())
            
            assert(response.status == HttpStatusCode.OK) { "Expected 200, got ${response.status}" }
            assert(result.output.trim() == "Hello, World!") { "Expected 'Hello, World!', got '${result.output.trim()}'" }
            assert(result.error == null) { "Expected no error, got '${result.error}'" }
            
            println("✅ Print statement passed")
            passed++
        } catch (e: Exception) {
            println("❌ Print statement failed: ${e.message}")
            failed++
        }

        // Test 4: Variable persistence
        try {
            println("\n📋 Test 4: Variable persistence")
            
            // Set a variable
            val response1 = client.post("$baseUrl/execute/$sessionId") {
                contentType(ContentType.Application.Json)
                setBody(CodeRequest("val x = 42"))
            }
            assert(response1.status == HttpStatusCode.OK) { "Failed to set variable" }
            
            // Use the variable
            val response2 = client.post("$baseUrl/execute/$sessionId") {
                contentType(ContentType.Application.Json)
                setBody(CodeRequest("x * 2"))
            }
            val result = json.decodeFromString<CodeResponse>(response2.bodyAsText())
            
            assert(response2.status == HttpStatusCode.OK) { "Expected 200, got ${response2.status}" }
            assert(result.output.trim() == "84") { "Expected '84', got '${result.output.trim()}'" }
            assert(result.error == null) { "Expected no error, got '${result.error}'" }
            
            println("✅ Variable persistence passed")
            passed++
        } catch (e: Exception) {
            println("❌ Variable persistence failed: ${e.message}")
            failed++
        }

        // Test 5: Session isolation
        try {
            println("\n📋 Test 5: Session isolation")
            val sessionId2 = UUID.randomUUID().toString()
            
            // Set variable in first session (should already be set from previous test)
            // Try to access variable from second session (should fail)
            val response = client.post("$baseUrl/execute/$sessionId2") {
                contentType(ContentType.Application.Json)
                setBody(CodeRequest("x"))
            }
            val result = json.decodeFromString<CodeResponse>(response.bodyAsText())
            
            // Should have an error because x is not defined in this session
            assert(result.error != null) { "Expected error accessing undefined variable from different session" }
            
            println("✅ Session isolation passed")
            passed++
        } catch (e: Exception) {
            println("❌ Session isolation failed: ${e.message}")
            failed++
        }

        // Test 6: Error handling
        try {
            println("\n📋 Test 6: Error handling")
            val response = client.post("$baseUrl/execute/$sessionId") {
                contentType(ContentType.Application.Json)
                setBody(CodeRequest("val y = 1 / 0"))
            }
            val result = json.decodeFromString<CodeResponse>(response.bodyAsText())
            
            // Should have an error due to division by zero or compilation error
            assert(result.error != null) { "Expected error for division by zero or invalid syntax" }
            
            println("✅ Error handling passed")
            passed++
        } catch (e: Exception) {
            println("❌ Error handling failed: ${e.message}")
            failed++
        }

        // Test 7: Reset session
        try {
            println("\n📋 Test 7: Reset session")
            val response = client.post("$baseUrl/reset/$sessionId")
            val result = json.decodeFromString<ResetResponse>(response.bodyAsText())
            
            assert(response.status == HttpStatusCode.OK) { "Expected 200, got ${response.status}" }
            assert(result.message.contains("reset")) { "Expected reset message, got '${result.message}'" }
            
            println("✅ Reset session passed")
            passed++
        } catch (e: Exception) {
            println("❌ Reset session failed: ${e.message}")
            failed++
        }

        // Test 8: Empty code
        try {
            println("\n📋 Test 8: Empty code validation")
            val response = client.post("$baseUrl/execute/$sessionId") {
                contentType(ContentType.Application.Json)
                setBody(CodeRequest(""))
            }
            val result = json.decodeFromString<CodeResponse>(response.bodyAsText())
            
            assert(response.status == HttpStatusCode.BadRequest) { "Expected 400, got ${response.status}" }
            assert(result.error != null) { "Expected error for empty code" }
            
            println("✅ Empty code validation passed")
            passed++
        } catch (e: Exception) {
            println("❌ Empty code validation failed: ${e.message}")
            failed++
        }

        // Test 9: Multi-line code
        try {
            println("\n📋 Test 9: Multi-line code")
            val multiLineCode = """
                fun greet(name: String): String {
                    return "Hello, ${'$'}name!"
                }
                greet("Kotlin")
            """.trimIndent()
            
            val response = client.post("$baseUrl/execute/$sessionId") {
                contentType(ContentType.Application.Json)
                setBody(CodeRequest(multiLineCode))
            }
            val result = json.decodeFromString<CodeResponse>(response.bodyAsText())
            
            assert(response.status == HttpStatusCode.OK) { "Expected 200, got ${response.status}" }
            assert(result.output.trim() == "Hello, Kotlin!") { "Expected 'Hello, Kotlin!', got '${result.output.trim()}'" }
            assert(result.error == null) { "Expected no error, got '${result.error}'" }
            
            println("✅ Multi-line code passed")
            passed++
        } catch (e: Exception) {
            println("❌ Multi-line code failed: ${e.message}")
            failed++
        }

        client.close()

        println("\n🏁 Test Results:")
        println("✅ Passed: $passed")
        println("❌ Failed: $failed")
        println("📊 Total: ${passed + failed}")

        if (failed == 0) {
            println("\n🎉 All tests passed!")
        } else {
            println("\n💥 Some tests failed!")
        }
    }
}

// Run the tests
KotlinAPITest().runTests()