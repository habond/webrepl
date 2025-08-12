# Multi-Language Web REPL v2.0

[![CI](https://github.com/habond/webrepl/actions/workflows/ci.yml/badge.svg)](https://github.com/habond/webrepl/actions/workflows/ci.yml)
[![Docker Build & Publish](https://github.com/habond/webrepl/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/habond/webrepl/actions/workflows/docker-publish.yml)

A containerized web-based REPL (Read-Eval-Print Loop) supporting multiple programming languages through a modern React interface. Execute code in real-time with persistent session management and comprehensive development tooling.

## 🚀 Features

- **Multi-Language Support**: Python, JavaScript, Ruby, PHP, Kotlin, Haskell, and Bash backends
- **Modern Terminal Interface**: React-based terminal with real-time code execution
- **Intentional Session Management**: Users must create sessions and choose languages before coding
- **Persistent Execution Environments**: Variables and imports persist within each session
- **Keyboard Shortcuts**: Platform-specific hotkeys for rapid session switching
- **Container Architecture**: Fully containerized with Docker Compose orchestration  
- **Environment Configuration**: Comprehensive `.env` file configuration for flexible deployment
- **Development Ready**: Hot reloading, structured logging, and comprehensive testing

## 📋 Supported Languages

| Language   | Backend Technology | Default Port | Configurable |
|------------|-------------------|--------------|--------------|
| Python     | FastAPI           | 8000         | ✅ `BACKEND_PORT` |
| JavaScript | Express.js        | 8000         | ✅ `BACKEND_PORT` |
| Ruby       | Sinatra           | 8000         | ✅ `BACKEND_PORT` |
| PHP        | Built-in Server   | 8000         | ✅ `BACKEND_PORT` |
| Kotlin     | Ktor              | 8000         | ✅ `BACKEND_PORT` |
| Haskell    | Scotty            | 8000         | ✅ `BACKEND_PORT` |
| Bash       | FastAPI/subprocess| 8000         | ✅ `BACKEND_PORT` |

## 🏃‍♂️ Quick Start

### Using Docker (Recommended)

```bash
# Start the application
./control.sh start

# View logs
./control.sh logs -f

# Stop the application
./control.sh stop

# Restart (rebuild and restart)
./control.sh restart
```

Access the application at: http://localhost:8080

## 💡 How to Use

The application requires intentional session creation before you can start coding:

1. **Open the Application**: Navigate to http://localhost:8080
2. **Create Your First Session**: 
   - Click the "Create your first session" button, or
   - Click the "+" button in the session sidebar
3. **Choose Your Language**: Select from Python, JavaScript, Ruby, PHP, Kotlin, Haskell, or Bash
4. **Start Coding**: The terminal activates and you can begin executing code
5. **Persistent Environment**: All variables, functions, and imports remain available within your session
6. **Multiple Sessions**: Create additional sessions for different projects or languages

### ⌨️ Keyboard Shortcuts

Navigate between sessions quickly with platform-specific keyboard shortcuts:

**Mac:**
- `⌘⌥1` through `⌘⌥9` - Switch directly to session 1-9
- `⌘⌥[` - Switch to previous session
- `⌘⌥]` - Switch to next session

**Windows/Linux:**
- `Ctrl+Alt+1` through `Ctrl+Alt+9` - Switch directly to session 1-9
- `Ctrl+Alt+[` - Switch to previous session
- `Ctrl+Alt+]` - Switch to next session

**Terminal Navigation:**
- `Enter` - Execute code
- `Shift+Enter` - New line in multi-line input
- `Arrow Up/Down` - Navigate command history

**Key Benefits**:
- **No Automatic Sessions**: Forces deliberate language choice rather than defaulting
- **Clear Interface**: Terminal is disabled until you create a session, making the workflow obvious  
- **Language Isolation**: Each session maintains its own execution environment
- **Rapid Switching**: Keyboard shortcuts work even when terminal input is focused

## ⚙️ Configuration

### Environment Variables

The application supports comprehensive configuration through environment variables. Default settings are provided in the `.env` file, with an example template in `.env.example`.

#### Core Settings

```bash
# Application Ports
FRONTEND_PORT=8080              # Frontend nginx port  
BACKEND_PORT=8000               # All backend services port
VITE_DEV_PORT=5173             # Vite development server port

# Environment & Security
ENVIRONMENT=development         # development|production
CORS_ORIGINS=http://localhost:8080  # Comma-separated allowed origins
```

#### Service URLs

```bash
# Session Manager
SESSION_MANAGER_URL=http://session-manager:8000

# Language Backends
PYTHON_BACKEND_URL=http://backend-python:8000
JAVASCRIPT_BACKEND_URL=http://backend-javascript:8000  
RUBY_BACKEND_URL=http://backend-ruby:8000
PHP_BACKEND_URL=http://backend-php:8000
KOTLIN_BACKEND_URL=http://backend-kotlin:8000
HASKELL_BACKEND_URL=http://backend-haskell:8000
```

#### Frontend Configuration

```bash
# Vite Environment Variables (prefixed with VITE_)
VITE_SESSION_REFRESH_INTERVAL=30000  # Session refresh rate (ms)
VITE_BACKEND_PORT=8000               # Backend port for display
```

#### Custom Deployment Example

```bash
# Production deployment on different ports
FRONTEND_PORT=3000
BACKEND_PORT=9000
ENVIRONMENT=production
CORS_ORIGINS=https://myapp.com,https://api.myapp.com

# External service integration
SESSION_MANAGER_URL=http://external-session-service:9000
DATABASE_PATH=/mnt/persistent/sessions.db
```

**Getting Started with Configuration:**
```bash
# Use the provided defaults (recommended for development)
./control.sh start

# Or create custom configuration
cp .env.example .env.local
# Edit .env.local with your custom settings
./control.sh restart
```

### Manual Docker Commands

```bash
# Start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🧪 Testing

Backends can be tested by accessing their health endpoints and executing sample code through the API:

```bash
# Check backend health
curl http://localhost:8080/api/python/health
curl http://localhost:8080/api/javascript/health
curl http://localhost:8080/api/ruby/health
curl http://localhost:8080/api/php/health
curl http://localhost:8080/api/kotlin/health
curl http://localhost:8080/api/haskell/health

# Test session manager
curl http://localhost:8080/api/sessions
```

## 🏗️ Architecture

### Container Architecture
- **Frontend**: nginx serving React app with API proxy
- **Session Manager**: SQLite-based session persistence and management
- **Language Backends**: Isolated containers for each programming language
- **Networking**: Bridge network connecting all containers

### API Endpoints
- `POST /api/{language}/execute/{sessionId}` - Execute code
- `POST /api/{language}/reset/{sessionId}` - Reset session
- `GET /api/sessions` - List active sessions
- `POST /api/sessions` - Create new session
- `DELETE /api/sessions/{sessionId}` - Delete session
- `PUT /api/sessions/{sessionId}/rename` - Rename session

### Session Management
Each user session maintains:
- **Isolated execution environments** per language with no cross-session interference
- **Persistent variables and imports** between requests within the same session
- **Intentional creation workflow** requiring explicit language selection
- **Automatic cleanup and metadata tracking** with execution counts and timestamps
- **UUID-based session identification** for reliable session routing
- **No default sessions** - users must explicitly create sessions to start coding

## 🛠️ Development

### Frontend Development
```bash
cd frontend
npm install
npm run dev          # Development server
npm run lint         # ESLint check
npm run build        # Production build
```

### Backend Development (Python Example)
```bash
cd backend/python
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
make dev             # Development server
make check           # Run all checks
make format          # Format code
```

## 📁 Project Structure

```
webrepl/
├── frontend/           # React terminal interface
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── hooks/      # React hooks
│   │   └── services/   # API services
│   └── nginx.conf      # Proxy configuration
├── backend/           # Multi-language backends
│   ├── python/        # Python FastAPI backend
│   ├── javascript/    # Node.js Express backend
│   ├── ruby/          # Ruby Sinatra backend
│   ├── php/           # PHP backend
│   ├── kotlin/        # Kotlin Ktor backend
│   ├── haskell/       # Haskell Scotty backend
│   └── session-manager/ # Session persistence
├── docker-compose.yml # Main orchestration
└── control.sh        # Application control script
```

## 🔒 Security Considerations

This application executes arbitrary code in sandboxed Docker containers. Each backend container has:
- No external network access
- Limited filesystem access
- Isolated execution environments
- Automatic session cleanup

**Warning**: Never expose this application to untrusted networks without additional security measures.

## 📖 Documentation

- [Project Documentation](CLAUDE.md) - Comprehensive development guide
- [Backend Architecture](backend/CLAUDE.md) - Backend implementation details
- [Frontend Architecture](frontend/CLAUDE.md) - Frontend implementation details
- [Session Manager](backend/session-manager/CLAUDE.md) - Session management service details

### Language-Specific Documentation
- [Python Backend](backend/python/CLAUDE.md)
- [JavaScript Backend](backend/javascript/CLAUDE.md)
- [Ruby Backend](backend/ruby/CLAUDE.md)
- [PHP Backend](backend/php/CLAUDE.md)
- [Kotlin Backend](backend/kotlin/CLAUDE.md)
- [Haskell Backend](backend/haskell/CLAUDE.md)
- [Bash Backend](backend/bash/CLAUDE.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes using the health endpoints and API
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

Built with ❤️ using React, Docker, and modern web technologies.