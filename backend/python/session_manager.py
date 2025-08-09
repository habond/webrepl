"""
Session Management Module for Python REPL Backend

Provides centralized session handling with metadata, cleanup, and monitoring.
"""

import time
import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class SessionMetadata:
    """Metadata for a session"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    execution_count: int = 0
    namespace_size: int = 0
    
    def update_access(self) -> None:
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now()
    
    def increment_execution(self) -> None:
        """Increment execution counter"""
        self.execution_count += 1
        self.update_access()


class SessionManager:
    """Centralized session management with automatic cleanup"""
    
    def __init__(self, cleanup_interval: int = 3600, session_timeout: int = 7200):
        """
        Initialize session manager
        
        Args:
            cleanup_interval: How often to run cleanup (seconds)
            session_timeout: How long until a session expires (seconds)
        """
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, SessionMetadata] = {}
        self._cleanup_interval = cleanup_interval
        self._session_timeout = session_timeout
        self._cleanup_thread: Optional[threading.Thread] = None
        self._shutdown = False
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def get_session_namespace(self, session_id: str) -> Dict[str, Any]:
        """Get or create a namespace for the given session"""
        if session_id not in self._sessions:
            self._sessions[session_id] = {}
            self._metadata[session_id] = SessionMetadata(session_id=session_id)
        
        # Update metadata
        self._metadata[session_id].update_access()
        self._metadata[session_id].namespace_size = len(self._sessions[session_id])
        
        return self._sessions[session_id]
    
    def reset_session(self, session_id: str) -> bool:
        """Reset a session's namespace"""
        if session_id in self._sessions:
            self._sessions[session_id].clear()
            self._metadata[session_id].update_access()
            self._metadata[session_id].namespace_size = 0
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Completely remove a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            del self._metadata[session_id]
            return True
        return False
    
    def record_execution(self, session_id: str) -> None:
        """Record that code was executed in this session"""
        if session_id in self._metadata:
            self._metadata[session_id].increment_execution()
    
    def get_session_info(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session metadata"""
        return self._metadata.get(session_id)
    
    def get_all_sessions(self) -> Dict[str, SessionMetadata]:
        """Get metadata for all active sessions"""
        return self._metadata.copy()
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self._sessions)
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count of removed sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, metadata in self._metadata.items():
            if now - metadata.last_accessed > timedelta(seconds=self._session_timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        return len(expired_sessions)
    
    def _start_cleanup_thread(self) -> None:
        """Start the background cleanup thread"""
        def cleanup_worker():
            while not self._shutdown:
                try:
                    removed = self.cleanup_expired_sessions()
                    if removed > 0:
                        print(f"Cleaned up {removed} expired sessions")
                except Exception as e:
                    print(f"Error during session cleanup: {e}")
                
                # Wait for next cleanup interval
                for _ in range(self._cleanup_interval):
                    if self._shutdown:
                        break
                    time.sleep(1)
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def shutdown(self) -> None:
        """Shutdown the session manager"""
        self._shutdown = True
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)


# Global session manager instance
session_manager = SessionManager()