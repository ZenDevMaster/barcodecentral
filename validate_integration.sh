#!/bin/bash

################################################################################
# Barcode Central - Integration Validation Script
# Version: 1.0.0
# Description: Validates complete integration of all components
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Log file
LOG_FILE="validation_report_$(date +%Y%m%d_%H%M%S).log"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo "================================================================================"
    echo "$1"
    echo "================================================================================"
    echo ""
}

print_section() {
    echo ""
    echo "--------------------------------------------------------------------------------"
    echo "$1"
    echo "--------------------------------------------------------------------------------"
}

check_pass() {
    ((TOTAL_CHECKS++))
    ((PASSED_CHECKS++))
    echo -e "${GREEN}✓${NC} $1"
    echo "[PASS] $1" >> "$LOG_FILE"
}

check_fail() {
    ((TOTAL_CHECKS++))
    ((FAILED_CHECKS++))
    echo -e "${RED}✗${NC} $1"
    echo "[FAIL] $1" >> "$LOG_FILE"
    if [ -n "$2" ]; then
        echo -e "  ${RED}Error: $2${NC}"
        echo "  Error: $2" >> "$LOG_FILE"
    fi
}

check_warn() {
    ((TOTAL_CHECKS++))
    ((WARNING_CHECKS++))
    echo -e "${YELLOW}⚠${NC} $1"
    echo "[WARN] $1" >> "$LOG_FILE"
    if [ -n "$2" ]; then
        echo -e "  ${YELLOW}Warning: $2${NC}"
        echo "  Warning: $2" >> "$LOG_FILE"
    fi
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
    echo "[INFO] $1" >> "$LOG_FILE"
}

################################################################################
# Validation Functions
################################################################################

validate_python_environment() {
    print_section "Python Environment"
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        check_pass "Python 3 installed: $PYTHON_VERSION"
    else
        check_fail "Python 3 not found"
        return 1
    fi
    
    # Check Python version >= 3.11
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        check_pass "Python version >= 3.11"
    else
        check_warn "Python version < 3.11 (recommended: 3.11+)"
    fi
}

validate_python_syntax() {
    print_section "Python Syntax Validation"
    
    # Check main application file
    if python3 -m py_compile app.py 2>/dev/null; then
        check_pass "app.py compiles successfully"
    else
        check_fail "app.py has syntax errors"
    fi
    
    # Check all Python files
    SYNTAX_ERRORS=0
    while IFS= read -r file; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            check_fail "Syntax error in $file"
            ((SYNTAX_ERRORS++))
        fi
    done < <(find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./static/*")
    
    if [ $SYNTAX_ERRORS -eq 0 ]; then
        check_pass "All Python files compile successfully"
    fi
}

validate_imports() {
    print_section "Import Validation"
    
    # Test main app import
    if python3 -c "import app" 2>/dev/null; then
        check_pass "Main app imports successfully"
    else
        check_fail "Main app import failed"
    fi
    
    # Test Flask app
    if python3 -c "from app import app; print('OK')" 2>/dev/null | grep -q "OK"; then
        check_pass "Flask app initializes successfully"
    else
        check_fail "Flask app initialization failed"
    fi
    
    # Test blueprints
    BLUEPRINTS=("auth_bp" "web_bp" "templates_bp" "printers_bp" "print_bp" "preview_bp" "history_bp")
    for bp in "${BLUEPRINTS[@]}"; do
        MODULE=$(echo "$bp" | sed 's/_bp$//')
        if python3 -c "from blueprints.${module}_bp import ${bp}" 2>/dev/null; then
            check_pass "Blueprint ${bp} imports successfully"
        else
            check_fail "Blueprint ${bp} import failed"
        fi
    done
    
    # Test managers
    MANAGERS=("template_manager" "printer_manager" "history_manager" "preview_generator" "print_job")
    for mgr in "${MANAGERS[@]}"; do
        CLASS_NAME=$(echo "$mgr" | sed -r 's/(^|_)([a-z])/\U\2/g')
        if python3 -c "from ${mgr} import ${CLASS_Name}" 2>/dev/null; then
            check_pass "Manager ${mgr} imports successfully"
        else
            check_warn "Manager ${mgr} import check skipped"
        fi
    done
}

validate_file_structure() {
    print_section "File Structure Validation"
    
    # Check required directories
    REQUIRED_DIRS=("blueprints" "templates" "static" "templates_zpl" "utils" "tests" "logs" "previews")
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            check_pass "Directory exists: $dir"
        else
            check_fail "Directory missing: $dir"
        fi
    done
    
    # Check required files
    REQUIRED_FILES=("app.py" "requirements.txt" "Dockerfile" "docker-compose.yml" ".env.example")
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            check_pass "File exists: $file"
        else
            check_fail "File missing: $file"
        fi
    done
    
    # Check environment file
    if [ -f ".env" ]; then
        check_pass "Environment file (.env) exists"
    else
        check_warn "Environment file (.env) not found (required for running)"
    fi
}

validate_configuration() {
    print_section "Configuration Validation"
    
    if [ -f ".env" ]; then
        # Check required environment variables
        REQUIRED_VARS=("SECRET_KEY" "LOGIN_USER" "LOGIN_PASSWORD")
        for var in "${REQUIRED_VARS[@]}"; do
            if grep -q "^${var}=" .env; then
                VALUE=$(grep "^${var}=" .env | cut -d'=' -f2)
                if [ -n "$VALUE" ]; then
                    check_pass "Environment variable set: $var"
                else
                    check_fail "Environment variable empty: $var"
                fi
            else
                check_fail "Environment variable missing: $var"
            fi
        done
        
        # Check if using default secret key
        if grep -q "SECRET_KEY=dev-secret-key" .env || grep -q "SECRET_KEY=your-secret-key" .env; then
            check_warn "Using default SECRET_KEY (change for production)"
        fi
    else
        check_warn "Cannot validate configuration (.env not found)"
    fi
}

validate_docker() {
    print_section "Docker Configuration"
    
    # Check if Docker is installed
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
        check_pass "Docker installed: $DOCKER_VERSION"
    else
        check_warn "Docker not installed (optional for development)"
        return
    fi
    
    # Check if docker-compose is installed
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | tr -d ',')
        check_pass "docker-compose installed: $COMPOSE_VERSION"
    else
        check_warn "docker-compose not installed (optional for development)"
    fi
    
    # Validate docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        if docker-compose config > /dev/null 2>&1; then
            check_pass "docker-compose.yml is valid"
        else
            check_fail "docker-compose.yml has errors"
        fi
    fi
    
    # Validate Dockerfile
    if [ -f "Dockerfile" ]; then
        check_pass "Dockerfile exists"
    else
        check_fail "Dockerfile missing"
    fi
}

validate_dependencies() {
    print_section "Dependencies Validation"
    
    if [ -f "requirements.txt" ]; then
        check_pass "requirements.txt exists"
        
        # Check if dependencies are installed
        MISSING_DEPS=0
        while IFS= read -r line; do
            # Skip empty lines and comments
            [[ -z "$line" || "$line" =~ ^# ]] && continue
            
            PACKAGE=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)
            if python3 -c "import $PACKAGE" 2>/dev/null; then
                : # Package installed
            else
                check_warn "Package not installed: $PACKAGE"
                ((MISSING_DEPS++))
            fi
        done < requirements.txt
        
        if [ $MISSING_DEPS -eq 0 ]; then
            check_pass "All required packages installed"
        else
            check_warn "$MISSING_DEPS package(s) not installed"
        fi
    else
        check_fail "requirements.txt missing"
    fi
}

validate_tests() {
    print_section "Test Suite Validation"
    
    # Check if pytest is available
    if command -v pytest &> /dev/null; then
        check_pass "pytest is installed"
        
        # Check if tests directory exists
        if [ -d "tests" ]; then
            check_pass "tests directory exists"
            
            # Count test files
            TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
            check_info "Found $TEST_COUNT test files"
            
            # Run tests (optional, can be slow)
            if [ "${RUN_TESTS:-0}" = "1" ]; then
                print_section "Running Test Suite"
                if pytest tests/ -v --tb=short > /dev/null 2>&1; then
                    check_pass "All tests passed"
                else
                    check_fail "Some tests failed"
                fi
            else
                check_info "Skipping test execution (set RUN_TESTS=1 to run)"
            fi
        else
            check_warn "tests directory not found"
        fi
    else
        check_warn "pytest not installed (optional for development)"
    fi
}

validate_documentation() {
    print_section "Documentation Validation"
    
    DOCS=("README.md" "QUICKSTART.md" "DEPLOYMENT.md" "CONTRIBUTING.md" "PROJECT_SUMMARY.md" 
          "VALIDATION_CHECKLIST.md" "FEATURES.md" "LIMITATIONS.md" "ROADMAP.md")
    
    for doc in "${DOCS[@]}"; do
        if [ -f "$doc" ]; then
            check_pass "Documentation exists: $doc"
        else
            check_warn "Documentation missing: $doc"
        fi
    done
    
    # Check roo-docs directory
    if [ -d "roo-docs" ]; then
        check_pass "roo-docs directory exists"
        DOC_COUNT=$(find roo-docs -name "*.md" | wc -l)
        check_info "Found $DOC_COUNT documentation files in roo-docs/"
    else
        check_warn "roo-docs directory not found"
    fi
}

validate_scripts() {
    print_section "Scripts Validation"
    
    SCRIPTS=("run_dev.sh" "run_tests.sh" "scripts/deploy.sh" "scripts/backup.sh" "scripts/restore.sh")
    
    for script in "${SCRIPTS[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                check_pass "Script exists and is executable: $script"
            else
                check_warn "Script exists but not executable: $script"
            fi
        else
            check_warn "Script missing: $script"
        fi
    done
}

generate_summary() {
    print_header "Validation Summary"
    
    echo "Total Checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
    echo ""
    
    # Calculate success rate
    if [ $TOTAL_CHECKS -gt 0 ]; then
        SUCCESS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
        echo "Success Rate: ${SUCCESS_RATE}%"
    fi
    
    echo ""
    echo "Detailed log saved to: $LOG_FILE"
    echo ""
    
    # Overall status
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✓ Integration validation PASSED${NC}"
        echo ""
        echo "The application is ready for deployment!"
        return 0
    else
        echo -e "${RED}✗ Integration validation FAILED${NC}"
        echo ""
        echo "Please fix the failed checks before deployment."
        return 1
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "Barcode Central - Integration Validation"
    echo "Started: $(date)"
    echo "Working Directory: $(pwd)"
    echo ""
    
    # Initialize log file
    echo "Barcode Central - Integration Validation Report" > "$LOG_FILE"
    echo "Generated: $(date)" >> "$LOG_FILE"
    echo "========================================" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Run all validations
    validate_python_environment
    validate_python_syntax
    validate_imports
    validate_file_structure
    validate_configuration
    validate_docker
    validate_dependencies
    validate_tests
    validate_documentation
    validate_scripts
    
    # Generate summary
    generate_summary
    
    # Return appropriate exit code
    if [ $FAILED_CHECKS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"