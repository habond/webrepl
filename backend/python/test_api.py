#!/usr/bin/env python3
"""
Test suite for Python REPL backend
Tests the core functionality: execution, persistence, and reset
"""

import json
import requests
import sys
import uuid

BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = str(uuid.uuid4())  # This generates a proper GUID

def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["language"] == "python"
    print("✓ Health check passed")

def test_simple_expression():
    """Test simple expression evaluation"""
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "2 + 2"}
    )
    assert response.status_code == 200
    data = response.json()
    # Python doesn't print expression results without print()
    assert data["error"] is None
    print("✓ Simple expression evaluation passed")

def test_print_output():
    """Test print statement output capture"""
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "print('Hello, Python!')"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "Hello, Python!\n"
    assert data["error"] is None
    print("✓ Print output capture passed")

def test_variable_persistence():
    """Test that variables persist between executions"""
    # Set a variable
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "test_var = 42"}
    )
    assert response.status_code == 200
    
    # Use the variable in another execution
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "print(test_var * 2)"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "84\n"
    assert data["error"] is None
    print("✓ Variable persistence passed")

def test_error_handling():
    """Test error handling for invalid code"""
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "1 / 0"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "ZeroDivisionError" in data["error"]
    print("✓ Error handling passed")

def test_reset_functionality():
    """Test environment reset functionality"""
    # Set a variable
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "reset_test_var = 999"}
    )
    assert response.status_code == 200
    
    # Reset the environment
    response = requests.post(f"{BASE_URL}/reset/{TEST_SESSION_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Namespace reset successfully"
    
    # Try to access the variable (should fail)
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "print(reset_test_var)"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is not None
    assert "NameError" in data["error"]
    print("✓ Reset functionality passed")

def test_multiline_code():
    """Test multiline code execution"""
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": code}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "120\n"
    assert data["error"] is None
    print("✓ Multiline code execution passed")

def test_import_persistence():
    """Test that imports persist between executions"""
    # Import a module
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "import math"}
    )
    assert response.status_code == 200
    
    # Use the imported module
    response = requests.post(
        f"{BASE_URL}/execute/{TEST_SESSION_ID}",
        json={"code": "print(math.pi)"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "3.14159" in data["output"]
    print("✓ Import persistence passed")


def test_session_isolation():
    """Test that different sessions have isolated environments"""
    session1_id = str(uuid.uuid4())
    session2_id = str(uuid.uuid4())
    
    # Set variable in session 1
    response = requests.post(
        f"{BASE_URL}/execute/{session1_id}",
        json={"code": "session_var = 'session1'"}
    )
    assert response.status_code == 200
    
    # Set different variable value in session 2
    response = requests.post(
        f"{BASE_URL}/execute/{session2_id}",
        json={"code": "session_var = 'session2'"}
    )
    assert response.status_code == 200
    
    # Check session 1 still has its value
    response = requests.post(
        f"{BASE_URL}/execute/{session1_id}",
        json={"code": "print(session_var)"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "session1\n"
    
    # Check session 2 has its own value
    response = requests.post(
        f"{BASE_URL}/execute/{session2_id}",
        json={"code": "print(session_var)"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "session2\n"
    
    print("✓ Session isolation passed")

def run_all_tests():
    """Run all tests"""
    print("\n=== Python Backend Test Suite ===\n")
    
    tests = [
        test_health_check,
        test_simple_expression,
        test_print_output,
        test_variable_persistence,
        test_error_handling,
        test_reset_functionality,
        test_multiline_code,
        test_import_persistence,
        test_session_isolation
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except requests.exceptions.ConnectionError:
            print(f"✗ {test.__name__} failed: Could not connect to backend")
            print("  Make sure the Python backend is running on port 8000")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with unexpected error: {e}")
            failed += 1
    
    print(f"\n=== Results: {len(tests) - failed}/{len(tests)} tests passed ===\n")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)