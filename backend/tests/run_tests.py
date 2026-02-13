#!/usr/bin/env python3
"""
Test runner script for backend tests
"""
import subprocess
import sys
import os

def run_tests():
    """Run all backend tests"""
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'backend/tests/', 
            '-v',
            '--tb=short'
        ], check=True, capture_output=True, text=True)
        
        print("✅ All tests passed!")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Some tests failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print("⚠️  pytest not found. Installing pytest...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest'], 
                         check=True, capture_output=True)
            print("✅ pytest installed successfully")
            return run_tests()
        except subprocess.CalledProcessError as e:
            print("❌ Failed to install pytest:", e.stderr)
            return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)