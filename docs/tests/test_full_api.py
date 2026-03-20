#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace/tencent-cloud-scf-activation-sqlite')

# 设置环境变量
os.environ['API_KEY'] = 'test-api-key'
os.environ['ENCRYPTION_KEY'] = 'test-encryption-key'
os.environ['RATE_LIMIT'] = '60'
os.environ['DB_PATH'] = '/tmp/test-full-api.db'

# 导入模块
import index

# 清除旧测试
if os.path.exists('/tmp/test-full-api.db'):
    os.unlink('/tmp/test-full-api.db')

index.init_db()

print("=== Test 1: Generate activation codes ===")
body_generate = {
    "duration": 30,
    "count": 2,
    "package_type": "premium"
}
result = index.handle_generate(body_generate)
print(result)
print()

auth_codes = result['data']['auth_codes']
first_code = auth_codes[0]
second_code = auth_codes[1]
print(f"Generated codes: {auth_codes}")
print()

print("=== Test 2: Verify with all required parameters ===")
body_verify = {
    "auth_code": first_code,
    "machine_code": "device-001",
    "version": "1.0.0",
    "auth_type": "plugin"
}
result_verify = index.handle_verify(body_verify)
print(result_verify)
print()

expiry_date = result_verify['data']['expiry_date']

print("=== Test 3: Verify again with current_expiry_date ===")
body_verify2 = {
    "auth_code": first_code,
    "machine_code": "device-001",
    "version": "1.0.0",
    "auth_type": "plugin",
    "current_expiry_date": expiry_date
}
result_verify2 = index.handle_verify(body_verify2)
print(result_verify2)
print()

print("=== Test 4: Permission interface - unauthenticated ===")
body_perm1 = {
    "machine_code": "device-002",
    "version": "1.0.0",
    "auth_type": "plugin"
}
result_perm1 = index.handle_permission(body_perm1)
print(result_perm1)
print()

print("=== Test 5: Permission interface - authenticated premium ===")
body_perm2 = {
    "machine_code": "device-001",
    "version": "1.0.0",
    "auth_type": "plugin",
    "auth_code": first_code
}
result_perm2 = index.handle_permission(body_perm2)
print(result_perm2)
print()

print("=== Test 6: Verify with wrong current_expiry_date (should return invalid) ===")
body_verify3 = {
    "auth_code": first_code,
    "machine_code": "device-001",
    "version": "1.0.0",
    "auth_type": "plugin",
    "current_expiry_date": "2025-01-01T00:00:00"
}
result_verify3 = index.handle_verify(body_verify3)
print(result_verify3)
print()

print("=== Test 7: Verify with missing required parameter (version) ===")
body_verify_bad = {
    "auth_code": first_code,
    "machine_code": "device-001",
    "auth_type": "plugin"
}
result_verify_bad = index.handle_verify(body_verify_bad)
print(result_verify_bad)
print()

# Clean up
if os.path.exists('/tmp/test-full-api.db'):
    os.unlink('/tmp/test-full-api.db')

print("=== All tests completed ===")
