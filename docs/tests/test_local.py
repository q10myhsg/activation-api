#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
os.environ['API_KEY'] = 'a7f8d2e1b4c958f3a6d4c7e2b1a8c9d0'
os.environ['ENCRYPTION_KEY'] = 'openclaw-activation-secret-2026'
os.environ['RATE_LIMIT'] = '60'
os.environ['DB_PATH'] = '/tmp/activation.db'

import sys
sys.path.insert(0, '/root/.openclaw/workspace/tencent-cloud-scf-activation-sqlite')

import json
import importlib
import index
importlib.reload(index)

print("=== 测试生成激活码 ===")

# 模拟生成请求
event = {
    "httpMethod": "POST",
    "path": "/auth/generate",
    "headers": {
        "x-api-key": "a7f8d2e1b4c958f3a6d4c7e2b1a8c9d0"
    },
    "queryString": {
        "apiKey": "a7f8d2e1b4c958f3a6d4c7e2b1a8c9d0"
    },
    "body": json.dumps({
        "duration": 30,
        "count": 2,
        "package_type": "premium"
    }),
    "isBase64Encoded": False
}

result = index.main_handler(event, None)
print(f"状态码: {result['statusCode']}")
print(f"响应: {json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False)}")

# 获取生成的激活码
data = json.loads(result['body'])
if data['status'] == 'success':
    auth_code = data['data']['auth_codes'][0]
    print("\n=== 测试验证激活码 ===")
    
    # 验证请求
    event_verify = {
        "httpMethod": "POST",
        "path": "/auth/verify",
        "headers": {
            "x-api-key": "a7f8d2e1b4c958f3a6d4c7e2b1a8c9d0"
        },
        "queryString": {
            "apiKey": "a7f8d2e1b4c958f3a6d4c7e2b1a8c9d0"
        },
        "body": json.dumps({
            "auth_code": auth_code,
            "machine_code": "test-machine-123456",
            "plugin_version": "1.0.0"
        }),
        "isBase64Encoded": False
    }
    
    result_verify = index.main_handler(event_verify, None)
    print(f"状态码: {result_verify['statusCode']}")
    print(f"响应: {json.dumps(json.loads(result_verify['body']), indent=2, ensure_ascii=False)}")
    
    print("\n=== 测试重复验证（同一机器） ===")
    result_verify2 = index.main_handler(event_verify, None)
    print(f"状态码: {result_verify2['statusCode']}")
    print(f"响应: {json.dumps(json.loads(result_verify2['body']), indent=2, ensure_ascii=False)}")
    
    print("\n=== 测试不同机器绑定 ===")
    event_verify3 = event_verify.copy()
    body = json.loads(event_verify3['body'])
    body['machine_code'] = "another-machine-789"
    event_verify3['body'] = json.dumps(body)
    result_verify3 = index.main_handler(event_verify3, None)
    print(f"状态码: {result_verify3['statusCode']}")
    print(f"响应: {json.dumps(json.loads(result_verify3['body']), indent=2, ensure_ascii=False)}")
