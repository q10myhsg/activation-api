#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试过期时间计算逻辑 - 本地离线测试"""

import sys
sys.path.insert(0, 'tencent-cloud-scf-activation-sqlite')

from datetime import datetime, timedelta
import sqlite3
import os

# 导入我们修改后的函数
from index import *

def test_unused_activation_calculates_expiry():
    """测试：未使用过的激活码首次激活，应该根据duration计算expiry_date"""
    print("=" * 60)
    print("测试1: 未使用激活码首次激活 → 根据duration计算expiry_date")
    print("=" * 60)
    
    # 生成一个3天有效期的激活码
    duration = 3
    auth_code = f"{duration}_testrandom1234567890"
    
    # 插入数据库
    info = {
        "auth_code": auth_code,
        "duration": duration,
        "package_type": "premium",
        "generate_date": datetime.utcnow().isoformat(),
        "activated_date": None,
        "machine_code": None,
        "expiry_date": None
    }
    insert_activation_code(info)
    
    # 模拟验证请求
    body = {
        "auth_code": auth_code,
        "machine_code": "machine-abc123",
        "current_expiry_date": None
    }
    
    result = handle_verify(body)
    print(f"返回状态: {result['status']}")
    print(f"返回消息: {result['message']}")
    if result['status'] == 'valid' and result['data']:
        print(f"expiry_date: {result['data']['expiry_date']}")
        print(f"activated_date: {result['data']['activated_date']}")
        print(f"machine_code: {result['data']['machine_code']}")
        
        # 检查数据库中的存储
        db_info = get_activation_code(auth_code)
        print(f"\n数据库存储:")
        print(f"  expiry_date: {db_info['expiry_date']}")
        print(f"  activated_date: {db_info['activated_date']}")
        print(f"  machine_code: {db_info['machine_code']}")
        
        # 验证计算是否正确：expiry应该是激活时间 + 3天
        activated = datetime.fromisoformat(db_info['activated_date'])
        expiry = datetime.fromisoformat(db_info['expiry_date'].rstrip('Z'))
        expected_delta = timedelta(days=3)
        actual_delta = expiry - activated
        print(f"\n时间差验证:")
        print(f"  预期: {expected_delta.total_seconds()} 秒")
        print(f"  实际: {actual_delta.total_seconds()} 秒")
        if abs(actual_delta.total_seconds() - expected_delta.total_seconds()) < 2:
            print("✅ 过期时间计算正确！")
        else:
            print("❌ 过期时间计算错误！")
    
    print()

def test_used_activation_checks_current_expiry():
    """测试：已使用激活码，验证current_expiry_date是否匹配"""
    print("=" * 60)
    print("测试2: 已使用激活码重复验证 → 验证current_expiry_date是否匹配")
    print("=" * 60)
    
    duration = 7
    auth_code = f"{duration}_testused12345678"
    
    # 先插入，再模拟首次激活
    info = {
        "auth_code": auth_code,
        "duration": duration,
        "package_type": "premium",
        "generate_date": datetime.utcnow().isoformat(),
        "activated_date": None,
        "machine_code": None,
        "expiry_date": None
    }
    insert_activation_code(info)
    
    # 首次激活
    body1 = {
        "auth_code": auth_code,
        "machine_code": "machine-xyz789",
        "current_expiry_date": None
    }
    result1 = handle_verify(body1)
    print(f"首次激活状态: {result1['status']}")
    stored_expiry = result1['data']['expiry_date']
    print(f"返回的过期时间: {stored_expiry}")
    
    # 二次验证，正确的current_expiry
    print(f"\n二次验证 → 使用正确的current_expiry_date:")
    body2 = {
        "auth_code": auth_code,
        "machine_code": "machine-xyz789",
        "current_expiry_date": stored_expiry
    }
    result2 = handle_verify(body2)
    print(f"返回状态: {result2['status']}")
    if result2['status'] == 'valid':
        print("✅ 正确验证通过！")
    else:
        print("❌ 验证失败，错误")
    
    # 二次验证，错误的current_expiry
    print(f"\n二次验证 → 使用错误的current_expiry_date:")
    wrong_expiry = "2025-01-01T00:00:00Z"
    body3 = {
        "auth_code": auth_code,
        "machine_code": "machine-xyz789",
        "current_expiry_date": wrong_expiry
    }
    result3 = handle_verify(body3)
    print(f"返回状态: {result3['status']}")
    print(f"返回消息: {result3['message']}")
    if result3['status'] == 'invalid':
        print("✅ 正确拒绝不一致的过期时间！")
    else:
        print("❌ 应该拒绝但通过了，错误")
    
    print()

def test_permanent_activation():
    """测试：永久有效激活码"""
    print("=" * 60)
    print("测试3: 永久有效激活码 (-1)")
    print("=" * 60)
    
    duration = -1
    auth_code = f"{duration}_testpermanent12345"
    
    info = {
        "auth_code": auth_code,
        "duration": duration,
        "package_type": "lifetime",
        "generate_date": datetime.utcnow().isoformat(),
        "activated_date": None,
        "machine_code": None,
        "expiry_date": None
    }
    insert_activation_code(info)
    
    body = {
        "auth_code": auth_code,
        "machine_code": "machine-perm",
        "current_expiry_date": None
    }
    result = handle_verify(body)
    print(f"返回状态: {result['status']}")
    if result['status'] == 'valid':
        print(f"expiry_date: {result['data']['expiry_date']}")
        db_info = get_activation_code(auth_code)
        print(f"数据库 expiry_date: {db_info['expiry_date']}")
        if '9999' in str(db_info['expiry_date']):
            print("✅ 永久激活正确设置！")
        else:
            print("❌ 永久激活设置错误")
    print()

def test_expired_activation():
    """测试：已过期激活码返回 expired"""
    print("=" * 60)
    print("测试4: 已过期激活码 → 返回 expired 状态")
    print("=" * 60)
    
    # 创建一个已过期的激活码
    auth_code = "1_testexpired1234567"
    yesterday = (datetime.utcnow() - timedelta(days=2)).isoformat()
    info = {
        "auth_code": auth_code,
        "duration": 1,
        "package_type": "basic",
        "generate_date": yesterday,
        "activated_date": yesterday,
        "machine_code": "machine-expired",
        "expiry_date": (datetime.utcnow() - timedelta(days=1)).isoformat()
    }
    insert_activation_code(info)
    
    body = {
        "auth_code": auth_code,
        "machine_code": "machine-expired",
        "current_expiry_date": info['expiry_date']
    }
    result = handle_verify(body)
    print(f"返回状态: {result['status']}")
    print(f"返回消息: {result['message']}")
    if result['status'] == 'expired':
        print("✅ 正确识别过期！")
    else:
        print("❌ 没有识别出过期，错误")
    print()

def main():
    print("🚀 开始本地测试过期时间计算逻辑...\n")
    
    # 初始化数据库到临时文件
    global CONFIG
    CONFIG["db_path"] = "/tmp/test_expiry.db"
    if os.path.exists(CONFIG["db_path"]):
        os.unlink(CONFIG["db_path"])
    
    init_db()
    
    # 运行所有测试
    test_unused_activation_calculates_expiry()
    test_used_activation_checks_current_expiry()
    test_permanent_activation()
    test_expired_activation()
    
    print("\n" + "=" * 60)
    print("🎯 所有测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
