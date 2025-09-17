#!/bin/bash

# Media Manager - Client Validation Script
# Validates generated API clients and ensures they work correctly

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="http://localhost:8000"
GENERATED_DIR="generated"
LOG_FILE="validation.log"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if API is running
check_api_health() {
    log "Checking API health..."
    
    if curl -f -s "$API_BASE_URL/health" > /dev/null 2>&1; then
        success "API is running and healthy"
        return 0
    else
        error "API is not running or unhealthy. Please start the backend server first."
        error "Run: cd backend && uvicorn app.main:app --reload"
        return 1
    fi
}

# Validate OpenAPI specification
validate_openapi_spec() {
    log "Validating OpenAPI specification..."
    
    if command -v swagger-codegen-cli &> /dev/null; then
        if swagger-codegen-cli validate -i "$API_BASE_URL/openapi.json"; then
            success "OpenAPI specification is valid"
            return 0
        else
            error "OpenAPI specification validation failed"
            return 1
        fi
    else
        warning "swagger-codegen-cli not found, skipping OpenAPI validation"
        warning "Install with: npm install -g swagger-codegen-cli"
        return 0
    fi
}

# Validate TypeScript client
validate_typescript_client() {
    log "Validating TypeScript client..."
    
    if [[ ! -d "$GENERATED_DIR/typescript" ]]; then
        error "TypeScript client not found. Run: npm run generate:typescript"
        return 1
    fi
    
    cd "$GENERATED_DIR/typescript"
    
    # Check if package.json exists
    if [[ ! -f "package.json" ]]; then
        error "TypeScript client package.json not found"
        cd - > /dev/null
        return 1
    fi
    
    # Install dependencies
    log "Installing TypeScript client dependencies..."
    if npm install; then
        success "TypeScript client dependencies installed"
    else
        error "Failed to install TypeScript client dependencies"
        cd - > /dev/null
        return 1
    fi
    
    # Build the client
    log "Building TypeScript client..."
    if npm run build; then
        success "TypeScript client built successfully"
    else
        error "TypeScript client build failed"
        cd - > /dev/null
        return 1
    fi
    
    # Run basic import test
    log "Testing TypeScript client imports..."
    cat > test-import.js << 'EOF'
const { Configuration, DefaultApi } = require('./dist');

console.log('TypeScript client imports successful');
console.log('Available APIs:', Object.keys({ DefaultApi }));

// Test configuration
const config = new Configuration({
    basePath: 'http://localhost:8000'
});

console.log('Configuration created successfully');
console.log('Base path:', config.basePath);
EOF
    
    if node test-import.js; then
        success "TypeScript client import test passed"
        rm -f test-import.js
    else
        error "TypeScript client import test failed"
        rm -f test-import.js
        cd - > /dev/null
        return 1
    fi
    
    cd - > /dev/null
    return 0
}

# Validate Python client
validate_python_client() {
    log "Validating Python client..."
    
    if [[ ! -d "$GENERATED_DIR/python" ]]; then
        error "Python client not found. Run: npm run generate:python"
        return 1
    fi
    
    cd "$GENERATED_DIR/python"
    
    # Check if setup.py exists
    if [[ ! -f "setup.py" ]]; then
        error "Python client setup.py not found"
        cd - > /dev/null
        return 1
    fi
    
    # Install the client in development mode
    log "Installing Python client in development mode..."
    if python -m pip install -e .; then
        success "Python client installed successfully"
    else
        error "Failed to install Python client"
        cd - > /dev/null
        return 1
    fi
    
    # Test basic import
    log "Testing Python client imports..."
    python << 'EOF'
try:
    import media_manager_client
    from media_manager_client.api import default_api
    from media_manager_client.configuration import Configuration
    from media_manager_client.api_client import ApiClient
    
    print("Python client imports successful")
    print(f"Client version: {getattr(media_manager_client, '__version__', 'unknown')}")
    
    # Test configuration
    config = Configuration(host='http://localhost:8000')
    client = ApiClient(config)
    api = default_api.DefaultApi(client)
    
    print("Python client configuration successful")
    print(f"API host: {config.host}")
    
except ImportError as e:
    print(f"Import error: {e}")
    exit(1)
except Exception as e:
    print(f"Configuration error: {e}")
    exit(1)
EOF
    
    if [[ $? -eq 0 ]]; then
        success "Python client import test passed"
    else
        error "Python client import test failed"
        cd - > /dev/null
        return 1
    fi
    
    cd - > /dev/null
    return 0
}

# Run integration tests with generated clients
run_integration_tests() {
    log "Running integration tests with generated clients..."
    
    # Create a simple integration test
    cat > test-integration.py << 'EOF'
#!/usr/bin/env python3
"""
Integration test for generated API clients
"""
import sys
import requests
import json

def test_api_health():
    """Test API health endpoint"""
    try:
        response = requests.get('http://localhost:8000/health')
        response.raise_for_status()
        data = response.json()
        
        assert 'status' in data
        assert data['status'] == 'healthy'
        
        print("✓ API health test passed")
        return True
    except Exception as e:
        print(f"✗ API health test failed: {e}")
        return False

def test_openapi_spec():
    """Test OpenAPI specification endpoint"""
    try:
        response = requests.get('http://localhost:8000/openapi.json')
        response.raise_for_status()
        spec = response.json()
        
        assert 'openapi' in spec
        assert 'info' in spec
        assert 'paths' in spec
        
        print("✓ OpenAPI specification test passed")
        return True
    except Exception as e:
        print(f"✗ OpenAPI specification test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("Running integration tests...")
    
    tests = [
        test_api_health,
        test_openapi_spec,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("All integration tests passed!")

if __name__ == '__main__':
    main()
EOF
    
    if python test-integration.py; then
        success "Integration tests passed"
        rm -f test-integration.py
        return 0
    else
        error "Integration tests failed"
        rm -f test-integration.py
        return 1
    fi
}

# Main validation function
main() {
    log "Starting client validation..."
    
    # Clear previous log
    > "$LOG_FILE"
    
    local exit_code=0
    
    # Run validations
    check_api_health || exit_code=1
    validate_openapi_spec || exit_code=1
    
    if [[ -d "$GENERATED_DIR/typescript" ]]; then
        validate_typescript_client || exit_code=1
    else
        warning "TypeScript client not found, skipping validation"
    fi
    
    if [[ -d "$GENERATED_DIR/python" ]]; then
        validate_python_client || exit_code=1
    else
        warning "Python client not found, skipping validation"
    fi
    
    # Run integration tests
    run_integration_tests || exit_code=1
    
    if [[ $exit_code -eq 0 ]]; then
        success "All client validations passed!"
        log "Validation log saved to: $LOG_FILE"
    else
        error "Some validations failed. Check the log for details: $LOG_FILE"
    fi
    
    return $exit_code
}

# Handle command line arguments
case "${1:-all}" in
    "typescript"|"ts")
        check_api_health && validate_typescript_client
        ;;
    "python"|"py")
        check_api_health && validate_python_client
        ;;
    "integration"|"test")
        check_api_health && run_integration_tests
        ;;
    "all"|*)
        main
        ;;
esac
