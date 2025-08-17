import pytest
import requests
import json
import os
import uuid
import time

# Test configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SESSION_MANAGER_URL = os.getenv("SESSION_MANAGER_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 10  # seconds


class TestPHPBackend:
    """Test suite for PHP backend webserver"""

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
                    "language": "php"
                },
                timeout=5
            )
            if response.status_code not in (200, 201):
                raise Exception(f"Failed to create session: {response.status_code} - {response.text}")
            
            # Use the session ID returned by the session manager
            session_data = response.json()
            self.test_session_id = session_data["id"]
            assert session_data["language"] == "php"
        except Exception as e:
            pytest.fail(f"Failed to setup test session: {e}")

    def teardown_method(self):
        """Cleanup after each test - delete the test session"""
        try:
            requests.delete(f"{SESSION_MANAGER_URL}/sessions/{self.test_session_id}", timeout=5)
        except:
            pass  # Ignore cleanup errors

    def test_health_endpoint(self):
        """Test that the health endpoint returns correct status"""
        response = requests.get(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["language"] == "php"
        assert "version" in data
        assert "timestamp" in data

    def test_basic_execution(self):
        """Test basic PHP code execution"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "echo 'Hello, World!';"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "Hello, World!"
        assert data["error"] is None

    def test_variable_assignment_and_persistence(self):
        """Test that variables persist between executions"""
        # Set a variable
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "$x = 42;"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        # Use the variable in another execution
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "echo $x;"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "42"
        assert data["error"] is None

    def test_function_definition(self):
        """Test that functions can be defined and called in single execution"""
        # Define and call function in same execution
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "function greet($name) { return 'Hello, ' . $name . '!'; } echo greet('PHP');"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "Hello, PHP!"
        assert data["error"] is None

    def test_class_definition_and_usage(self):
        """Test class definition and object creation in single execution"""
        # Define class and create instance in same execution
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": """
class Person {
    public $name;
    public $age;
    
    public function __construct($name, $age) {
        $this->name = $name;
        $this->age = $age;
    }
    
    public function greeting() {
        return "Hi, I'm {$this->name} and I'm {$this->age} years old";
    }
}
$person = new Person('Alice', 30); 
echo $person->greeting();
            """},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "Hi, I'm Alice and I'm 30 years old" in data["output"]
        assert data["error"] is None

    def test_array_operations(self):
        """Test array creation and manipulation"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "$arr = [1, 2, 3, 4, 5]; echo implode(', ', $arr);"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "1, 2, 3, 4, 5"
        assert data["error"] is None

    def test_associative_arrays(self):
        """Test associative array operations"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "$data = ['name' => 'Bob', 'age' => 25]; echo $data['name'] . ' is ' . $data['age'] . ' years old';"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "Bob is 25 years old"
        assert data["error"] is None

    def test_built_in_functions(self):
        """Test PHP built-in functions"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "echo strlen('Hello, World!');"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "13"
        assert data["error"] is None

    def test_string_operations(self):
        """Test string manipulation functions"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "$text = 'Hello World'; echo strtoupper(strrev($text));"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "DLROW OLLEH"
        assert data["error"] is None

    def test_control_structures(self):
        """Test if statements and loops"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "for ($i = 1; $i <= 3; $i++) { echo $i . ' '; }"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "1 2 3 "
        assert data["error"] is None

    def test_json_operations(self):
        """Test JSON encoding and decoding"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "$array = ['key' => 'value', 'number' => 42]; echo json_encode($array);"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        # Parse the JSON to verify it's valid
        json_result = json.loads(data["output"])
        assert json_result["key"] == "value"
        assert json_result["number"] == 42
        assert data["error"] is None

    def test_expression_evaluation(self):
        """Test that expressions return values"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "2 + 2"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        # PHP should evaluate the expression and return the result
        assert "4" in data["output"]
        assert data["error"] is None

    def test_syntax_error_handling(self):
        """Test that syntax errors are properly caught"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "echo 'missing semicolon'"},
            timeout=REQUEST_TIMEOUT
        )
        # This might not be a syntax error in PHP, let's try a real syntax error
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "if (true { echo 'missing closing parenthesis'; }"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["error"] is not None
        assert "error" in data["error"].lower() or "parse" in data["error"].lower()

    def test_runtime_error_handling(self):
        """Test that runtime errors are properly caught"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "echo $undefined_variable;"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        # PHP might not throw error for undefined variables, let's try division by zero
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "throw new Exception('Test exception');"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["error"] is not None
        assert "exception" in data["error"].lower()

    def test_session_isolation(self):
        """Test that different sessions don't share variables"""
        # Create another session for comparison
        other_session_id = str(uuid.uuid4())
        response = requests.post(
            f"{SESSION_MANAGER_URL}/sessions",
            json={
                "name": f"Other Session {other_session_id[:8]}",
                "language": "php"
            },
            timeout=5
        )
        if response.status_code in (200, 201):
            session_data = response.json()
            other_session_id = session_data["id"]
        
        try:
            # Set variable in first session
            response = requests.post(
                f"{BASE_URL}/execute/{self.test_session_id}",
                json={"code": "$isolation_test = 'session1';"},
                timeout=REQUEST_TIMEOUT
            )
            assert response.status_code == 200
            
            # Try to access it from second session (should fail or be empty)
            response = requests.post(
                f"{BASE_URL}/execute/{other_session_id}",
                json={"code": "echo isset($isolation_test) ? $isolation_test : 'not_found';"},
                timeout=REQUEST_TIMEOUT
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["output"] == "not_found"
            assert data["error"] is None
        finally:
            # Clean up other session
            requests.delete(f"{SESSION_MANAGER_URL}/sessions/{other_session_id}", timeout=5)

    def test_session_reset(self):
        """Test that session reset clears variables"""
        # Set a variable
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "$reset_test = 'should_be_cleared';"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        # Reset the session
        response = requests.post(
            f"{BASE_URL}/reset/{self.test_session_id}",
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "reset" in data["message"].lower()
        
        # Try to access the variable (should be gone)
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "echo isset($reset_test) ? $reset_test : 'variable_cleared';"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "variable_cleared"
        assert data["error"] is None

    def test_empty_code_validation(self):
        """Test that empty code returns appropriate error"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": ""},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 400
        
        data = response.json()
        assert data["error"] is not None
        assert "empty" in data["error"].lower()

    def test_whitespace_only_code_validation(self):
        """Test that whitespace-only code returns appropriate error"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "   \n\t  "},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 400
        
        data = response.json()
        assert data["error"] is not None
        assert "empty" in data["error"].lower()

    def test_complex_php_features(self):
        """Test advanced PHP features like closures"""
        response = requests.post(
            f"{BASE_URL}/execute/{self.test_session_id}",
            json={"code": "$numbers = [1, 2, 3, 4, 5]; $doubled = array_map(function($n) { return $n * 2; }, $numbers); echo implode(', ', $doubled);"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["output"] == "2, 4, 6, 8, 10"
        assert data["error"] is None

    def test_wrong_session_language(self):
        """Test behavior when session is created for different language"""
        # Create a session for a different language
        wrong_session_id = str(uuid.uuid4())
        response = requests.post(
            f"{SESSION_MANAGER_URL}/sessions",
            json={
                "name": f"Wrong Language Session {wrong_session_id[:8]}",
                "language": "python"  # Different language!
            },
            timeout=5
        )
        
        try:
            if response.status_code in (200, 201):
                # Try to execute PHP code in a Python session
                response = requests.post(
                    f"{BASE_URL}/execute/{wrong_session_id}",
                    json={"code": "echo 'This should fail';"},
                    timeout=REQUEST_TIMEOUT
                )
                assert response.status_code == 400
                
                data = response.json()
                assert data["error"] is not None
                assert "not configured for php" in data["error"].lower()
        finally:
            # Clean up wrong session
            requests.delete(f"{SESSION_MANAGER_URL}/sessions/{wrong_session_id}", timeout=5)

    def test_invalid_session_handling(self):
        """Test behavior with non-existent session ID"""
        fake_session_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/execute/{fake_session_id}",
            json={"code": "echo 'test';"},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 400
        
        data = response.json()
        assert data["error"] is not None
        assert "not configured for php" in data["error"].lower()