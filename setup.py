#!/usr/bin/env python3
"""
Setup script for Food Trend Predictor
Helps initialize the project and verify dependencies
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if key dependencies are installed"""
    required = [
        'praw', 'supabase', 'transformers', 'xgboost', 
        'sklearn', 'streamlit', 'plotly', 'pandas', 'torch'
    ]
    
    missing = []
    for package in required:
        try:
            if package == 'sklearn':
                __import__('sklearn')
            else:
                __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} missing")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        print("   Then edit .env with your credentials")
        return False
    
    print("✅ .env file exists")
    
    # Check for required variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'REDDIT_USER_AGENT',
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var).startswith('your_'):
            missing.append(var)
    
    if missing:
        print(f"⚠️  Missing or default values for: {', '.join(missing)}")
        print("   Edit .env file with your actual credentials")
        return False
    
    print("✅ All environment variables configured")
    return True

def create_directories():
    """Create necessary directories"""
    dirs = ['models', 'data', 'logs']
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created directory: {dir_name}/")
    
    return True

def test_reddit_connection():
    """Test Reddit API connection"""
    try:
        import praw
        from dotenv import load_dotenv
        load_dotenv()
        
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
        )
        
        # Test by fetching one post
        subreddit = reddit.subreddit("food")
        next(subreddit.hot(limit=1))
        
        print("✅ Reddit API connection successful")
        return True
    except Exception as e:
        print(f"❌ Reddit API connection failed: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv()
        
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # Test connection
        supabase.table('reddit_posts').select('*').limit(1).execute()
        
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        print("   Make sure you've created the tables using database_schema.sql")
        return False

def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "="*70)
    print("🎉 Setup Complete!")
    print("="*70)
    print("\n📝 Next Steps:\n")
    print("1. Set up Supabase database:")
    print("   - Go to your Supabase project")
    print("   - Open SQL Editor")
    print("   - Run the SQL from database_schema.sql")
    print()
    print("2. Collect Reddit data:")
    print("   python etl.py collect 1000  # Start with 1000 posts")
    print()
    print("3. Train the model:")
    print("   python model.py")
    print()
    print("4. Generate predictions:")
    print("   python predict_service.py report")
    print()
    print("5. Launch dashboard:")
    print("   streamlit run dashboard.py")
    print()
    print("="*70)
    print("📚 Documentation: README.md")
    print("❓ Need help? Check config.py for settings")
    print("="*70)

def main():
    """Run setup checks"""
    print("="*70)
    print("🍕 Food Trend Predictor - Setup")
    print("="*70)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Directories", create_directories),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        result = check_func()
        results.append(result)
        print()
    
    # Optional connection tests
    if results[2]:  # If env file is configured
        print("📋 Testing Connections...")
        print()
        test_reddit_connection()
        print()
        test_supabase_connection()
        print()
    
    if all(results):
        display_next_steps()
    else:
        print("\n⚠️  Setup incomplete. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
