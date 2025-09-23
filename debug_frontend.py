#!/usr/bin/env python3
"""
Frontend Debugging Script for Email Backup Application

This script helps you debug frontend issues by providing clear instructions
and checking if the server is running properly.
"""

import requests
import time
import webbrowser

def check_server():
    """Check if the server is running and accessible"""
    print("Checking server status...")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("SUCCESS: Server is running and accessible")
            return True
        else:
            print(f"ERROR: Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Server is not running!")
        print("   Please start the server with: python main.py")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    print("\nTesting API endpoints...")

    # Test login
    try:
        response = requests.post("http://localhost:8000/token",
                               data={"username": "admin", "password": "admin123"})
        if response.status_code == 200:
            print("SUCCESS: Login API working")
            return "token_received"
        else:
            print(f"ERROR: Login API failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"ERROR: Login API error: {e}")
        return None

def print_debugging_instructions():
    """Print comprehensive debugging instructions"""
    print("\n" + "="*60)
    print("FRONTEND DEBUGGING INSTRUCTIONS")
    print("="*60)

    print("\n1. SERVER STATUS:")
    print("   SUCCESS: Make sure server is running: python main.py")
    print("   SUCCESS: Check server at: http://localhost:8000")

    print("\n2. BROWSER ACCESS:")
    print("   SUCCESS: Open: http://localhost:8000 (NOT file://)")
    print("   ERROR: Don't double-click index.html file")

    print("\n3. BROWSER DEBUGGING:")
    print("   SUCCESS: Press F12 to open Developer Tools")
    print("   SUCCESS: Check Console tab for JavaScript errors")
    print("   SUCCESS: Check Network tab for failed API calls")

    print("\n4. EXPECTED CONSOLE LOGS:")
    print("   - 'Frontend initialized'")
    print("   - 'Backend URL: http://localhost:8000'")
    print("   - 'Element found: dashboard-section'")
    print("   - 'Element found: templates-section'")
    print("   - 'Element found: validation-section'")

    print("\n5. TESTING NAVIGATION:")
    print("   SUCCESS: Login with: admin / admin123")
    print("   SUCCESS: Click 'Templates' in sidebar")
    print("   SUCCESS: Check console for: 'Navigation link clicked: nav-templates'")
    print("   SUCCESS: Check console for: 'Navigating to page: templates'")
    print("   SUCCESS: Check console for: 'Showing section: templates-section'")
    print("   SUCCESS: Check console for: 'Loading templates...'")

    print("\n6. COMMON ISSUES:")
    print("   ERROR: File opened directly (use http:// instead)")
    print("   ERROR: Server not running")
    print("   ERROR: CORS errors in console")
    print("   ERROR: JavaScript errors preventing navigation")

    print("\n7. IF STILL NOT WORKING:")
    print("   - Clear browser cache and reload")
    print("   - Try incognito/private browsing")
    print("   - Check firewall/antivirus blocking requests")

    print("\n" + "="*60)

def main():
    print("Email Backup Application - Frontend Debugger")
    print("="*60)

    if not check_server():
        print_debugging_instructions()
        return

    token = test_api_endpoints()

    if token:
        print("SUCCESS: All API endpoints working correctly")
        print("TARGET: The issue is likely with frontend access or browser setup")
    else:
        print("ERROR: API endpoints not working - check server logs")

    print_debugging_instructions()

    # Offer to open browser
    try:
        response = input("\nWould you like to open the application in your browser? (y/n): ")
        if response.lower() == 'y':
            webbrowser.open("http://localhost:8000")
            print("Browser opened to: http://localhost:8000")
    except:
        pass

if __name__ == "__main__":
    main()