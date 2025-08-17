<?php
/**
 * PHP REPL Backend Server v2.0.0
 * Session-based PHP REPL with automatic cleanup and monitoring
 */

ini_set('display_errors', 0);
error_reporting(0);

// Configuration
$port = intval($_ENV['BACKEND_PORT'] ?? '8000');
$host = '0.0.0.0';
$sessionManagerUrl = $_ENV['SESSION_MANAGER_URL'] ?? 'http://session-manager:8000';

// CORS configuration
$environment = $_ENV['ENVIRONMENT'] ?? 'development';
$corsOriginsEnv = $_ENV['CORS_ORIGINS'] ?? 'http://localhost:8080';
$corsOrigins = $environment === 'development' 
    ? ['*'] 
    : explode(',', $corsOriginsEnv);

// Error handling functions
class ErrorHandler {
    public static function handleValidationError($message, $sessionId) {
        return [
            'message' => $message,
            'errorType' => 'validation_error'
        ];
    }
    
    public static function handleExecutionError($error, $sessionId) {
        return [
            'message' => $error,
            'errorType' => 'execution_error'
        ];
    }
    
    public static function handleSessionError($message, $sessionId) {
        return [
            'message' => $message,
            'errorType' => 'session_error'
        ];
    }
    
    public static function handleInternalError($error, $sessionId) {
        return [
            'message' => 'Internal server error',
            'errorType' => 'internal_error'
        ];
    }
    
    public static function formatExecutionResult($output, $error, $sessionId, $sessionInfo = null) {
        $result = [
            'output' => $output ?: '',
            'error' => null,
            'errorType' => null,
            'sessionInfo' => $sessionInfo
        ];
        
        if ($error) {
            $result['error'] = $error;
            $result['errorType'] = 'execution_error';
        }
        
        return $result;
    }
    
    public static function getHttpStatusForErrorType($errorType) {
        $statusMap = [
            'validation_error' => 400,
            'session_error' => 404,
            'execution_error' => 200, // Execution errors are normal responses
            'internal_error' => 500
        ];
        
        return $statusMap[$errorType] ?? 500;
    }
}

// Session management functions
function makeHttpRequest($method, $url, $data = null) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
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
    
    return ['body' => $response, 'status' => $httpCode];
}

function serializeContext($context) {
    try {
        $serialized = serialize($context);
        return base64_encode($serialized);
    } catch (Exception $e) {
        error_log("Failed to serialize context: " . $e->getMessage());
        return '';
    }
}

function deserializeContext($serializedData) {
    try {
        if (empty($serializedData)) {
            return [];
        }
        $decoded = base64_decode($serializedData);
        return unserialize($decoded) ?: [];
    } catch (Exception $e) {
        error_log("Failed to deserialize context: " . $e->getMessage());
        return [];
    }
}

function getSessionContext($sessionId) {
    global $sessionManagerUrl;
    
    $response = makeHttpRequest('GET', "$sessionManagerUrl/sessions/$sessionId/environment");
    
    if ($response['status'] === 200) {
        $data = json_decode($response['body'], true);
        if (isset($data['environment']['serialized_data'])) {
            return deserializeContext($data['environment']['serialized_data']);
        }
    }
    
    return [];
}

function saveSessionContext($sessionId, $context) {
    global $sessionManagerUrl;
    
    $serializedData = serializeContext($context);
    $data = [
        'language' => 'php',
        'serialized_data' => $serializedData
    ];
    
    makeHttpRequest('PUT', "$sessionManagerUrl/sessions/$sessionId/environment", $data);
}

function verifySessionLanguage($sessionId) {
    global $sessionManagerUrl;
    
    $response = makeHttpRequest('GET', "$sessionManagerUrl/sessions/$sessionId");
    
    if ($response['status'] === 200) {
        $data = json_decode($response['body'], true);
        return isset($data['language']) && $data['language'] === 'php';
    }
    
    return false;
}

function notifySessionManager($sessionId) {
    global $sessionManagerUrl;
    
    makeHttpRequest('PUT', "$sessionManagerUrl/sessions/$sessionId/activity?language=php");
}

// Output capturing functions
function captureOutput($code, $context = []) {
    // Extract variables from context into current scope
    foreach ($context as $key => $value) {
        if (is_string($key) && preg_match('/^[a-zA-Z_][a-zA-Z0-9_]*$/', $key)) {
            $$key = $value;
        }
    }
    
    ob_start();
    $error = null;
    $result = null;
    
    try {
        // Try to evaluate as expression first (for REPL-like behavior)
        if (!preg_match('/;\s*$/', trim($code)) && !preg_match('/^\s*(if|for|while|foreach|function|class|switch|try)\s/i', trim($code))) {
            $result = @eval("return $code;");
            if ($result !== null && $result !== false) {
                // Output the result for REPL-like behavior
                echo $result;
            }
        } else {
            // Execute as statement
            eval($code);
        }
    } catch (ParseError $e) {
        $error = "Parse error: " . $e->getMessage();
    } catch (Error $e) {
        $error = "Fatal error: " . $e->getMessage();
    } catch (Exception $e) {
        $error = "Exception: " . $e->getMessage();
    }
    
    $output = ob_get_contents();
    ob_end_clean();
    
    // Capture updated variables back to context
    $newContext = [];
    foreach (get_defined_vars() as $key => $value) {
        if ($key !== 'code' && $key !== 'context' && $key !== 'error' && 
            $key !== 'result' && $key !== 'output' && $key !== 'newContext') {
            $newContext[$key] = $value;
        }
    }
    
    return ['output' => $output, 'error' => $error, 'context' => $newContext];
}

// Handle CORS
function handleCors() {
    global $corsOrigins;
    
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    
    if (in_array('*', $corsOrigins) || in_array($origin, $corsOrigins)) {
        header("Access-Control-Allow-Origin: " . ($corsOrigins[0] === '*' ? '*' : $origin));
        header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
        header("Access-Control-Allow-Headers: Content-Type, Authorization");
        header("Access-Control-Allow-Credentials: true");
    }
    
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(200);
        exit;
    }
}

// Route handling
function handleRequest() {
    global $sessionManagerUrl;
    
    handleCors();
    
    $method = $_SERVER['REQUEST_METHOD'];
    $path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
    $pathParts = explode('/', trim($path, '/'));
    
    // Health check endpoint
    if ($method === 'GET' && $path === '/health') {
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'ok',
            'language' => 'php',
            'version' => '2.0.0',
            'stateless' => true,
            'timestamp' => date('c')
        ]);
        return;
    }
    
    // Execute code endpoint: POST /execute/{sessionId}
    if ($method === 'POST' && count($pathParts) === 2 && $pathParts[0] === 'execute') {
        $sessionId = $pathParts[1];
        
        error_log("Executing code for session " . substr($sessionId, 0, 8) . "...");
        
        // Verify session is configured for PHP
        if (!verifySessionLanguage($sessionId)) {
            http_response_code(400);
            header('Content-Type: application/json');
            echo json_encode([
                'output' => '',
                'error' => "Session $sessionId is not configured for PHP",
                'errorType' => 'session_error'
            ]);
            return;
        }
        
        $input = json_decode(file_get_contents('php://input'), true);
        $code = $input['code'] ?? '';
        
        // Validate input
        if (empty(trim($code))) {
            $errorResponse = ErrorHandler::handleValidationError(
                'Code cannot be empty',
                $sessionId
            );
            http_response_code(ErrorHandler::getHttpStatusForErrorType($errorResponse['errorType']));
            header('Content-Type: application/json');
            echo json_encode([
                'output' => '',
                'error' => $errorResponse['message'],
                'errorType' => $errorResponse['errorType']
            ]);
            return;
        }
        
        // Get session context
        $context = getSessionContext($sessionId);
        
        // Execute code
        $executionResult = captureOutput($code, $context);
        
        // Save updated context
        saveSessionContext($sessionId, $executionResult['context']);
        
        // Notify session manager
        notifySessionManager($sessionId);
        
        // Format result
        $result = ErrorHandler::formatExecutionResult(
            $executionResult['output'],
            $executionResult['error'],
            $sessionId
        );
        
        header('Content-Type: application/json');
        echo json_encode($result);
        return;
    }
    
    // Reset session endpoint: POST /reset/{sessionId}
    if ($method === 'POST' && count($pathParts) === 2 && $pathParts[0] === 'reset') {
        $sessionId = $pathParts[1];
        
        error_log("Resetting session " . substr($sessionId, 0, 8) . "...");
        
        $response = makeHttpRequest('DELETE', "$sessionManagerUrl/sessions/$sessionId/environment");
        
        if ($response['status'] === 200) {
            header('Content-Type: application/json');
            echo json_encode([
                'message' => 'Context reset successfully',
                'sessionId' => $sessionId
            ]);
        } else if ($response['status'] === 404) {
            $errorResponse = ErrorHandler::handleSessionError(
                "Session $sessionId not found",
                $sessionId
            );
            http_response_code(ErrorHandler::getHttpStatusForErrorType($errorResponse['errorType']));
            header('Content-Type: application/json');
            echo json_encode([
                'error' => $errorResponse['message'],
                'errorType' => $errorResponse['errorType']
            ]);
        } else {
            $errorResponse = ErrorHandler::handleInternalError(
                'Failed to reset session environment',
                $sessionId
            );
            http_response_code(ErrorHandler::getHttpStatusForErrorType($errorResponse['errorType']));
            header('Content-Type: application/json');
            echo json_encode([
                'error' => $errorResponse['message'],
                'errorType' => $errorResponse['errorType']
            ]);
        }
        return;
    }
    
    // Default route
    if ($method === 'GET' && $path === '/') {
        header('Content-Type: application/json');
        echo json_encode(['message' => 'PHP REPL API is running']);
        return;
    }
    
    // 404 for unhandled routes
    http_response_code(404);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'Not found']);
}

// Handle the request
handleRequest();
?>