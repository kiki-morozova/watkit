import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
import winreg

def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"⛌ command failed: {cmd}")
        print(f"Error: {e}")
        if check:
            sys.exit(1)
        return e

def check_prerequisites():
    """Check if required tools are installed"""
    print("checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("⛌ python 3.7+ is required")
        sys.exit(1)
    print(f"✓ python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check git
    if not shutil.which("git"):
        print("⛌ git is required but not installed")
        print("please install git first: https://git-scm.com/download/win")
        sys.exit(1)
    print("✓ git found")
    
    # Check pip
    if not shutil.which("pip") and not shutil.which("pip3"):
        print("⛌ pip is required but not installed")
        print("please install pip first")
        sys.exit(1)
    print("✓ pip found")

def get_install_directory():
    """Get the installation directory"""
    home = Path.home()
    install_dir = home / "watkit"
    return install_dir

def clone_repository(install_dir):
    """Clone the watkit repository"""
    print(f"cloning watkit repository to {install_dir}...")
    
    if install_dir.exists():
        print(f"ⓘ directory {install_dir} already exists")
        response = input("do you want to remove it and reinstall? (y/N): ")
        if response.lower() in ['y', 'yes']:
            shutil.rmtree(install_dir)
        else:
            print("installation cancelled")
            sys.exit(0)
    
    run_command(f"git clone https://github.com/kiki-morozova/watkit.git {install_dir}")
    print("✓ repository cloned successfully")

def install_python_dependencies(install_dir, cli_only=True):
    """Install Python dependencies"""
    print("installing python dependencies...")
    
    if cli_only:
        print("  installing CLI-only dependencies...")
        dependencies = [
            "colorama",      # For colored terminal output
            "requests",      # For HTTP requests
            "httpx",         # For async HTTP requests
        ]
    else:
        print("  installing all dependencies (including server)...")
        dependencies = [
            "colorama",      # For colored terminal output
            "requests",      # For HTTP requests
            "httpx",         # For async HTTP requests
            "fastapi",       # For the web server
            "boto3",         # For AWS S3 integration
            "python-dotenv", # For environment variables
            "python-jose[cryptography]", # For JWT handling
            "uvicorn[standard]", # For running FastAPI server
        ]
    
    # Install each dependency
    for dep in dependencies:
        print(f"  installing {dep}...")
        run_command(f"pip install {dep}")
    
    print("✓ python dependencies installed")

def cleanup_unnecessary_directories(install_dir):
    """Remove server and test_packages directories if CLI-only installation"""
    print("cleaning up unnecessary directories...")
    
    server_dir = install_dir / "server"
    test_packages_dir = install_dir / "test_packages"
    
    if server_dir.exists():
        shutil.rmtree(server_dir)
        print("  removed server/ directory")
    
    if test_packages_dir.exists():
        shutil.rmtree(test_packages_dir)
        print("  removed test_packages/ directory")
    
    print("✓ cleanup complete")

def create_watkit_script(install_dir):
    """Create a watkit executable script for Windows"""
    print("creating watkit executable...")
    
    # Create the watkit batch file
    watkit_bat = install_dir / "watkit.bat"
    with open(watkit_bat, 'w') as f:
        f.write(f"""@echo off
REM watkit package manager for Windows
setlocal

REM Add the cli directory to Python path
set CLI_DIR=%~dp0cli
set PYTHONPATH=%CLI_DIR%;%PYTHONPATH%

REM Change to the cli directory
cd /d "%CLI_DIR%"

REM Run watkit
python watkit.py %*
""")
    
    # Create the watkit Python script
    watkit_script = install_dir / "watkit.py"
    with open(watkit_script, 'w') as f:
        f.write(f"""#!/usr/bin/env python3
import sys
import os

# Add the cli directory to Python path
cli_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli')
sys.path.insert(0, cli_dir)

# Change to the cli directory
os.chdir(cli_dir)

# Import and run the main function
from watkit import main

if __name__ == "__main__":
    main()
""")
    
    print("✓ watkit executable created")

def add_to_path_windows(install_dir):
    """Add watkit to Windows PATH using registry"""
    print("setting up PATH...")
    
    try:
        # Get the current user's PATH from registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
        
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""
        
        # Check if already in PATH
        if str(install_dir) not in current_path:
            # Add to PATH
            new_path = current_path + ";" + str(install_dir) if current_path else str(install_dir)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            print(f"✓ added watkit to Windows PATH")
        else:
            print(f"✓ watkit already in Windows PATH")
        
        winreg.CloseKey(key)
        
        # Also add to current session
        os.environ['PATH'] = f"{install_dir};{os.environ.get('PATH', '')}"
        print("✓ added watkit to current session PATH")
        
    except Exception as e:
        print(f"ⓘ could not modify registry automatically: {e}")
        print("please add the following directory to your PATH manually:")
        print(f"  {install_dir}")
        print("\ninstructions:")
        print("1. press Win+R, type 'sysdm.cpl', press Enter")
        print("2. click 'Environment Variables'")
        print("3. under 'User variables', find 'Path' and click 'Edit'")
        print("4. click 'New' and add the directory above")
        print("5. click 'OK' on all dialogs")

def verify_installation():
    """Verify the installation"""
    print("verifying installation...")
    
    # Try to run watkit
    result = run_command("watkit --help", check=False, capture_output=True)
    
    if result.returncode == 0:
        print("✓ watkit installed successfully!")
        print("\ninstallation complete!")
        print("\nto start using watkit:")
        print("1. restart your command prompt or PowerShell")
        print("2. try: watkit --help")
        print("3. initialize a new project: watkit init")
        print("4. check out the README for more commands: https://github.com/kiki-morozova/watkit")
    else:
        print("⛌ installation verification failed")
        print("please check the installation and try again")
        print("\nif the command is not found, try:")
        print("1. restart your command prompt or PowerShell")
        print("2. or run: watkit.bat --help")
        sys.exit(1)

def main():
    """Main installation function"""
    print("watkit windows installer")
    print("=" * 40)
    
    # Check if running on Windows
    if platform.system() != 'Windows':
        print("⛌ this installer is designed for windows systems")
        sys.exit(1)
    
    # Check prerequisites
    check_prerequisites()
    
    # Get installation directory
    install_dir = get_install_directory()
    print(f"installation directory: {install_dir}")
    
    # Ask user about CLI-only installation
    print("\ninstallation options:")
    print("1. CLI-only (recommended) - installs only the command-line tools")
    print("2. Full installation - includes server and web dependencies")
    
    cli_only = True  # Default to CLI-only
    response = input("\ninstall CLI-only? (Y/n): ").strip().lower()
    if response in ['n', 'no']:
        cli_only = False
        print("installing full version with server dependencies...")
    else:
        print("installing CLI-only version...")
    
    # Clone repository
    clone_repository(install_dir)
    
    # Install Python dependencies
    install_python_dependencies(install_dir, cli_only=cli_only)
    
    # Clean up unnecessary directories if CLI-only
    if cli_only:
        cleanup_unnecessary_directories(install_dir)
    
    # Create watkit executable
    create_watkit_script(install_dir)
    
    # Setup PATH
    add_to_path_windows(install_dir)
    
    # Verify installation
    verify_installation()

if __name__ == "__main__":
    main() 