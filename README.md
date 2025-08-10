# Multi-Language Web REPL v2.0

[![CI](https://github.com/habond/webrepl/actions/workflows/ci.yml/badge.svg)](https://github.com/habond/webrepl/actions/workflows/ci.yml)
[![Docker Build & Publish](https://github.com/habond/webrepl/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/habond/webrepl/actions/workflows/docker-publish.yml)

A containerized web-based REPL (Read-Eval-Print Loop) supporting multiple programming languages through a modern React interface. Execute code in real-time with persistent session management and comprehensive development tooling.

## 🚀 Features

- **Multi-Language Support**: Python, JavaScript, Ruby, PHP, Kotlin, and Haskell backends
- **Modern Terminal Interface**: React-based terminal with real-time code execution
- **Session Management**: Persistent execution environments with automatic cleanup
- **Container Architecture**: Fully containerized with Docker Compose orchestration
- **Development Ready**: Hot reloading, structured logging, and comprehensive testing

## 📋 Supported Languages

| Language   | Backend Technology | Container Port |
|------------|-------------------|----------------|
| Python     | FastAPI           | 8000          |
| JavaScript | Express.js        | 8000          |
| Ruby       | Sinatra           | 8000          |
| PHP        | Built-in Server   | 8000          |
| Kotlin     | Ktor              | 8000          |
| Haskell    | Scotty            | 8000          |

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
- Isolated execution environments per language
- Persistent variables and imports between requests
- Automatic cleanup and metadata tracking
- UUID-based session identification

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