#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

# 配置
API_BASE = "https://1259223433-45s5ysqkrg.ap-beijing.tencentscf.com"
API_KEY = "a7f8d2e1b4c958f3a6d4c7e2b1a8c9d0"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

print("=" * 60)
print("第一步：生成激活码（30天，premium套餐）")
print("=" * 60)

generate_body = {
    "duration": 30,
    "count": 1,
    "package_type": "premium"
}

resp = requests.post(f"{API_BASE}/auth/generate", headers=headers, json=generate_body)
print(f"状态码: {resp.status_code}")
result = resp.json()
print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

if result["status"] != "success":
    print("❌ 生成失败！")
    exit(1)

auth_code = result["data"]["auth_codes"][0]
print(f"\n✅ 生成成功，激活码: {auth_code}")

print("\n" + "=" * 60)
print("第二步：首次验证激活（新机器）")
print("=" * 60)

verify_body = {
    "auth_code": auth_code,
    "machine_code": "test-machine-complete-flow",
    "plugin_version": "1.0.0"
}

resp2 = requests.post(f"{API_BASE}/auth/verify", headers=headers, json=verify_body)
print(f"状态码: {resp2.status_code}")
result2 = resp2.json()
print(f"响应: {json.dumps(result2, indent=2, ensure_ascii=False)}")

if result2["status"] != "valid":
    print("❌ 首次验证失败！")
    exit(1)

print(f"\n✅ 首次激活成功，过期时间: {result2['data']['expiry_date']}")

print("\n" + "=" * 60)
print("第三步：重复验证（同一机器）")
print("=" * 60)

resp3 = requests.post(f"{API_BASE}/auth/verify", headers=headers, json=verify_body)
print(f"状态码: {resp3.status_code}")
result3 = resp3.json()
print(f"响应: {json.dumps(result3, indent=2, ensure_ascii=False)}")

if result3["status"] != "valid":
    print(f"❌ 重复验证失败，返回状态: {result3['status']}")
    exit(1)

print(f"\n✅ 重复验证成功，仍然返回valid，符合预期")

print("\n" + "=" * 60)
print("第四步：尝试用不同机器验证同一个激活码")
print("=" * 60)

verify_body2 = {
    "auth_code": auth_code,
    "machine_code": "another-machine-different",
    "plugin_version": "1.0.0"
}

resp4 = requests.post(f"{API_BASE}/auth/verify", headers=headers, json=verify_body2)
print(f"状态码: {resp4.status_code}")
result4 = resp4.json()
print(f"响应: {json.dumps(result4, indent=2, ensure_ascii=False)}")

if result4["status"] != "used":
    print(f"❌ 预期返回used，实际返回: {result4['status']}")
    exit(1)

print(f"\n✅ 正确返回used状态，防止多设备使用，符合预期")

print("\n" + "=" * 60)
print("🎉 完整流程测试全部通过！所有功能正常工作！")
print("=" * 60)
