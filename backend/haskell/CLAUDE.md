# Haskell Backend - Scotty-based REPL Server

Haskell backend implementation for the Web REPL using Scotty web framework and the Haskell Interpreter (hint).

## Stack

- **Framework**: Scotty (lightweight Haskell web framework)
- **Interpreter**: hint (Runtime Haskell interpreter using GHC API)
- **Language**: Haskell with GHC 9.4
- **Build System**: Cabal
- **Container**: haskell:9.4 base image

## Architecture

### Core Components

**Main.hs**:
- Scotty web server on port 8000
- Session-based code execution using hint interpreter
- CORS middleware for cross-origin requests
- JSON API with Aeson for serialization

### API Endpoints

#### `GET /health`
Health check endpoint returning server status.

**Response**:
```json
{
  "status": "healthy"
}
```

#### `POST /execute/{sessionId}`
Execute Haskell code in a session-specific context.

**Request**:
```json
{
  "code": "map (*2) [1,2,3,4,5]"
}
```

**Response**:
```json
{
  "output": "[2,4,6,8,10]",
  "error": null
}
```

#### `POST /reset/{sessionId}`
Reset the session execution context.

**Response**:
```json
{
  "message": "Session reset successfully"
}
```

## Code Execution

### Interpreter Configuration
- Uses `hint` library for safe Haskell evaluation
- Imports Prelude by default
- Evaluates expressions and returns string representation
- Captures both successful results and compilation/runtime errors

### Session Management
- Session states stored in IORef with Map structure
- Each session maintains isolated execution context
- Session reset clears the specific session's state

### Error Handling
- Compilation errors returned with full GHC error messages
- Runtime exceptions caught and returned as error strings
- Type errors and syntax errors properly reported

## Dependencies

**Cabal Package Dependencies**:
- `scotty`: Web framework
- `aeson`: JSON serialization
- `text`: Text handling
- `containers`: Data structures (Map)
- `http-types`: HTTP status codes
- `wai-cors`: CORS middleware
- `hint`: Haskell interpreter
- `transformers`: Monad transformers

## Development

### Local Development
```bash
cd backend/haskell
cabal update
cabal build
cabal run haskell-repl
```

### Docker Development
```bash
cd backend/haskell
docker build -t webrepl-backend-haskell .
docker run -p 8000:8000 webrepl-backend-haskell
```

## Container Configuration

### Dockerfile Structure
1. Base image: `haskell:9.4` (includes GHC and Cabal)
2. Working directory: `/app`
3. Dependencies cached via cabal file copy
4. Source code compilation with `cabal build`
5. Exposed port: 8000
6. Runtime: `cabal run haskell-repl`

### Build Optimization
- Cabal file copied first for dependency caching
- Only source changes trigger recompilation
- Multi-stage caching for faster rebuilds

## Security Considerations

### Code Execution Safety
- Code executed in sandboxed interpreter environment
- No filesystem access beyond interpreter scope
- Network access restricted within container
- Timeout protection for long-running computations

### CORS Configuration
- Development mode: Accepts all origins
- Production mode: Restricted to frontend origin
- Configurable via `ENVIRONMENT` variable

## Supported Features

### Language Features
- Pure functional expressions
- Pattern matching
- List comprehensions
- Lambda expressions
- Type inference
- Standard Prelude functions

### Limitations
- No persistent module definitions between executions
- No file I/O operations
- No network operations
- No unsafe operations
- Session state not preserved (stateless evaluation)

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Execute Code
```bash
curl -X POST http://localhost:8000/execute/test-session \
  -H "Content-Type: application/json" \
  -d '{"code": "filter even [1..10]"}'
```

### Expected Output
```json
{
  "output": "[2,4,6,8,10]",
  "error": null
}
```

## Error Examples

### Syntax Error
```json
{
  "code": "map (*2"
}
```
Returns compilation error with line/column information.

### Type Error
```json
{
  "code": "1 + \"hello\""
}
```
Returns type mismatch error from GHC.

### Runtime Error
```json
{
  "code": "head []"
}
```
Returns runtime exception message.

## Performance Notes

- First execution may be slower due to interpreter initialization
- Subsequent executions benefit from warm JIT compilation
- Complex type inference may increase evaluation time
- Large data structures may impact response time

## Future Enhancements

- Persistent session namespaces with variable bindings
- Module imports beyond Prelude
- Multi-line function definitions
- Custom type definitions within sessions
- Execution timeout configuration
- Memory usage limits