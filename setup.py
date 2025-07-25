#!/usr/bin/env python3
"""
Setup script for the Traffic Management System.
This script helps configure the project structure and dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_dependencies():
    """Check if required system dependencies are available."""
    dependencies = ['pip']
    
    for dep in dependencies:
        if not shutil.which(dep):
            print(f"❌ Required dependency '{dep}' not found")
            return False
        print(f"✅ Found {dep}")
    
    return True

def install_requirements():
    """Install Python requirements."""
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python requirements"
    )

def setup_environment():
    """Setup environment configuration."""
    env_example = Path('.env.example')
    env_file = Path('.env')
    
    if not env_example.exists():
        print("❌ .env.example not found")
        return False
    
    if not env_file.exists():
        print("🔄 Creating .env file from .env.example...")
        shutil.copy(env_example, env_file)
        print("✅ .env file created")
        print("📝 Please edit .env file with your actual credentials:")
        print("   - NEO4J_PASSWORD")
        print("   - ANTHROPIC_API_KEY")
        print("   - LANGCHAIN_API_KEY (optional)")
    else:
        print("✅ .env file already exists")
    
    return True

def validate_configuration():
    """Validate configuration files."""
    try:
        # Add current directory to path for imports
        sys.path.insert(0, os.getcwd())
        
        from config.settings import settings
        
        print("🔄 Validating configuration...")
        
        # Check required settings
        required = [
            ('NEO4J_URI', settings.NEO4J_URI),
            ('NEO4J_USERNAME', settings.NEO4J_USERNAME),
            ('NEO4J_PASSWORD', settings.NEO4J_PASSWORD),
            ('ANTHROPIC_API_KEY', settings.ANTHROPIC_API_KEY)
        ]
        
        missing = []
        for name, value in required:
            if not value or value == "your_password_here" or value == "your_api_key_here":
                missing.append(name)
        
        if missing:
            print("⚠️ Configuration incomplete. Missing/placeholder values for:")
            for name in missing:
                print(f"   - {name}")
            print("\n📝 Please edit .env file with real values")
            return False
        
        print("✅ Configuration validation passed")
        return True
        
    except ImportError as e:
        print(f"⚠️ Could not validate configuration: {e}")
        print("This is normal if dependencies aren't installed yet")
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def test_imports():
    """Test if all modules can be imported."""
    try:
        print("🔄 Testing module imports...")
        
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Test core imports
        from config.settings import settings
        print("✅ Config module imported")
        
        from src.core.state import GraphState
        print("✅ Core modules imported")
        
        from prompts.system_prompts import system_prompt
        print("✅ Prompts imported")
        
        print("✅ All imports successful")
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Import test error: {e}")
        return False

def create_directories():
    """Create any missing directories."""
    directories = [
        'logs',
        'cache',
        'backups',
        'notebooks/exploration',
        'docs/workflow_diagrams'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory created/verified: {directory}")
    
    return True

def main():
    """Main setup function."""
    print("🚀 TRAFFIC MANAGEMENT SYSTEM SETUP")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Checking system dependencies", check_dependencies),
        ("Installing Python requirements", install_requirements),
        ("Setting up environment configuration", setup_environment),
        ("Creating directories", create_directories),
        ("Testing module imports", test_imports),
        ("Validating configuration", validate_configuration),
    ]
    
    failed_steps = []
    
    for description, func in steps:
        print(f"\n📋 {description}...")
        if not func():
            failed_steps.append(description)
    
    print("\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)
    
    if not failed_steps:
        print("🎉 Setup completed successfully!")
        print("\n🚀 Next steps:")
        print("  1. Edit .env file with your credentials")
        print("  2. Start your Neo4j database")
        print("  3. Run: python scripts/setup_database.py")
        print("  4. Test with: python main.py")
        print("  5. Or run demo: python scripts/demo.py")
        return 0
    else:
        print(f"❌ Setup completed with {len(failed_steps)} issues:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\n💡 Please resolve the above issues and run setup again")
        return 1

if __name__ == "__main__":
    sys.exit(main())
