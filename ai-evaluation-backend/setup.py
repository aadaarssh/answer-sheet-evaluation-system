#!/usr/bin/env python3
"""
Setup and installation script for AI Evaluation System Backend
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print setup banner."""
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║     AI Answer Sheet Evaluation System         ║
    ║              Setup & Installation             ║
    ╚═══════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment file."""
    print("\n🔧 Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ Environment file already exists")
        return True
    
    # Copy from example or create new
    env_content = """# AI Evaluation System Configuration

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_evaluation_system

# JWT Authentication
SECRET_KEY=your-super-secret-key-change-in-production-123456789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI APIs
OPENAI_API_KEY=your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10

# Processing
REAL_TIME_THRESHOLD=5
REDIS_URL=redis://localhost:6379

# Email notifications (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@example.com
EMAIL_PASSWORD=your-email-password

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173
"""
    
    try:
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✓ Environment file created")
        print("⚠️  Please update the API keys and database settings in .env")
        return True
    except Exception as e:
        print(f"❌ Failed to create environment file: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "uploads",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"✓ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def check_services():
    """Check if required services are available."""
    print("\n🔍 Checking required services...")
    
    services_status = {}
    
    # Check MongoDB
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✓ MongoDB - Available")
        services_status['mongodb'] = True
    except Exception:
        print("⚠️  MongoDB - Not available (required for database)")
        services_status['mongodb'] = False
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        r.ping()
        print("✓ Redis - Available")
        services_status['redis'] = True
    except Exception:
        print("⚠️  Redis - Not available (required for async processing)")
        services_status['redis'] = False
    
    return services_status

def print_installation_guide():
    """Print service installation guide."""
    system = platform.system().lower()
    
    print("\n📋 Service Installation Guide:")
    print("━" * 50)
    
    if system == "windows":
        print("Windows Installation:")
        print("1. MongoDB:")
        print("   - Download from: https://www.mongodb.com/try/download/community")
        print("   - Follow installation wizard")
        print("   - Start: net start MongoDB")
        print("")
        print("2. Redis:")
        print("   - Download from: https://github.com/tporadowski/redis/releases")
        print("   - Extract and run redis-server.exe")
        print("")
    
    elif system == "darwin":  # macOS
        print("macOS Installation (using Homebrew):")
        print("1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("2. MongoDB: brew install mongodb-community")
        print("3. Redis: brew install redis")
        print("4. Start services:")
        print("   - brew services start mongodb-community")
        print("   - brew services start redis")
        print("")
    
    else:  # Linux
        print("Linux Installation:")
        print("1. MongoDB:")
        print("   - Ubuntu/Debian: sudo apt-get install mongodb")
        print("   - CentOS/RHEL: sudo yum install mongodb-server")
        print("")
        print("2. Redis:")
        print("   - Ubuntu/Debian: sudo apt-get install redis-server")
        print("   - CentOS/RHEL: sudo yum install redis")
        print("")

def print_next_steps():
    """Print next steps after installation."""
    print("\n🎯 Next Steps:")
    print("━" * 50)
    print("1. Update API keys in .env file:")
    print("   - Get OpenAI API key: https://platform.openai.com/api-keys")
    print("   - Get Gemini API key: https://makersuite.google.com/app/apikey")
    print("")
    print("2. Start the services:")
    print("   - Main server:    python start_server.py")
    print("   - Celery worker:  python start_worker.py")
    print("")
    print("3. Access the application:")
    print("   - API Server:     http://localhost:8000")
    print("   - Documentation:  http://localhost:8000/docs")
    print("   - Health Check:   http://localhost:8000/health")
    print("")
    print("4. Test the installation:")
    print("   - Register a professor account")
    print("   - Create an evaluation scheme")
    print("   - Upload sample answer sheets")
    print("")

def main():
    """Main setup function."""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Setup environment
    if not setup_environment():
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Check services
    services = check_services()
    
    missing_services = [service for service, available in services.items() if not available]
    
    if missing_services:
        print(f"\n⚠️  Missing services: {', '.join(missing_services)}")
        print_installation_guide()
    else:
        print("\n✅ All services are available!")
    
    print_next_steps()
    
    print("\n🎉 Setup completed successfully!")
    print("Please review the configuration and start the services.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup failed: {e}")
        sys.exit(1)