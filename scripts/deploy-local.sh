#!/bin/bash

# SPIDER Local Deployment Script
# This script sets up SPIDER for local development and testing

set -e

echo "🕷️  SPIDER Local Deployment"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.9+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.9"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.9+ is required. Found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    # Install development dependencies
    pip install -r requirements-dev.txt 2>/dev/null || print_warning "Development requirements not found"
    
    print_success "Dependencies installed"
}

# Install Playwright browsers
install_playwright() {
    print_status "Installing Playwright browsers..."
    
    if command -v playwright &> /dev/null; then
        playwright install
        print_success "Playwright browsers installed"
    else
        print_warning "Playwright not found, skipping browser installation"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p logs
    mkdir -p cache
    mkdir -p config
    mkdir -p tests
    
    print_success "Directories created"
}

# Setup configuration
setup_config() {
    print_status "Setting up configuration..."
    
    if [ ! -f "config/spider.yaml" ]; then
        print_warning "Configuration file not found, creating default..."
        # The config file should already exist from our setup
    fi
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            print_warning "Created .env file from example. Please update with your actual values."
        else
            print_warning "No .env.example found, creating basic .env file..."
            cat > .env << EOF
# SPIDER Environment Variables
DATABASE_URL=sqlite:///data/spider.db
REDIS_URL=redis://localhost:6379
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF
        fi
    fi
    
    print_success "Configuration setup complete"
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Create database directory
    mkdir -p data
    
    # Run database migrations if they exist
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        print_success "Database migrations applied"
    else
        print_warning "No database migrations found"
    fi
    
    print_success "Database initialized"
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --cov=spider --cov-report=html --cov-report=term
        print_success "Tests completed"
    else
        print_warning "pytest not found, skipping tests"
    fi
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_status "Setting up pre-commit hooks..."
    
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "pre-commit not found, skipping hook setup"
    fi
}

# Create systemd service (optional)
create_systemd_service() {
    print_status "Creating systemd service (optional)..."
    
    if [ "$1" = "--systemd" ]; then
        sudo tee /etc/systemd/system/spider.service > /dev/null << EOF
[Unit]
Description=SPIDER Web Scraping Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python -m spider.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        print_success "Systemd service created. Use 'sudo systemctl start spider' to start the service."
    else
        print_warning "Skipping systemd service creation. Use --systemd flag to enable."
    fi
}

# Main deployment function
main() {
    echo "Starting SPIDER local deployment..."
    echo
    
    check_python
    setup_venv
    install_dependencies
    install_playwright
    create_directories
    setup_config
    init_database
    run_tests
    setup_pre_commit
    create_systemd_service "$@"
    
    echo
    print_success "SPIDER local deployment completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Update .env file with your API keys and configuration"
    echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
    echo "3. Run 'python -m spider.main --help' to see available commands"
    echo "4. Run 'python -m spider.main --urls https://httpbin.org/html' to test scraping"
    echo
    echo "For development:"
    echo "- Run 'pytest' to run tests"
    echo "- Run 'black .' to format code"
    echo "- Run 'flake8 .' to check code style"
    echo "- Run 'mypy .' to check type hints"
    echo
}

# Run main function with all arguments
main "$@"
