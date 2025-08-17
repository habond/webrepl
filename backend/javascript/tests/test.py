import pytest
import requests
import json
import os
import uuid

# Test configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SESSION_MANAGER_URL = os.getenv("SESSION_MANAGER_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 10  # seconds


class TestJavaScriptBackend:
    """Test suite for JavaScript backend webserver"""

    def setup_method(self):
        """Setup before each test - create a test session"""
        # Create a unique test session for each test
        self.test_session_id = str(uuid.uuid4())
        
        # Create session via session manager
        try:
            response = requests.post(
                f"{SESSION_MANAGER_URL}/sessions",
                json={
                    "name": f"Test Session {self.test_session_id[:8]}",
                    "language": "javascript"
                },
                timeout=5
            )
            if response.status_code == 200:
                session_data = response.json()
                self.test_session_id = session_data["id"]
        except requests.exceptions.RequestException:
            # If session creation fails, continue with generated UUID
            pass

    def teardown_method(self):
        """Cleanup after each test - delete the test session"""
        try:
            requests.delete(
                f"{SESSION_MANAGER_URL}/sessions/{self.test_session_id}",
                timeout=5
            )
        except requests.exceptions.RequestException:
            pass

    def _make_request(self, method, endpoint, **kwargs):
        """Helper method to make requests with consistent timeout"""
        url = f"{BASE_URL}{endpoint}"
        kwargs.setdefault('timeout', REQUEST_TIMEOUT)
        return getattr(requests, method)(url, **kwargs)

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["language"] == "javascript"

    def test_simple_console_log(self):
        """Test basic console.log execution"""
        code = "console.log('Hello World');"
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "Hello World" in data["output"]
        assert data["error"] is None

    def test_variable_declaration(self):
        """Test variable declaration and output"""
        code = "const x = 42; console.log(x);"
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "42" in data["output"]
        assert data["error"] is None

    def test_arithmetic_operations(self):
        """Test basic arithmetic and math operations"""
        code = "const result = 10 + 5 * 2; console.log(result);"
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "20" in data["output"]

    def test_function_definition_and_call(self):
        """Test function definition and execution"""
        code = """
        function greet(name) {
            return 'Hello, ' + name + '!';
        }
        console.log(greet('World'));
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "Hello, World!" in data["output"]

    def test_array_operations(self):
        """Test array creation and methods"""
        code = """
        const arr = [1, 2, 3, 4, 5];
        const doubled = arr.map(x => x * 2);
        console.log(doubled);
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "2" in data["output"] and "4" in data["output"] and "10" in data["output"]

    def test_object_operations(self):
        """Test object creation and property access"""
        code = """
        const obj = { name: 'Test', value: 123 };
        console.log(obj.name + ': ' + obj.value);
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "Test: 123" in data["output"]

    def test_error_handling(self):
        """Test JavaScript syntax/runtime error handling"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "undefinedVariable.someMethod();"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is not None
        assert ("ReferenceError" in data["error"] or "TypeError" in data["error"] or 
                "undefined" in data["error"])

    def test_syntax_error_handling(self):
        """Test handling of syntax errors"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "const x = ;"}  # Invalid syntax
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is not None

    def test_empty_code_validation(self):
        """Test validation of empty code"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": ""}
        )
        assert response.status_code == 400

    def test_session_persistence(self):
        """Test that variables persist between executions in same session"""
        # Set variable in first request
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "const persistentVar = 'I persist!';"}
        )
        assert response.status_code == 200
        
        # Use variable in second request
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "console.log(persistentVar);"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "I persist!" in data["output"]

    def test_function_persistence(self):
        """Test that functions persist between executions in same session"""
        # Define function in first request
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "function multiply(a, b) { return a * b; }"}
        )
        assert response.status_code == 200
        
        # Use function in second request
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "console.log(multiply(6, 7));"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "42" in data["output"]

    def test_session_isolation(self):
        """Test that different sessions are isolated"""
        # Create a second session
        session2_id = str(uuid.uuid4())
        try:
            response = requests.post(
                f"{SESSION_MANAGER_URL}/sessions",
                json={
                    "name": f"Test Session 2 {session2_id[:8]}",
                    "language": "javascript"
                },
                timeout=5
            )
            if response.status_code == 200:
                session_data = response.json()
                session2_id = session_data["id"]
        except requests.exceptions.RequestException:
            pass
        
        try:
            # Set variable in first session
            response = requests.post(
                f"{BASE_URL}/execute/{self.test_session_id}",
                json={"code": "const isolatedVar = 'session1';"}
            )
            assert response.status_code == 200
            
            # Try to access variable from second session (should fail)
            response = requests.post(
                f"{BASE_URL}/execute/{session2_id}",
                json={"code": "console.log(isolatedVar);"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is not None  # Should be ReferenceError
            
        finally:
            # Cleanup second session
            try:
                requests.delete(f"{SESSION_MANAGER_URL}/sessions/{session2_id}", timeout=5)
            except requests.exceptions.RequestException:
                pass

    def test_session_reset(self):
        """Test session reset functionality"""
        # Create a variable
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "const resetTestVar = 'will be deleted';"}
        )
        assert response.status_code == 200
        
        # Reset session
        response = requests.post(f"{BASE_URL}/reset/{self.test_session_id}")
        assert response.status_code == 200
        
        # Try to access variable (should fail after reset)
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "console.log(resetTestVar);"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is not None  # Should be ReferenceError

    def test_es6_features(self):
        """Test ES6+ features like arrow functions, destructuring"""
        code = """
        const numbers = [1, 2, 3, 4, 5];
        const [first, second, ...rest] = numbers;
        const squared = numbers.map(n => n * n);
        console.log(`First: ${first}, Second: ${second}, Squared: ${squared}`);
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert "First: 1" in data["output"]
        assert "Second: 2" in data["output"]

    def test_class_definition(self):
        """Test ES6 class definition and usage"""
        code = """
        class Person {
            constructor(name) {
                this.name = name;
            }
            greet() {
                return `Hello, I'm ${this.name}`;
            }
        }
        const person = new Person('Alice');
        console.log(person.greet());
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Hello, I'm Alice" in data["output"]

    def test_promise_basic_usage(self):
        """Test Promise creation and basic usage"""
        code = """
        const promise = new Promise((resolve) => {
            resolve('Promise resolved!');
        });
        promise.then(result => console.log(result));
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Promise resolved!" in data["output"]

    def test_json_operations(self):
        """Test JSON parsing and stringifying"""
        code = """
        const obj = { name: 'test', value: 42 };
        const jsonString = JSON.stringify(obj);
        const parsed = JSON.parse(jsonString);
        console.log(parsed.name + ': ' + parsed.value);
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert "test: 42" in data["output"]

    def test_multiple_console_outputs(self):
        """Test multiple console.log statements in single execution"""
        code = """
        console.log('Line 1');
        console.log('Line 2');
        console.log('Line 3');
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Line 1" in data["output"]
        assert "Line 2" in data["output"]
        assert "Line 3" in data["output"]

    def test_console_error_output(self):
        """Test console.error output capture"""
        code = """
        console.log('Normal output');
        console.error('Error output');
        """
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Normal output" in data["output"]
        assert "Error output" in data["output"]

    def test_expression_evaluation(self):
        """Test that expressions return values when no console output"""
        code = "5 + 3"
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert "8" in data["output"]

    def test_invalid_session_handling(self):
        """Test handling of invalid session ID"""
        invalid_session = "invalid-session-id"
        response = requests.post(
            f"{BASE_URL}/execute/{invalid_session}",
            json={"code": "console.log('test');"}
        )
        # Should return error for invalid session
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is not None
        assert "not configured for JavaScript" in data["error"]


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v"])