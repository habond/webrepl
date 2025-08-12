# Frontend - React Multi-Language REPL Interface v2.0

React application providing a web-based terminal interface for multi-language REPL with session management and persistent execution contexts.

## Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite with HMR and ESLint rules
- **Styling**: CSS with terminal-inspired design (no framework)
- **HTTP Client**: Fetch API
- **Container**: nginx:alpine serving static files
- **Session Management**: UUID-based session routing and persistence

## Features v2.0

- **Multi-Language Support**: Python, JavaScript, Ruby, PHP, Kotlin, Haskell, Perl language selection
- **Session Management**: UUID-based sessions with persistent execution contexts
- **Terminal Interface**: Terminal-style UI with chronological entry history
- **Session Switching**: Create, select, and manage multiple sessions
- **URL Routing**: Each session gets unique URL (`/<sessionId>`)
- **Auto-Focus**: Input field automatically focuses after execution
- **Keyboard Shortcuts**: Enter key execution, terminal-style navigation
- **Real-time Updates**: Auto-scroll to bottom, loading states
- **Session Metadata**: Session names, creation times, execution counts

## Architecture v2.0

### Hook-Based Architecture
The frontend uses three core custom hooks:

**useSessionManager** (`src/hooks/useSessionManager.ts`):
- Manages session CRUD operations via `/api/sessions` endpoints
- Handles session persistence and auto-refresh (30s interval)
- Provides `createSession`, `deleteSession`, `renameSession` methods
- Sessions are NOT stored in localStorage - exist only in backend memory

**useTerminal** (`src/hooks/useTerminal.ts`):
- Manages terminal history, input state, and UI behavior
- Maintains per-session terminal state with automatic cleanup
- Handles Enter key execution, auto-focus, scroll-to-bottom
- Terminal history cached per session, cleared when sessions deleted

**useCodeExecution** (`src/hooks/useCodeExecution.ts`):
- Handles code execution API calls to `/api/{language}/execute/{sessionId}`
- Manages execution loading states and error handling
- Integrates with terminal history via `addEntry` callback

## Component Structure

### Core Components
- `App.tsx`: Main application with session routing and language selection
- `App.css`: Terminal-inspired styling with dark theme
- `main.tsx`: React DOM entry point

### Terminal Interface
- **Entry Types**: `TerminalEntry` with `'input' | 'output' | 'error'` types
- **Chronological Display**: Terminal history shows entries in execution order
- **Session Isolation**: Each session maintains separate terminal history
- **Auto-Scroll**: Terminal automatically scrolls to bottom after execution

## API Integration v2.0

### Session-Based Communication
- **Session APIs**: Communicates with `/api/sessions` for session management  
- **Execution APIs**: `POST /api/{language}/execute/{sessionId}` for code execution
- **Reset APIs**: `POST /api/{language}/reset/{sessionId}` for session reset
- **Proxy Configuration**: nginx routes `/api/{language}/*` to `backend-{language}:8000/*`

### Language Support
- **Python**: `/api/python/execute/{sessionId}`
- **JavaScript**: `/api/javascript/execute/{sessionId}`
- **Ruby**: `/api/ruby/execute/{sessionId}`
- **PHP**: `/api/php/execute/{sessionId}`
- **Kotlin**: `/api/kotlin/execute/{sessionId}`
- **Haskell**: `/api/haskell/execute/{sessionId}`
- **Perl**: `/api/perl/execute/{sessionId}`

## Development

### Development Commands
```bash
# Install dependencies
npm install

# Run development server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
tsc

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix
```

### Code Quality
```bash
# ESLint handles all linting and formatting
npm run lint        # Check code style and formatting
npm run lint:fix    # Auto-fix issues and format code
```

## Configuration

### Vite Configuration
- Uses [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) with Babel for Fast Refresh
- TypeScript configuration with strict type checking
- Development proxy configuration for API calls

### ESLint Configuration
Integrated ESLint configuration handles both linting and formatting:
- TypeScript-aware rules
- React best practices
- Automatic code formatting (no separate Prettier)
- Import sorting and organization

## Build Process

1. TypeScript compilation with strict type checking
2. Vite bundling with optimized production build
3. Static files served by nginx:alpine container
4. nginx proxy configuration routes API calls to backend services
5. Comprehensive `.dockerignore` for optimized build contexts

## UI/UX Design

### Terminal Styling
- **Color Scheme**: Dark terminal theme with blue accents (`#7dd3fc`)
- **Typography**: Monospace fonts for code input and output
- **Visual Hierarchy**: Clear distinction between input, output, and error states
- **Responsive Design**: Works across desktop and mobile devices

### Session Management UI
- **Session Selector**: Dropdown for switching between active sessions
- **Language Selector**: Toggle between Python, JavaScript, Ruby, PHP, Kotlin, Haskell
- **Create Session**: Button to create new isolated sessions
- **Delete Session**: Remove sessions and cleanup state

## Session Routing

### URL-Based Sessions
- Each session has unique URL: `http://localhost:8080/<sessionId>`
- Direct session links are bookmarkable and shareable
- Session ID validation and fallback to default session
- Browser history integration for session navigation

## UI Flow v2.0

1. **Session Creation**: User creates new session or selects existing session
2. **Language Selection**: Choose programming language (Python/JavaScript/Ruby/PHP/Kotlin/Haskell/Perl)
3. **Code Input**: Type code in terminal-style input field
4. **Execution**: Press Enter or click Run button
5. **Session Persistence**: Code execution updates session-specific context
6. **Terminal Display**: Response shows in chronological terminal history
7. **State Preservation**: Variables and functions persist within session

## Terminal Entry Types

```typescript
interface TerminalEntry {
  id: string;
  type: 'input' | 'output' | 'error';
  content: string;
  timestamp: Date;
  language?: string;
}
```

## Error Handling

- **Network Errors**: "Failed to connect to server" with retry options
- **Execution Errors**: Language-specific error messages displayed in terminal
- **Session Errors**: Session not found, creation failures handled gracefully
- **Loading States**: Visual feedback during code execution and API calls

## Performance Optimizations

- **Component Memoization**: Optimized re-rendering for large terminal histories
- **Session State Management**: Efficient session switching without data loss
- **Terminal Scrolling**: Optimized scroll-to-bottom behavior
- **API Caching**: Session metadata cached and refreshed periodically

## Advanced Features

### Session Management
- **Auto-Refresh**: Session list updates every 30 seconds
- **Session Metadata**: Display creation time, execution count, last accessed
- **Session Cleanup**: Automatic cleanup when sessions are deleted
- **Session Isolation**: Complete isolation between different session contexts

### Terminal Functionality  
- **Command History**: Navigate through previous inputs with Arrow Up/Down keys
- **Multi-Line Input**: Support for complex code blocks (Shift+Enter for new line)
- **Copy/Paste**: Terminal supports standard copy/paste operations
- **Keyboard Shortcuts**: Full keyboard navigation support

### Keyboard Shortcuts Implementation

**Session Switching Hotkeys:**
- Implemented in `App.tsx` using global keyboard event listeners
- Platform detection via `navigator.platform` for Mac vs Windows/Linux
- Uses `event.code` property to detect physical keys (avoids Option key special characters issue)

**Mac Shortcuts:**
- `⌘⌥1-9` (Cmd+Option+1-9): Direct session access by index
- `⌘⌥[` / `⌘⌥]` (Cmd+Option+Brackets): Previous/Next session navigation

**Windows/Linux Shortcuts:**
- `Ctrl+Alt+1-9`: Direct session access by index
- `Ctrl+Alt+[` / `Ctrl+Alt+]`: Previous/Next session navigation

**Implementation Details:**
- Hotkeys work even when input field is focused (no blocking for session switching)
- Auto-refocus input after session switch with 50ms delay
- Visual hints in `SessionSwitcher` component show shortcuts next to session names
- Keyboard shortcuts reference panel at bottom of session sidebar
- Uses `code.startsWith('Digit')` to detect number keys reliably across keyboard layouts

## Development Notes

- **TypeScript**: Strict type checking with comprehensive interface definitions
- **React 19**: Uses modern React features including hooks and concurrent rendering
- **State Management**: Custom hooks provide clean separation of concerns
- **Testing**: Ready for test suite integration with React Testing Library
- **Accessibility**: Terminal interface supports keyboard navigation and screen readers