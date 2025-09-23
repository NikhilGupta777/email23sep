#!/usr/bin/env python3
import requests
import time

def test_server():
    """Test if the server is running and accessible"""
    try:
        print("Testing server accessibility...")
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("SUCCESS: Server is running and accessible")
            print(f"Response content length: {len(response.text)} characters")
            return True
        else:
            print(f"ERROR: Server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server. Make sure to run: python main.py")
        return False
    except Exception as e:
        print(f"ERROR: Error testing server: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\nTesting API endpoints...")

    # Test login
    try:
        response = requests.post("http://localhost:8000/token",
                               data={"username": "admin", "password": "admin123"})
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("SUCCESS: Login API working")
            return token
        else:
            print(f"ERROR: Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"ERROR: Login API error: {e}")
        return None

def test_protected_endpoints(token):
    """Test protected API endpoints"""
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Test templates endpoint
    try:
        response = requests.get("http://localhost:8000/templates", headers=headers)
        if response.status_code == 200:
            print("SUCCESS: Templates API working")
        else:
            print(f"ERROR: Templates API failed: {response.status_code}")
    except Exception as e:
        print(f"ERROR: Templates API error: {e}")

    # Test email validation
    try:
        response = requests.post("http://localhost:8000/email/validate",
                               json={"emails": ["test@example.com"]},
                               headers=headers)
        if response.status_code == 200:
            print("SUCCESS: Email validation API working")
        else:
            print(f"ERROR: Email validation API failed: {response.status_code}")
    except Exception as e:
        print(f"ERROR: Email validation API error: {e}")

if __name__ == "__main__":
    print("Testing Email Backup Application")
    print("=" * 50)

    if test_server():
        token = test_api_endpoints()
        test_protected_endpoints(token)

    print("\n" + "=" * 50)
    print("INSTRUCTIONS FOR FRONTEND TESTING:")
    print("1. Make sure the server is running: python main.py")
    print("2. Open your browser and go to: http://localhost:8000")
    print("3. Open browser Developer Tools (F12)")
    print("4. Check the Console tab for any JavaScript errors")
    print("5. Try logging in with: admin / admin123")
    print("6. Check Network tab to see if API calls are being made")
    print("=" * 50)