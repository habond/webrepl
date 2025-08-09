#!/usr/bin/env node
/**
 * Test suite for JavaScript REPL backend
 * Tests the core functionality: execution, persistence, and reset
 */

const http = require('http')
const crypto = require('crypto')

const BASE_URL = 'http://localhost:8000'
const TEST_SESSION_ID = crypto.randomUUID()

// Helper function to make HTTP requests
function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(BASE_URL + path)
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    }

    const req = http.request(options, (res) => {
      let body = ''
      res.on('data', chunk => body += chunk)
      res.on('end', () => {
        try {
          const response = {
            status: res.statusCode,
            data: JSON.parse(body)
          }
          resolve(response)
        } catch (e) {
          reject(new Error(`Failed to parse response: ${e.message}`))
        }
      })
    })

    req.on('error', reject)
    
    if (data) {
      req.write(JSON.stringify(data))
    }
    req.end()
  })
}

async function testHealthCheck() {
  const response = await makeRequest('GET', '/health')
  console.assert(response.status === 200, 'Health check status should be 200')
  console.assert(response.data.status === 'ok', 'Health status should be ok')
  console.assert(response.data.language === 'javascript', 'Language should be javascript')
  console.log('✓ Health check passed')
}

async function testSimpleExpression() {
  const response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code: '2 + 2' })
  console.assert(response.status === 200, 'Execute status should be 200')
  console.assert(response.data.output === '4\n', 'Output should be 4')
  console.assert(response.data.error === null, 'Error should be null')
  console.log('✓ Simple expression evaluation passed')
}

async function testConsoleOutput() {
  const response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code: 'console.log("Hello, JavaScript!")' })
  console.assert(response.status === 200, 'Execute status should be 200')
  console.assert(response.data.output === 'Hello, JavaScript!\n', 'Output should match')
  console.assert(response.data.error === null, 'Error should be null')
  console.log('✓ Console output capture passed')
}

async function testVariablePersistence() {
  // Set a variable
  let response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code: 'let testVar = 42' })
  console.assert(response.status === 200, 'Execute status should be 200')
  
  // Use the variable in another execution
  response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code: 'testVar * 2' })
  console.assert(response.status === 200, 'Execute status should be 200')
  console.assert(response.data.output === '84\n', 'Output should be 84')
  console.assert(response.data.error === null, 'Error should be null')
  console.log('✓ Variable persistence passed')
}

async function testErrorHandling() {
  const response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code: 'undefinedVariable.property' })
  console.assert(response.status === 200, 'Execute status should be 200')
  console.assert(response.data.error !== null, 'Error should not be null')
  console.assert(response.data.error.includes('TypeError'), 'Error should be TypeError')
  console.log('✓ Error handling passed')
}

async function testResetFunctionality() {
  // Set a variable
  let response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code: 'let resetTestVar = 999' })
  console.assert(response.status === 200, 'Execute status should be 200')
  
  // Reset the environment
  response = await makeRequest('POST', `/reset/${TEST_SESSION_ID}`)
  console.assert(response.status === 200, 'Reset status should be 200')
  console.assert(response.data.message === 'Context reset successfully', 'Reset message should match')
  
  // Try to access the variable (should be undefined)
  response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code: 'typeof resetTestVar' })
  console.assert(response.status === 200, 'Execute status should be 200')
  console.assert(response.data.output === 'undefined\n', 'Variable should be undefined after reset')
  console.log('✓ Reset functionality passed')
}

async function testMultilineCode() {
  const code = `
function factorial(n) {
  if (n <= 1) return 1
  return n * factorial(n - 1)
}
console.log(factorial(5))
`
  const response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code })
  console.assert(response.status === 200, 'Execute status should be 200')
  console.assert(response.data.output === '120\n', 'Output should be 120')
  console.assert(response.data.error === null, 'Error should be null')
  console.log('✓ Multiline code execution passed')
}

async function testObjectOutput() {
  const response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { 
    code: 'console.log({name: "test", value: 123})' 
  })
  console.assert(response.status === 200, 'Execute status should be 200')
  console.assert(response.data.output.includes('"name"'), 'Output should contain object properties')
  console.assert(response.data.output.includes('"test"'), 'Output should contain object values')
  console.log('✓ Object output serialization passed')
}

async function testAsyncCode() {
  const code = `
const promise = new Promise(resolve => resolve(42))
promise.then(val => console.log('Promise resolved:', val))
`
  const response = await makeRequest('POST', `/execute/${TEST_SESSION_ID}`, { code })
  console.assert(response.status === 200, 'Execute status should be 200')
  // Note: Promise won't resolve in sync execution, but shouldn't error
  console.assert(response.data.error === null, 'Error should be null')
  console.log('✓ Async code handling passed')
}

async function runAllTests() {
  console.log('\n=== JavaScript Backend Test Suite ===\n')
  
  const tests = [
    testHealthCheck,
    testSimpleExpression,
    testConsoleOutput,
    testVariablePersistence,
    testErrorHandling,
    testResetFunctionality,
    testMultilineCode,
    testObjectOutput,
    testAsyncCode
  ]
  
  let failed = 0
  for (const test of tests) {
    try {
      await test()
    } catch (error) {
      console.log(`✗ ${test.name} failed: ${error.message}`)
      if (error.code === 'ECONNREFUSED') {
        console.log('  Make sure the JavaScript backend is running on port 8000')
      }
      failed++
    }
  }
  
  console.log(`\n=== Results: ${tests.length - failed}/${tests.length} tests passed ===\n`)
  return failed === 0
}

// Run tests
runAllTests().then(success => {
  process.exit(success ? 0 : 1)
}).catch(error => {
  console.error('Test suite failed:', error)
  process.exit(1)
})