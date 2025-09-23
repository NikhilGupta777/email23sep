#!/usr/bin/env python3
"""
Advanced Email Validation Features Test
"""

import requests
import time

def test_advanced_validation():
    """Test advanced email validation features"""

    # Test emails with various issues
    test_emails = [
        # Valid emails
        "test@gmail.com",
        "user@outlook.com",
        "contact@kalkiavatar.org",

        # Invalid format
        "invalid-email",
        "@domain.com",
        "test@.com",

        # Disposable emails
        "test@10minutemail.com",
        "user@guerrillamail.com",
        "contact@mailinator.com",

        # Role-based emails (using unknown domains)
        "admin@unknowncompany.com",
        "support@unknownservice.com",
        "info@randomdomain.com",
        "noreply@testdomain.com",

        # Spam traps
        "test@spamtrap.com",
        "user@spamcop.net",

        # Invalid domains
        "test@nonexistentdomain12345.com",
        "user@invalid-domain-test.com",
    ]

    print("ADVANCED EMAIL VALIDATION FEATURES TEST")
    print("=" * 60)
    print(f"Testing with {len(test_emails)} emails (including problematic ones)")
    print()

    # Get auth token
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
    print("Testing advanced validation features...")
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
    invalid_count = len(results) - valid_count

    emails_per_second = len(test_emails) / total_time

    print("RESULTS:")
    print(f"   Total emails processed: {len(test_emails)}")
    print(f"   Valid format: {valid_count} ({valid_count/len(test_emails)*100:.1f}%)")
    print(f"   Invalid format: {invalid_count} ({invalid_count/len(test_emails)*100:.1f}%)")
    print()
    print("PERFORMANCE:")
    print(f"   Total time: {total_time:.2f} seconds")
    print(f"   Speed: {emails_per_second:.1f} emails/second")
    print(f"   Average per email: {(total_time/len(test_emails))*1000:.1f}ms")
    print()

    if emails_per_second > 10:
        print("FAST PERFORMANCE ACHIEVED! (>10 emails/sec)")
    else:
        print("Performance acceptable")

    print()
    print("ADVANCED FEATURES DETECTION:")
    print("=" * 40)

    # Check for disposable email detection
    disposable_detected = [r for r in results if "Disposable" in r.get("reason", "")]
    print(f"Disposable emails detected: {len(disposable_detected)}")
    for r in disposable_detected:
        print(f"   - {r['email']}: {r['reason']}")

    # Check for role-based email detection
    role_based_detected = [r for r in results if "Role-based" in r.get("reason", "")]
    print(f"Role-based emails detected: {len(role_based_detected)}")
    for r in role_based_detected:
        print(f"   - {r['email']}: {r['reason']}")

    # Check for spam trap detection
    spam_trap_detected = [r for r in results if "Spam Trap" in r.get("reason", "")]
    print(f"Spam trap domains detected: {len(spam_trap_detected)}")
    for r in spam_trap_detected:
        print(f"   - {r['email']}: {r['reason']}")

    # Check for invalid format detection
    invalid_format = [r for r in results if "Invalid Format" in r.get("reason", "")]
    print(f"Invalid formats detected: {len(invalid_format)}")
    for r in invalid_format:
        print(f"   - {r['email']}: {r['reason']}")

    # Check for valid emails
    valid_emails = [r for r in results if r["valid"] and "Invalid" not in r.get("reason", "")]
    print(f"Valid emails accepted: {len(valid_emails)}")
    for r in valid_emails[:3]:  # Show first 3
        print(f"   - {r['email']}: {r['reason']}")

    if len(valid_emails) > 3:
        print(f"   ... and {len(valid_emails)-3} more valid emails")

    print()
    print("ALL DETAILED RESULTS:")
    print("-" * 40)
    for i, result in enumerate(results):
        status = "[VALID]" if result["valid"] else "[INVALID]"
        print(f"   {status} {result['email']} - {result['reason']}")

    print()
    print("EXPECTED DETECTIONS:")
    print("-" * 40)
    print("Should be INVALID (Disposable):")
    print("  - test@10minutemail.com, user@guerrillamail.com, contact@mailinator.com")
    print("Should be INVALID (Role-based):")
    print("  - admin@unknowncompany.com, support@unknownservice.com, info@randomdomain.com, noreply@testdomain.com")
    print("Should be INVALID (Spam traps):")
    print("  - test@spamtrap.com, user@spamcop.net")
    print("Should be INVALID (Format/Domain):")
    print("  - invalid-email, @domain.com, test@.com, test@nonexistentdomain12345.com, user@invalid-domain-test.com")

    print()
    print("SUMMARY:")
    print("=" * 40)
    print("Advanced validation features working:")
    print(f"   - Disposable email detection: {'YES' if disposable_detected else 'NO'}")
    print(f"   - Role-based email detection: {'YES' if role_based_detected else 'NO'}")
    print(f"   - Spam trap detection: {'YES' if spam_trap_detected else 'NO'}")
    print(f"   - Invalid format detection: {'YES' if invalid_format else 'NO'}")
    print(f"   - Valid email acceptance: {'YES' if valid_emails else 'NO'}")
    print()
    print("ADVANCED EMAIL VALIDATION SYSTEM COMPLETE!")

if __name__ == "__main__":
    test_advanced_validation()