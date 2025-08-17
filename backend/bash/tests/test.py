import pytest
import requests
import json
import os

# Test configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TEST_SESSION_ID = "test-session-123"
REQUEST_TIMEOUT = 10  # seconds


class TestBashBackend:
    """Test suite for Bash backend webserver"""

    def _make_request(self, method, endpoint, **kwargs):
        """Helper method to make requests with consistent timeout"""
        url = f"{BASE_URL}{endpoint}"
        kwargs.setdefault('timeout', REQUEST_TIMEOUT)
        return getattr(requests, method)(url, **kwargs)

    def setup_method(self):
        """Setup before each test"""
        # Clean up any existing test session
        try:
            requests.post(f"{BASE_URL}/reset/{TEST_SESSION_ID}", timeout=5)
        except requests.exceptions.RequestException:
            pass

    def teardown_method(self):
        """Cleanup after each test"""
        # Reset test session
        try:
            requests.post(f"{BASE_URL}/reset/{TEST_SESSION_ID}", timeout=5)
        except requests.exceptions.RequestException:
            pass

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bash-backend"

    def test_simple_echo_command(self):
        """Test basic echo command execution"""
        code = "echo 'Hello World'"
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": code},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "Hello World" in data["output"]
        assert data["error"] is None

    def test_pwd_command(self):
        """Test pwd command returns session working directory"""
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "pwd"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert f"/tmp/bash_sessions/{TEST_SESSION_ID}" in data["output"]

    def test_file_operations(self):
        """Test file creation and reading"""
        # Create a file
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "echo 'test content' > testfile.txt"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        # Read the file
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "cat testfile.txt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "test content" in data["output"]

    def test_directory_operations(self):
        """Test directory creation and navigation"""
        # Create directory
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "mkdir testdir"}
        )
        assert response.status_code == 200
        
        # List directory
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "ls -la"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "testdir" in data["output"]

    def test_environment_variables(self):
        """Test environment variable access"""
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "echo $HOME"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output"].strip()  # Should have some output

    def test_error_handling(self):
        """Test command that produces error"""
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "ls /nonexistent"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is not None

    def test_empty_code_validation(self):
        """Test validation of empty code"""
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": ""}
        )
        assert response.status_code == 400

    def test_session_persistence(self):
        """Test that files persist between commands in same session"""
        # Create file in first command
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "echo 'persistent data' > persistent.txt"}
        )
        assert response.status_code == 200
        
        # Read file in second command
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "cat persistent.txt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "persistent data" in data["output"]

    def test_session_isolation(self):
        """Test that different sessions are isolated"""
        session2 = "test-session-456"
        
        try:
            # Create file in first session
            response = requests.post(
                f"{BASE_URL}/execute/{TEST_SESSION_ID}",
                json={"code": "echo 'session1 data' > isolation_test.txt"}
            )
            assert response.status_code == 200
            
            # Try to read file from second session (should fail)
            response = requests.post(
                f"{BASE_URL}/execute/{session2}",
                json={"code": "cat isolation_test.txt"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is not None  # Should not find the file
            
        finally:
            # Cleanup second session
            try:
                requests.post(f"{BASE_URL}/reset/{session2}", timeout=5)
            except requests.exceptions.RequestException:
                pass

    def test_pipe_operations(self):
        """Test bash pipe operations"""
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "echo 'hello world' | wc -w"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "2" in data["output"]  # "hello world" has 2 words

    def test_session_reset(self):
        """Test session reset functionality"""
        # Create a file
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "echo 'will be deleted' > temp.txt"}
        )
        assert response.status_code == 200
        
        # Reset session
        response = requests.post(f"{BASE_URL}/reset/{TEST_SESSION_ID}")
        assert response.status_code == 200
        
        # Try to read file (should fail after reset)
        response = requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "cat temp.txt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is not None

    def test_list_sessions(self):
        """Test listing active sessions"""
        # Execute a command to create session
        requests.post(
            f"{BASE_URL}/execute/{TEST_SESSION_ID}",
            json={"code": "echo 'create session'"}
        )
        
        # List sessions
        response = requests.get(f"{BASE_URL}/sessions")
        assert response.status_code == 200
        data = response.json()
        
        # Should find our test session
        session_ids = [s["id"] for s in data["sessions"]]
        assert TEST_SESSION_ID in session_ids

    def test_streaming_endpoint_basic(self):
        """Test streaming endpoint basic functionality"""
        # Test with simple command
        response = requests.post(
            f"{BASE_URL}/execute-stream/{TEST_SESSION_ID}",
            json={"code": "echo 'streaming test'"},
            headers={"Accept": "text/event-stream"},
            stream=True
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Collect streamed events
        events = []
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                event_data = json.loads(line[6:])  # Remove "data: " prefix
                events.append(event_data)
        
        # Should have output event and complete event
        output_events = [e for e in events if e["type"] == "output"]
        complete_events = [e for e in events if e["type"] == "complete"]
        
        assert len(output_events) > 0
        assert len(complete_events) == 1
        assert complete_events[0]["returnCode"] == 0

    def test_streaming_with_loop(self):
        """Test streaming endpoint with time-based loop"""
        # Test with command that produces output over time
        response = requests.post(
            f"{BASE_URL}/execute-stream/{TEST_SESSION_ID}",
            json={"code": "for i in {1..3}; do echo 'Line $i'; sleep 0.1; done"},
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=10
        )
        
        assert response.status_code == 200
        
        # Collect events
        events = []
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                events.append(event_data)
        
        # Should have multiple output events for each line
        output_events = [e for e in events if e["type"] == "output"]
        complete_events = [e for e in events if e["type"] == "complete"]
        
        assert len(output_events) >= 3  # At least 3 lines of output
        assert len(complete_events) == 1
        assert complete_events[0]["returnCode"] == 0


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v"])