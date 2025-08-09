# Kotlin Backend - Ktor Server REPL v2.0

Ktor server that executes Kotlin code in session-based sandboxed environments with persistent variable contexts.

## Stack

- **Framework**: Ktor 2.3.7 with Netty engine
- **Runtime**: OpenJDK 17 with Kotlin 1.9.21
- **Execution**: Kotlin Script Engine (JSR-223) for code evaluation
- **Container**: openjdk:17-jdk-slim base image (`webrepl-backend-kotlin`)
- **Session Management**: Session-based persistent variable bindings

## Features

- Session-based Kotlin execution with persistent variables per session
- Kotlin script engine integration for safe code evaluation
- Expression evaluation with automatic result display
- Session-specific variable context reset functionality
- Comprehensive error handling and reporting
- Session isolation preventing cross-session variable access

## API Endpoints

### `POST /execute/{sessionId}`
Execute Kotlin code in session-specific persistent context.

**Request:**
```json
{
  "code": "val x = 42\nprintln(x * 2)"
}
```

**Response:**
```json
{
  "output": "84\n",
  "error": null
}
```

### `POST /reset/{sessionId}`
Clear execution context and reset all variables for specific session.

**Response:**
```json
{
  "message": "Namespace reset successfully",
  "sessionId": "uuid"
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "language": "kotlin",
  "version": "2.0.0",
  "stateless": true,
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## Session Architecture

### Persistent Variable Contexts
- Each session ID maintains its own isolated Kotlin script engine bindings
- Variables, values, and function definitions persist between executions
- Sessions are completely isolated from each other
- Context persists until session is reset or container restart

### Session Isolation Example
```kotlin
// Session A
val x = 10
fun greet(name: String) = "Hello, $name!"

// Session B (completely separate)
val x = 20  // Different from Session A's x
val y = 30  // Session A cannot see this variable
```

## Security

- Code execution is isolated within the Kotlin script engine context
- No direct file system access from executed code
- No network access from executed code  
- Each session uses its own isolated variable bindings
- Session contexts prevent cross-session variable access

## Development

### Local Development Setup
```bash
# Build the project
gradle build

# Run development server
gradle run

# Run tests (once server is running)
kotlinc -script test_api.kt
```

### Docker Development
```bash
# Build image
docker build -t webrepl-backend-kotlin .

# Run container
docker run -p 8000:8000 webrepl-backend-kotlin

# Run tests in container
docker exec webrepl-backend-kotlin kotlinc -script test_api.kt
```

## Configuration

- **CORS**: Environment-based configuration
  - Development (`ENVIRONMENT=development`): Allows all origins
  - Production: Restricted to specific frontend origins
- **Port**: 8000 (internal container port)
- **Host**: 0.0.0.0 (binds to all interfaces)
- **Session Storage**: Serialized bindings stored via session manager

## Code Execution Flow

1. Receive POST request with Kotlin code and session ID
2. Get or restore session-specific script engine bindings from session manager
3. Set up output capture using System.out redirection
4. Execute code in session script engine context
5. Capture console output and any exceptions
6. Serialize and save updated bindings back to session manager
7. Return structured response with output/error

## Session Management Implementation

The backend integrates with the centralized session manager:
- Session bindings are serialized to base64-encoded JSON
- Only serializable values (strings, numbers, booleans) are persisted
- Complex objects and functions are not persisted across requests
- Session state is restored from session manager on each execution

```kotlin
// Bindings serialization
private fun serializeBindings(bindings: Map<String, Any?>): String {
    val serializable = bindings.filterValues { value ->
        value == null || value is String || value is Number || value is Boolean
    }
    return Base64.getEncoder().encodeToString(
        json.encodeToString(serializable).toByteArray()
    )
}
```

## Error Handling

- **Compilation Errors**: Kotlin syntax errors caught and returned in `error` field
- **Runtime Errors**: Exceptions during execution caught and returned
- **Script Engine Errors**: JSR-223 engine failures handled gracefully
- **Empty Code**: Returns HTTP 400 with appropriate error message
- **Session Errors**: Invalid session handling with proper error types

## Testing

The test suite (`test_api.kt`) verifies:
- Health check endpoint functionality
- Basic expression evaluation and output capture
- Variable persistence between executions within same session
- Session isolation (different sessions don't share variables)
- Error handling for syntax and runtime errors
- Multi-line code execution with function definitions
- Session reset functionality
- Empty code validation

```bash
# Run tests locally (server must be running)
kotlinc -script test_api.kt

# Run tests in Docker container
docker exec webrepl-backend-kotlin kotlinc -script test_api.kt
```

## Kotlin Capabilities

The REPL supports Kotlin language features including:
- **Variables**: `val`, `var` declarations with type inference
- **Functions**: Function definitions with parameters and return types
- **Data Classes**: Data class declarations and usage
- **Control Flow**: if/when expressions, loops
- **Collections**: List, Set, Map operations with functional APIs
- **String Templates**: String interpolation with `${}` syntax
- **Extension Functions**: Kotlin extension function definitions
- **Type Safety**: Null safety and type checking at runtime

## Build System

- **Build Tool**: Gradle 8.5 with Kotlin DSL
- **JVM Target**: Java 17
- **Dependencies**: Ktor server, Kotlin compiler embeddable, kotlinx.serialization
- **Application Plugin**: Configured for standalone execution

## Limitations

- Complex objects and custom classes are not persisted between executions
- Import statements may not work as expected due to script engine limitations
- Some advanced Kotlin features may have limited support in script context
- Function definitions persist within sessions but may have serialization limitations