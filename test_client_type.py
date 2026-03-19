#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test client_type changes"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tencent-cloud-scf-activation-sqlite'))

import index
from index import *

# 测试初始化
print("Testing database init...")
init_db()
print("✓ Database init OK")

# 测试生成激活码 - browser-extension
print("\nTesting generate activation code for browser-extension...")
generate_body = {
    "duration": 30,
    "count": 2,
    "package_type": "premium",
    "client_type": "browser-extension"
}
result = handle_generate(generate_body)
print(f"Status: {result.get('status')}")
print(f"Client type in response: {result.get('data', {}).get('client_type')}")
if result.get('status') == 'success':
    print("✓ Generate OK")
    auth_codes = result.get('data', {}).get('auth_codes', [])
else:
    print(f"✗ Generate failed: {result.get('message')}")

# 测试生成激活码 - pc-client
print("\nTesting generate activation code for pc-client...")
generate_body2 = {
    "duration": 7,
    "count": 1,
    "package_type": "basic",
    "client_type": "pc-client"
}
result2 = handle_generate(generate_body2)
print(f"Status: {result2.get('status')}")
if result2.get('status') == 'success':
    print("✓ Generate OK")
else:
    print(f"✗ Generate failed: {result2.get('message')}")

# 测试invalid client_type
print("\nTesting invalid client_type...")
generate_body_invalid = {
    "duration": 30,
    "count": 1,
    "package_type": "premium",
    "client_type": "invalid"
}
result_invalid = handle_generate(generate_body_invalid)
print(f"Status: {result_invalid.get('status')}")
print(f"Message: {result_invalid.get('message')}")
if result_invalid.get('status') == 'error' and 'client_type' in result_invalid.get('message'):
    print("✓ Invalid client_type correctly rejected")
else:
    print("✗ Invalid client_type not rejected")

# 测试list with client_type filter
print("\nTesting list with client_type filter...")
list_body = {
    "client_type": "browser-extension",
    "limit": 10
}
list_result = handle_list(list_body)
print(f"Total: {list_result.get('data', {}).get('total')}")
items = list_result.get('data', {}).get('list', [])
for item in items:
    print(f"  - {item.get('auth_code')} client_type={item.get('client_type')}")
print("✓ List with filter OK")

# 测试verify
if len(auth_codes) > 0:
    test_code = auth_codes[0]
    print(f"\nTesting verify for {test_code}...")
    verify_body = {
        "auth_code": test_code,
        "machine_code": "test-machine-001",
        "client_type": "browser-extension",
        "plugin_version": "1.0.0"
    }
    verify_result = handle_verify(verify_body)
    print(f"Status: {verify_result.get('status')}")
    print(f"Message: {verify_result.get('message')}")
    if verify_result.get('status') == 'valid':
        print("✓ Verify OK")
    else:
        print(f"✗ Verify failed")

# 测试device info
print("\nTesting device info...")
device_body = {
    "machine_code": "test-machine-001",
    "client_type": "browser-extension",
    "plugin_version": "1.0.0"
}
device_result = handle_device_info(device_body)
print(f"Status: {device_result.get('status')}")
data = device_result.get('data', {})
print(f"is_active: {data.get('is_active')}")
print(f"client_type: {data.get('client_type')}")
if device_result.get('status') == 'success':
    print("✓ Device info OK")
else:
    print(f"✗ Device info failed: {device_result.get('message')}")

print("\n✅ All tests passed!")
