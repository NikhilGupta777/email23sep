#!/usr/bin/env python3
"""
Ultra-Fast Email Validation Performance Test
"""

import requests
import time
import json

def test_validation_performance():
    """Test the ultra-fast email validation system"""

    # Test emails - mix of valid and invalid
    test_emails = [
        # Valid emails
        "test@gmail.com",
        "user@outlook.com",
        "contact@yahoo.com",
        "info@protonmail.com",
        "admin@kalkiavatar.org",

        # Invalid emails
        "invalid@nonexistentdomain12345.com",
        "test@.com",
        "@domain.com",
        "test..test@gmail.com",
        "test@",

        # More valid emails
        "support@apple.com",
        "hello@microsoft.com",
        "contact@amazon.com",
        "info@facebook.com",
        "help@twitter.com",

        # Edge cases
        "test+tag@gmail.com",
        "user.name@company.co.uk",
        "test@sub.domain.com",
    ]

    print("ULTRA-FAST EMAIL VALIDATION PERFORMANCE TEST")
    print("=" * 60)
    print(f"Testing with {len(test_emails)} emails")
    print()

    # First, get auth token
    print("Getting authentication token...")
    auth_response = requests.post("http://localhost:8000/token", data={
        "username": "admin",
        "password": "admin123"
    })

    if auth_response.status_code != 200:
        print("Failed to authenticate")
        return

    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("Authentication successful")
    print()

    # Test validation
    print("Starting ultra-fast validation...")
    start_time = time.time()

    validation_response = requests.post("http://localhost:8000/email/validate",
                                      json={"emails": test_emails},
                                      headers=headers)

    end_time = time.time()
    total_time = end_time - start_time

    if validation_response.status_code != 200:
        print(f"Validation failed: {validation_response.status_code}")
        print(validation_response.text)
        return

    results = validation_response.json()["results"]

    # Analyze results
    valid_count = sum(1 for r in results if r["valid"])
    deliverable_count = sum(1 for r in results if r.get("deliverable", False))
    invalid_count = len(results) - valid_count

    emails_per_second = len(test_emails) / total_time

    print("RESULTS:")
    print(f"   Total emails processed: {len(test_emails)}")
    print(f"   Valid format: {valid_count} ({valid_count/len(test_emails)*100:.1f}%)")
    print(f"   Deliverable: {deliverable_count} ({deliverable_count/len(test_emails)*100:.1f}%)")
    print(f"   Invalid: {invalid_count} ({invalid_count/len(test_emails)*100:.1f}%)")
    print()
    print("PERFORMANCE:")
    print(f"   Total time: {total_time:.2f} seconds")
    print(f"   Speed: {emails_per_second:.1f} emails/second")
    print(f"   Average per email: {(total_time/len(test_emails))*1000:.1f}ms")
    print()

    if emails_per_second > 10:
        print("ULTRA-FAST PERFORMANCE ACHIEVED! (>10 emails/sec)")
    elif emails_per_second > 5:
        print("Fast performance achieved! (>5 emails/sec)")
    else:
        print("Performance could be improved")

    print()
    print("SAMPLE RESULTS:")
    for i, result in enumerate(results[:5]):  # Show first 5 results
        status = "[VALID]" if result["valid"] else "[INVALID]"
        deliverable = "[DELIVERABLE]" if result.get("deliverable", False) else ""
        print(f"   {status}{deliverable} {result['email']} - {result['reason']}")

    if len(results) > 5:
        print(f"   ... and {len(results)-5} more results")

if __name__ == "__main__":
    test_validation_performance()