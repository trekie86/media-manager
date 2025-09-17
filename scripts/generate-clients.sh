#!/bin/bash

# OpenAPI Client Generation Script
# Generates TypeScript and Python clients from the FastAPI OpenAPI specification

set -e  # Exit on any error

# Configuration
API_URL="http://localhost:8000"
OPENAPI_SPEC_URL="${API_URL}/openapi.json"
OUTPUT_DIR="generated"
TYPESCRIPT_OUTPUT="${OUTPUT_DIR}/typescript-client"
PYTHON_OUTPUT="${OUTPUT_DIR}/python-client"
MOCK_SERVER_OUTPUT="${OUTPUT_DIR}/mock-server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if OpenAPI Generator CLI is installed
check_openapi_generator() {
    if ! command -v openapi-generator-cli &> /dev/null; then
        log_error "OpenAPI Generator CLI is not installed"
        log_info "Install with: npm install -g @openapitools/openapi-generator-cli"
        exit 1
    fi
    log_success "OpenAPI Generator CLI is available"
}

# Check if API is running
check_api_running() {
    log_info "Checking if API is running at ${API_URL}..."
    if ! curl -s "${API_URL}/health" > /dev/null; then
        log_error "API is not running at ${API_URL}"
        log_info "Start the API with: cd backend && uvicorn app.main:app --reload"
        exit 1
    fi
    log_success "API is running and accessible"
}

# Download OpenAPI specification
download_openapi_spec() {
    log_info "Downloading OpenAPI specification..."
    mkdir -p "${OUTPUT_DIR}"
    
    if curl -s "${OPENAPI_SPEC_URL}" -o "${OUTPUT_DIR}/openapi.json"; then
        log_success "OpenAPI specification downloaded to ${OUTPUT_DIR}/openapi.json"
    else
        log_error "Failed to download OpenAPI specification"
        exit 1
    fi
}

# Generate TypeScript client
generate_typescript_client() {
    log_info "Generating TypeScript client..."
    
    # Remove existing output directory
    rm -rf "${TYPESCRIPT_OUTPUT}"
    
    # Generate TypeScript client
    openapi-generator-cli generate \
        -i "${OUTPUT_DIR}/openapi.json" \
        -g typescript-fetch \
        -o "${TYPESCRIPT_OUTPUT}" \
        -c openapi-generator-config.json \
        --additional-properties=typescriptThreePlus=true,supportsES6=true,npmName=@trekie86/media-manager-client
    
    if [ $? -eq 0 ]; then
        log_success "TypeScript client generated in ${TYPESCRIPT_OUTPUT}"
        
        # Install dependencies for the generated client
        log_info "Installing TypeScript client dependencies..."
        cd "${TYPESCRIPT_OUTPUT}"
        npm install
        cd - > /dev/null
        
        log_success "TypeScript client dependencies installed"
    else
        log_error "Failed to generate TypeScript client"
        exit 1
    fi
}

# Generate Python client
generate_python_client() {
    log_info "Generating Python client..."
    
    # Remove existing output directory
    rm -rf "${PYTHON_OUTPUT}"
    
    # Generate Python client
    openapi-generator-cli generate \
        -i "${OUTPUT_DIR}/openapi.json" \
        -g python \
        -o "${PYTHON_OUTPUT}" \
        --additional-properties=packageName=media_manager_client,projectName=media-manager-python-client,packageVersion=1.0.0
    
    if [ $? -eq 0 ]; then
        log_success "Python client generated in ${PYTHON_OUTPUT}"
    else
        log_error "Failed to generate Python client"
        exit 1
    fi
}

# Generate mock server
generate_mock_server() {
    log_info "Generating Node.js Express mock server..."
    
    # Remove existing output directory
    rm -rf "${MOCK_SERVER_OUTPUT}"
    
    # Generate mock server
    openapi-generator-cli generate \
        -i "${OUTPUT_DIR}/openapi.json" \
        -g nodejs-express-server \
        -o "${MOCK_SERVER_OUTPUT}" \
        --additional-properties=serverPort=3001
    
    if [ $? -eq 0 ]; then
        log_success "Mock server generated in ${MOCK_SERVER_OUTPUT}"
        
        # Install dependencies for the mock server
        log_info "Installing mock server dependencies..."
        cd "${MOCK_SERVER_OUTPUT}"
        npm install
        cd - > /dev/null
        
        log_success "Mock server dependencies installed"
        log_info "Start mock server with: cd ${MOCK_SERVER_OUTPUT} && npm start"
    else
        log_error "Failed to generate mock server"
        exit 1
    fi
}

# Main execution
main() {
    log_info "Starting OpenAPI client generation..."
    
    # Pre-flight checks
    check_openapi_generator
    check_api_running
    
    # Download specification
    download_openapi_spec
    
    # Generate clients based on arguments
    if [ "$1" = "typescript" ] || [ "$1" = "all" ] || [ -z "$1" ]; then
        generate_typescript_client
    fi
    
    if [ "$1" = "python" ] || [ "$1" = "all" ]; then
        generate_python_client
    fi
    
    if [ "$1" = "mock" ] || [ "$1" = "all" ]; then
        generate_mock_server
    fi
    
    log_success "Client generation completed!"
    
    # Display usage information
    echo ""
    log_info "Generated clients:"
    [ -d "${TYPESCRIPT_OUTPUT}" ] && echo "  - TypeScript: ${TYPESCRIPT_OUTPUT}"
    [ -d "${PYTHON_OUTPUT}" ] && echo "  - Python: ${PYTHON_OUTPUT}"
    [ -d "${MOCK_SERVER_OUTPUT}" ] && echo "  - Mock Server: ${MOCK_SERVER_OUTPUT}"
    
    echo ""
    log_info "Usage examples:"
    if [ -d "${TYPESCRIPT_OUTPUT}" ]; then
        echo "  TypeScript: import { DefaultApi, Configuration } from './${TYPESCRIPT_OUTPUT}'"
    fi
    if [ -d "${MOCK_SERVER_OUTPUT}" ]; then
        echo "  Mock Server: cd ${MOCK_SERVER_OUTPUT} && npm start"
    fi
}

# Help function
show_help() {
    echo "OpenAPI Client Generation Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  all         Generate all clients (TypeScript, Python, Mock Server) [default]"
    echo "  typescript  Generate only TypeScript client"
    echo "  python      Generate only Python client"
    echo "  mock        Generate only mock server"
    echo "  help        Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - OpenAPI Generator CLI: npm install -g @openapitools/openapi-generator-cli"
    echo "  - API running at ${API_URL}"
    echo ""
}

# Handle arguments
case "$1" in
    help|--help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$1"
        ;;
esac
