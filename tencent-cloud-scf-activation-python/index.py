#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import hashlib
import hmac
import base64
import time
from datetime import datetime, timedelta
import os
import traceback
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# -------------------------- 配置 --------------------------
CONFIG = {
    "api_key": os.environ.get("API_KEY", "your-secret-api-key-here"),
    "encryption_key": os.environ.get("ENCRYPTION_KEY", "your-encryption-secret-key").encode('utf-8'),
    "rate_limit": int(os.environ.get("RATE_LIMIT", "60")),  # 每分钟最大请求数
    "mongo_uri": os.environ.get("MONGO_URI", ""),  # MongoDB连接URI
    "mongo_db": os.environ.get("MONGO_DB", "activation_db"),  # 数据库名
    "mongo_collection": os.environ.get("MONGO_COLLECTION", "activation_codes"),  # 集合名
}

# -------------------------- 数据存储 - MongoDB --------------------------
mongo_client = None
mongo_db = None
collection = None
rate_limit_requests = {}  # 频率限制仍使用内存，可接受

def get_mongo_collection():
    """获取MongoDB集合，懒加载连接"""
    global mongo_client, mongo_db, collection
    if collection is not None:
        return collection
    if not CONFIG["mongo_uri"]:
        raise Exception("请配置 MONGO_URI 环境变量")
    mongo_client = MongoClient(CONFIG["mongo_uri"], serverSelectionTimeoutMS=5000)
    # 测试连接
    mongo_client.admin.command('ping')
    mongo_db = mongo_client[CONFIG["mongo_db"]]
    collection = mongo_db[CONFIG["mongo_collection"]]
    # 创建索引
    collection.create_index("auth_code", unique=True)
    return collection

# 内存降级方案，如果MongoDB不可用
fallback_activation_codes = {}

# -------------------------- 加密工具 --------------------------
def encrypt_data(data: dict) -> str:
    """使用HMAC+SHA256加密数据，生成激活码部分"""
    data_str = json.dumps(data, sort_keys=True)
    signature = hmac.new(CONFIG["encryption_key"], data_str.encode('utf-8'), hashlib.sha256).hexdigest()
    combined = f"{data_str}|{signature}"
    return base64.urlsafe_b64encode(combined.encode('utf-8')).decode('utf-8')

def decrypt_data(encrypted: str) -> dict | None:
    """解密并验证激活码数据"""
    try:
        decoded = base64.urlsafe_b64decode(encrypted.encode('utf-8')).decode('utf-8')
        parts = decoded.rsplit('|', 1)
        if len(parts) != 2:
            return None
        data_str, signature = parts
        data = json.loads(data_str)
        
        # 验证签名
        expected_signature = hmac.new(CONFIG["encryption_key"], data_str.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None
        return data
    except Exception:
        return None

# -------------------------- 频率限制 --------------------------
def check_rate_limit(client_ip: str) -> bool:
    """检查请求频率限制"""
    now = int(time.time())
    window_start = now - 60  # 1分钟窗口
    
    # 清理过期请求
    if client_ip not in rate_limit_requests:
        rate_limit_requests[client_ip] = []
    
    # 过滤掉过期请求
    requests = [t for t in rate_limit_requests[client_ip] if t > window_start]
    
    if len(requests) >= CONFIG["rate_limit"]:
        return False
    
    requests.append(now)
    rate_limit_requests[client_ip] = requests
    return True

# -------------------------- 接口处理 --------------------------
def handle_verify(body: dict) -> dict:
    """处理激活码验证请求"""
    auth_code = body.get("auth_code")
    machine_code = body.get("machine_code")
    
    if not auth_code or not machine_code:
        return {
            "status": "invalid",
            "message": "缺少必填参数 auth_code 或 machine_code",
            "data": None
        }
    
    # 拆分激活码
    parts = auth_code.split('_', 1)
    if len(parts) != 2:
        return {
            "status": "invalid",
            "message": "激活码格式错误",
            "data": None
        }
    
    duration_str, encrypted_data = parts
    
    # 查询存储
    try:
        coll = get_mongo_collection()
        info = coll.find_one({"auth_code": auth_code})
        if not info:
            return {
                "status": "invalid",
                "message": "激活码不存在",
                "data": None
            }
        # 转换ObjectId
        if "_id" in info:
            del info["_id"]
    except Exception:
        traceback.print_exc()
        # 降级到内存存储
        if auth_code not in fallback_activation_codes:
            return {
                "status": "invalid",
                "message": "激活码不存在，数据库连接异常",
                "data": None
            }
        info = fallback_activation_codes[auth_code]
    
    # 检查设备绑定
    if info.get("machine_code") and info["machine_code"] != machine_code:
        return {
            "status": "used",
            "message": "激活码已被其他设备绑定",
            "data": None
        }
    
    # 检查是否过期
    now = datetime.utcnow()
    if info.get("expiry_date"):
        expiry = datetime.fromisoformat(info["expiry_date"].replace('Z', '+00:00'))
        if now > expiry:
            return {
                "status": "expired",
                "message": "激活码已过期",
                "data": None
            }
    
    # 检查当前过期时间是否一致（可选参数）
    current_expiry = body.get("current_expiry_date")
    if current_expiry and current_expiry != info.get("expiry_date"):
        return {
            "status": "invalid",
            "message": "激活信息已失效，请重新验证",
            "data": None
        }
    
    # 首次激活，绑定设备计算过期时间
    if not info.get("machine_code"):
        info["machine_code"] = machine_code
        info["activated_date"] = datetime.utcnow().isoformat() + 'Z'
        duration = info.get("duration")
        if duration == -1:  # 永久
            info["expiry_date"] = "9999-12-31T23:59:59Z"
        else:
            activated = datetime.fromisoformat(info["activated_date"].replace('Z', '+00:00'))
            expiry = activated + timedelta(days=duration)
            info["expiry_date"] = expiry.isoformat().replace('+00:00', 'Z')
        
        # 更新存储
        try:
            coll = get_mongo_collection()
            coll.update_one({"auth_code": auth_code}, {"$set": info})
        except Exception:
            traceback.print_exc()
            fallback_activation_codes[auth_code] = info
    
    return {
        "status": "valid",
        "message": "激活码验证成功",
        "data": {
            "expiry_date": info["expiry_date"],
            "activated_date": info["activated_date"],
            "machine_code": info["machine_code"]
        }
    }

def handle_generate(body: dict) -> dict:
    """处理生成激活码请求"""
    duration = body.get("duration")
    count = body.get("count", 1)
    package_type = body.get("package_type")
    
    if duration is None or not package_type:
        return {
            "status": "error",
            "message": "缺少必填参数 duration 或 package_type",
            "data": None
        }
    
    # 验证duration
    allowed_durations = [1, 7, 30, 365, -1]
    if duration not in allowed_durations:
        return {
            "status": "error",
            "message": "duration 必须为 1、7、30、365 或 -1（永久）",
            "data": None
        }
    
    auth_codes = []
    generate_date = datetime.utcnow().isoformat() + 'Z'
    
    for _ in range(count):
        # 生成激活码
        encrypted = encrypt_data({
            "duration": duration,
            "package_type": package_type,
            "ts": int(time.time() * 1000) + _  # 保证每个激活码唯一
        })
        auth_code = f"{duration}_{encrypted}"
        
        # 存储数据
        info = {
            "auth_code": auth_code,
            "duration": duration,
            "package_type": package_type,
            "generate_date": generate_date,
            "activated_date": None,
            "machine_code": None,
            "expiry_date": None
        }
        
        # 写入存储
        try:
            coll = get_mongo_collection()
            coll.insert_one(info)
        except Exception:
            traceback.print_exc()
            # 降级到内存
            if "_id" in info:
                del info["_id"]
            fallback_activation_codes[auth_code] = info
        
        auth_codes.append(auth_code)
    
    return {
        "status": "success",
        "message": f"成功生成 {count} 个激活码",
        "data": {
            "auth_codes": auth_codes,
            "duration": duration,
            "generate_date": generate_date
        }
    }

# -------------------------- 主入口 --------------------------
def main_handler(event, context):
    """腾讯云函数入口"""
    # CORS头
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-API-Key"
    }
    
    # 获取客户端IP
    client_ip = event.get("requestContext", {}).get("sourceIp", 
                event.get("headers", {}).get("x-forwarded-for", "127.0.0.1"))
    
    # 频率限制
    if not check_rate_limit(client_ip):
        return {
            "statusCode": 429,
            "headers": headers,
            "body": json.dumps({
                "status": "error",
                "message": "请求过于频繁，请稍后再试",
                "data": None
            })
        }
    
    # 处理OPTIONS跨域
    http_method = event.get("httpMethod", "").upper()
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": ""
        }
    
    # 验证API Key
    request_api_key = event.get("headers", {}).get("x-api-key", 
                    event.get("queryString", {}).get("apiKey", 
                    (event.get("body") if isinstance(event.get("body"), dict) else {}).get("apiKey")))
    if request_api_key != CONFIG["api_key"]:
        return {
            "statusCode": 401,
            "headers": headers,
            "body": json.dumps({
                "status": "error",
                "message": "API Key 无效",
                "data": None
            })
        }
    
    try:
        # 解析请求体
        body = event.get("body")
        if event.get("isBase64Encoded") and body:
            body = base64.b64decode(body).decode('utf-8')
        if isinstance(body, str):
            body = json.loads(body)
        
        path = event.get("path", "")
        result = None
        
        if path.endswith("/auth/verify") and http_method == "POST":
            result = handle_verify(body)
        elif path.endswith("/auth/generate") and http_method == "POST":
            result = handle_generate(body)
        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({
                    "status": "error",
                    "message": "接口不存在",
                    "data": None
                })
            }
        
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "status": "error",
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, ensure_ascii=False)
        }
