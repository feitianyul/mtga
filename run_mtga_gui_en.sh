#!/bin/bash

# Set script encoding to UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
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

# Check if running as root
check_admin() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running with root privileges"
        return 0
    else
        print_info "Running with normal user privileges"
        # For macOS, some operations may require sudo, but root is not mandatory
        return 1
    fi
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
print_info "Script directory: $SCRIPT_DIR"

# Check if uv is installed
check_uv() {
    if command -v uv &> /dev/null; then
        print_success "uv detected and ready"
        return 0
    else
        return 1
    fi
}

# Install uv
install_uv() {
    print_info "uv not installed, starting automatic installation..."
    print_info "Installing uv via curl, please wait..."
    
    # Use official installation script
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        print_success "uv installation successful!"
        
        # Add possible uv installation paths to current session PATH
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
        
        # Source env file if installation script provided it
        if [[ -f "$HOME/.local/bin/env" ]]; then
            source "$HOME/.local/bin/env" 2>/dev/null || true
        fi
        
        # Reload shell configuration
        if [[ -f "$HOME/.zshrc" ]]; then
            source "$HOME/.zshrc" 2>/dev/null || true
        fi
        if [[ -f "$HOME/.bashrc" ]]; then
            source "$HOME/.bashrc" 2>/dev/null || true
        fi
        
        # Check if uv is available again
        if command -v uv &> /dev/null; then
            print_success "uv is now available: $(which uv)"
            return 0
        else
            print_error "uv still not found after installation, please manually add $HOME/.local/bin or $HOME/.cargo/bin to PATH"
            print_error "or restart terminal window"
            return 1
        fi
    else
        print_error "uv installation failed"
        return 1
    fi
}

# Set path variables
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_ACTIVATE="$VENV_DIR/bin/activate"
OPENSSL_DIR="$SCRIPT_DIR/openssl"

# Check and create virtual environment
setup_venv() {
    # Switch to script directory
    cd "$SCRIPT_DIR" || exit 1
    
    if [[ ! -f "$VENV_PYTHON" ]]; then
        print_info "Virtual environment does not exist, creating..."
        
        # Install Python 3.13 using uv
        print_info "Installing Python 3.13..."
        if ! uv python install 3.13; then
            print_error "Python 3.13 installation failed"
            exit 1
        fi
        
        # Create virtual environment
        print_info "Creating virtual environment..."
        if ! uv venv --python 3.13; then
            print_error "Virtual environment creation failed"
            exit 1
        fi
        
        # Sync dependencies
        print_info "Syncing dependencies..."
        if ! uv sync; then
            print_error "Dependency sync failed"
            exit 1
        fi
        
        print_success "Virtual environment and dependencies installation completed!"
    else
        print_success "Virtual environment already exists"
        
        # Check if dependencies need updating
        print_info "Checking dependency status..."
        if ! uv sync --frozen; then
            print_warning "Dependencies may need updating, syncing..."
            if ! uv sync; then
                print_error "Dependency sync failed"
                exit 1
            fi
            print_success "Dependency sync completed!"
        else
            print_success "Dependencies are up to date"
        fi
    fi
}

# Check OpenSSL
check_openssl() {
    # On macOS, prefer system openssl or openssl installed via Homebrew
    if command -v openssl &> /dev/null; then
        print_success "System OpenSSL detected: $(which openssl)"
        return 0
    elif [[ -f "$OPENSSL_DIR/openssl" ]]; then
        print_success "Project OpenSSL detected: $OPENSSL_DIR/openssl"
        export PATH="$OPENSSL_DIR:$PATH"
        return 0
    else
        print_error "OpenSSL not found"
        print_info "Please install OpenSSL: brew install openssl"
        print_info "or ensure openssl file exists in project directory"
        return 1
    fi
}

# Check main program
check_main_program() {
    if [[ ! -f "$SCRIPT_DIR/mtga_gui.py" ]]; then
        print_error "Main program not found: $SCRIPT_DIR/mtga_gui.py"
        print_error "Please ensure program files are complete"
        return 1
    else
        print_success "Main program file exists"
        return 0
    fi
}

# Main function
main() {
    echo "===================================="
    echo "MTGA GUI Launcher (macOS)"
    echo "===================================="
    
    # Pre-set possible uv paths to PATH
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    # Check administrator privileges
    check_admin
    
    # Check and install uv
    if ! check_uv; then
        if ! install_uv; then
            exit 1
        fi
    fi
    
    # Setup virtual environment
    setup_venv
    
    # Check OpenSSL
    if ! check_openssl; then
        exit 1
    fi
    
    # Check main program
    if ! check_main_program; then
        exit 1
    fi
    
    # Set environment variables
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    print_info "Starting program, please wait..."
    
    # Switch to script directory and run program using uv (auto-uses virtual environment)
    cd "$SCRIPT_DIR" || exit 1
    
    # Run the program (requires sudo privileges)
    print_info "The program requires administrator privileges to modify network settings, you will be prompted for password..."
    if sudo uv run python "$SCRIPT_DIR/mtga_gui.py"; then
        print_success "Program exited normally"
    else
        exit_code=$?
        print_error "Program exited abnormally with code: $exit_code"
        echo "Press any key to continue..."
        read -n 1 -s
        exit $exit_code
    fi
}

# Run main function
main "$@"