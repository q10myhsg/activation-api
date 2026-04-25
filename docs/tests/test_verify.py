#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace/tencent-cloud-scf-activation-sqlite')

# Mock 环境变量
os.environ['API_KEY'] = 'test'
os.environ['ENCRYPTION_KEY'] = 'testtest'
os.environ['RATE_LIMIT'] = '60'
os.environ['DB_PATH'] = '/tmp/test_activation.db'

# import the module
import index

# Test 1: Generate 3 codes
print("=== Test 1: Generate 3 activation codes ===")
body = {
    "duration": 30,
    "count": 3,
    "package_type": "premium"
}
result = index.handle_generate(body)
print(result)
print()

# Get the first code
codes = result['data']['auth_codes']
first_code = codes[0]
print(f"Generated code: {first_code}")
print()

# Test 2: Verify first code (first activation)
print("=== Test 2: First activation with empty current_expiry ===")
body_verify = {
    "auth_code": first_code,
    "machine_code": "test-device-001",
    "plugin_version": "1.0.0"
}
result_verify = index.handle_verify(body_verify)
print(result_verify)
print()

# Test 3: Verify again with current_expiry matching database
print("=== Test 3: Verify again with correct current_expiry ===")
expiry_date = result_verify['data']['expiry_date']
body_verify2 = {
    "auth_code": first_code,
    "machine_code": "test-device-001",
    "plugin_version": "1.0.0",
    "current_expiry_date": expiry_date
}
result_verify2 = index.handle_verify(body_verify2)
print(result_verify2)
print()

# Test 4: Simulate extension - server updated expiry, client has old expiry
print("=== Test 4: Server extended expiry, client still has old expiry → should return invalid ===")
# This simulates admin extended expiry in database, client still has old
old_expiry = expiry_date
# We manually update expiry in db to be later
# For test, just verify with wrong expiry
fake_old_expiry = "2025-01-01T00:00:00"
body_verify4 = {
    "auth_code": first_code,
    "machine_code": "test-device-001",
    "plugin_version": "1.0.0",
    "current_expiry_date": fake_old_expiry
}
result_verify4 = index.handle_verify(body_verify4)
print(result_verify4)
print()

# Test 5: Transfer from another device - new device with existing expiry
print("=== Test 5: Transfer to new device with existing expiry (prolong) ===")
# Get second code
second_code = codes[1]
# Activate on new device with current_expiry_date from old device
original_duration = 30
old_activated = "2026-02-17T10:00:00"
old_expiry_transfer = "2026-03-19T10:00:00"
body_verify5 = {
    "auth_code": second_code,
    "machine_code": "new-device-002",
    "plugin_version": "1.0.0",
    "current_expiry_date": old_expiry_transfer
}
result_verify5 = index.handle_verify(body_verify5)
print(result_verify5)
print()

# Clean up
if os.path.exists('/tmp/test_activation.db'):
    os.unlink('/tmp/test_activation.db')

print("=== All tests completed ===")
