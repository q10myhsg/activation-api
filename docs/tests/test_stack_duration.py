#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace/tencent-cloud-scf-activation-sqlite')

# 设置环境变量
os.environ['API_KEY'] = 'test-api-key'
os.environ['ENCRYPTION_KEY'] = 'test-encryption-key'
os.environ['RATE_LIMIT'] = '60'
os.environ['DB_PATH'] = '/tmp/test-stack-duration.db'

# 导入
import index

# 清除旧测试
if os.path.exists('/tmp/test-stack-duration.db'):
    os.unlink('/tmp/test-stack-duration.db')

index.init_db()

print("=== Test 1: Generate two 30-day codes for same device ===")

# 生成两个 30 天激活码
body_gen1 = {
    "duration": 30,
    "count": 2,
    "package_type": "premium"
}
result_gen = index.handle_generate(body_gen1)
print(result_gen)
print()

codes = result_gen['data']['auth_codes']
code1 = codes[0]
code2 = codes[1]
print(f"Code 1: {code1}")
print(f"Code 2: {code2}")
print()

# 激活第一个
print("=== Activate first code on device test-device-001 ===")
body_verify1 = {
    "auth_code": code1,
    "machine_code": "test-device-001",
    "version": "1.0.0",
    "auth_type": "plugin"
}
result_verify1 = index.handle_verify(body_verify1)
print(result_verify1)
print()

expiry1 = result_verify1['data']['expiry_date']
print(f"First expiry: {expiry1}")
print()

# 激活第二个同一个设备 → 应该叠加 → 过期时间 30 + 30 = 60 天
print("=== Activate second code on SAME device test-device-001 → should STACK duration ===")
body_verify2 = {
    "auth_code": code2,
    "machine_code": "test-device-001",
    "version": "1.0.0",
    "auth_type": "plugin"
}
result_verify2 = index.handle_verify(body_verify2)
print(result_verify2)
print()

expiry2 = result_verify2['data']['expiry_date']
print(f"Second expiry after stack: {expiry2}")
print()

# 解析两个过期时间比较天数
from datetime import datetime
exp1_dt = datetime.fromisoformat(expiry1.split('.')[0])
exp2_dt = datetime.fromisoformat(expiry2.split('.')[0])
now = datetime.utcnow()
days1 = (exp1_dt - now).days
days2 = (exp2_dt - now).days

print(f"Days after first activation: ~{days1} days")
print(f"Days after second activation (stacked): ~{days2} days")
print(f"Expected ~{days1} + 30 = ~{days1 + 30} days, got ~{days2} days")

if days2 > days1 + 25:
    print("\n✅ TEST PASSED: Duration stacked correctly!")
else:
    print("\n❌ TEST FAILED: Duration not stacked")

print()
print("=== Test permission interface ===")
body_perm = {
    "machine_code": "test-device-001",
    "version": "1.0.0",
    "auth_type": "plugin",
    "auth_code": code2
}
result_perm = index.handle_permission(body_perm)
print(result_perm)

# 清理
if os.path.exists('/tmp/test-stack-duration.db'):
    os.unlink('/tmp/test-stack-duration.db')

print("\n=== All tests done ===")
