#!/usr/bin/env python3
"""
Large Batch Email Validation Performance Test
"""

import requests
import time
import random

def generate_test_emails(count=100):
    """Generate a large batch of test emails"""
    domains = [
        'gmail.com', 'outlook.com', 'yahoo.com', 'protonmail.com',
        'kalkiavatar.org', 'apple.com', 'microsoft.com', 'amazon.com',
        'company.com', 'business.com', 'enterprise.com', 'test.com'
    ]

    invalid_domains = [
        'nonexistentdomain12345.com', 'invalid-domain-test.com', 'fake12345.com'
    ]

    emails = []

    # Generate valid emails
    for i in range(count - 10):  # Leave 10 for invalid
        username = f"user{random.randint(1, 99999)}"
        domain = random.choice(domains)
        emails.append(f"{username}@{domain}")

    # Add some invalid emails
    for i in range(10):
        username = f"test{i}"
        domain = random.choice(invalid_domains)
        emails.append(f"{username}@{domain}")

    # Shuffle the list
    random.shuffle(emails)
    return emails

def test_large_batch_validation():
    """Test validation with a large batch of emails"""

    # Generate test emails
    test_emails = generate_test_emails(100)

    print("LARGE BATCH EMAIL VALIDATION PERFORMANCE TEST")
    print("=" * 60)
    print(f"Testing with {len(test_emails)} emails")
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
    print("Starting large batch validation...")
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

    if emails_per_second > 50:
        print("INSANE PERFORMANCE ACHIEVED! (>50 emails/sec)")
    elif emails_per_second > 25:
        print("ULTRA-FAST PERFORMANCE ACHIEVED! (>25 emails/sec)")
    elif emails_per_second > 10:
        print("FAST PERFORMANCE ACHIEVED! (>10 emails/sec)")
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
    test_large_batch_validation()