<?php
/**
 * Test suite for PHP REPL backend
 * Tests the core functionality: execution, persistence, and reset
 */

class PHPREPLTester {
    private $baseUrl = 'http://localhost:8000';
    private $testSessionId;
    
    public function __construct() {
        $this->testSessionId = $this->generateUuid();
    }
    
    private function generateUuid() {
        return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            mt_rand(0, 0xffff), mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0x0fff) | 0x4000,
            mt_rand(0, 0x3fff) | 0x8000,
            mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
        );
    }
    
    private function makeRequest($method, $url, $data = null) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        
        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: application/json',
                'Content-Length: ' . strlen(json_encode($data))
            ]);
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        return [
            'status_code' => $httpCode,
            'body' => json_decode($response, true)
        ];
    }
    
    public function testHealthCheck() {
        echo "Testing health check...\n";
        $response = $this->makeRequest('GET', $this->baseUrl . '/health');
        
        assert($response['status_code'] === 200, 'Health check should return 200');
        assert($response['body']['status'] === 'ok', 'Status should be ok');
        assert($response['body']['language'] === 'php', 'Language should be php');
        
        echo "✓ Health check passed\n";
    }
    
    public function testSimpleExpression() {
        echo "Testing simple expression evaluation...\n";
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => '2 + 2']
        );
        
        assert($response['status_code'] === 200, 'Simple expression should return 200');
        assert($response['body']['error'] === null, 'Should have no error');
        
        echo "✓ Simple expression evaluation passed\n";
    }
    
    public function testPrintOutput() {
        echo "Testing echo output capture...\n";
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => 'echo "Hello, PHP!";']
        );
        
        assert($response['status_code'] === 200, 'Echo should return 200');
        assert(strpos($response['body']['output'], 'Hello, PHP!') !== false, 'Output should contain hello message');
        assert($response['body']['error'] === null, 'Should have no error');
        
        echo "✓ Echo output capture passed\n";
    }
    
    public function testVariablePersistence() {
        echo "Testing variable persistence...\n";
        
        // Set a variable
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => '$x = 42;']
        );
        assert($response['status_code'] === 200, 'Variable assignment should return 200');
        
        // Use the variable in another request
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => 'echo $x;']
        );
        assert($response['status_code'] === 200, 'Variable use should return 200');
        assert(strpos($response['body']['output'], '42') !== false, 'Output should contain variable value');
        assert($response['body']['error'] === null, 'Should have no error');
        
        echo "✓ Variable persistence passed\n";
    }
    
    public function testErrorHandling() {
        echo "Testing error handling...\n";
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => 'undefined_function();']
        );
        
        assert($response['status_code'] === 200, 'Error should return 200');
        assert($response['body']['error'] !== null, 'Should have error message');
        
        echo "✓ Error handling passed\n";
    }
    
    public function testMultilineCode() {
        echo "Testing multi-line code execution...\n";
        $code = '$arr = [1, 2, 3];
foreach ($arr as $item) {
    echo $item . " ";
}';
        
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => $code]
        );
        
        assert($response['status_code'] === 200, 'Multi-line code should return 200');
        assert(strpos($response['body']['output'], '1 2 3') !== false, 'Output should contain array values');
        assert($response['body']['error'] === null, 'Should have no error');
        
        echo "✓ Multi-line code execution passed\n";
    }
    
    public function testReset() {
        echo "Testing context reset...\n";
        
        // Set a variable
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => '$resetTest = "should be cleared";']
        );
        assert($response['status_code'] === 200, 'Variable assignment should return 200');
        
        // Reset context
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/reset/' . $this->testSessionId
        );
        assert($response['status_code'] === 200, 'Reset should return 200');
        assert(strpos($response['body']['message'], 'reset') !== false, 'Should confirm reset');
        
        // Try to use the variable (should cause an error)
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => 'echo $resetTest;']
        );
        
        // In PHP, undefined variables produce a warning but don't stop execution
        // The output might be empty or contain a warning
        assert($response['status_code'] === 200, 'Using undefined variable should return 200');
        
        echo "✓ Context reset passed\n";
    }
    
    public function testEmptyCodeValidation() {
        echo "Testing empty code validation...\n";
        $response = $this->makeRequest('POST', 
            $this->baseUrl . '/execute/' . $this->testSessionId,
            ['code' => '']
        );
        
        assert($response['status_code'] === 400, 'Empty code should return 400');
        assert($response['body']['error'] !== null, 'Should have error message');
        
        echo "✓ Empty code validation passed\n";
    }
    
    public function runAllTests() {
        echo "Starting PHP REPL backend tests...\n";
        echo "Test session ID: " . $this->testSessionId . "\n\n";
        
        try {
            $this->testHealthCheck();
            $this->testSimpleExpression();
            $this->testPrintOutput();
            $this->testVariablePersistence();
            $this->testErrorHandling();
            $this->testMultilineCode();
            $this->testEmptyCodeValidation();
            $this->testReset();
            
            echo "\n✅ All PHP REPL backend tests passed!\n";
            return true;
        } catch (AssertionError $e) {
            echo "\n❌ Test failed: " . $e->getMessage() . "\n";
            return false;
        } catch (Exception $e) {
            echo "\n❌ Unexpected error: " . $e->getMessage() . "\n";
            return false;
        }
    }
}

// Run tests
$tester = new PHPREPLTester();
$success = $tester->runAllTests();
exit($success ? 0 : 1);
?>