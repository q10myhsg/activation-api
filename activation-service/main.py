from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import sqlite3
import hashlib
import base64
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="激活码管理API", version="1.0.0")

# API Key 验证
API_KEY = os.getenv("API_KEY", "default_api_key_123456")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="未授权的API Key")
    return api_key

# 数据模型
class VerifyRequest(BaseModel):
    auth_code: str = Field(..., description="激活码")
    machine_code: str = Field(..., description="机器码")
    plugin_version: str = Field(..., description="插件版本号")
    current_expiry_date: Optional[str] = Field(None, description="当前过期时间")

class GenerateRequest(BaseModel):
    duration: int = Field(..., description="有效期天数（1、7、30、365、-1表示永久）")
    count: Optional[int] = Field(1, description="生成激活码的数量")
    package_type: str = Field(..., description="套餐类型")

class VerifyResponse(BaseModel):
    status: str = Field(..., description="验证状态")
    message: str = Field(..., description="状态描述")
    data: Optional[Dict] = Field(None, description="验证成功时返回的详细信息")

class GenerateResponse(BaseModel):
    status: str = Field(..., description="生成状态")
    message: str = Field(..., description="状态描述")
    data: Optional[Dict] = Field(None, description="生成成功时返回的详细信息")

# 数据库操作
def init_db():
    conn = sqlite3.connect('activation_codes.db')
    cursor = conn.cursor()
    
    # 创建激活码表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activation_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auth_code TEXT UNIQUE NOT NULL,
        duration INTEGER NOT NULL,
        package_type TEXT NOT NULL,
        generate_date TEXT NOT NULL,
        activated_date TEXT,
        machine_code TEXT,
        expiry_date TEXT,
        is_used BOOLEAN DEFAULT 0,
        is_expired BOOLEAN DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()

def generate_auth_code(duration: int) -> str:
    """生成激活码"""
    # 生成随机数据
    random_data = str(uuid.uuid4()).encode('utf-8')
    
    # 使用SHA256加密
    hash_obj = hashlib.sha256(random_data)
    hash_hex = hash_obj.hexdigest()
    
    # 转换为base64并截取部分
    b64_encoded = base64.urlsafe_b64encode(hash_hex.encode('utf-8')).decode('utf-8').rstrip('=')
    
    # 格式：{duration}_{encrypted_data}
    return f"{duration}_{b64_encoded[:32]}"

def save_auth_codes(auth_codes: List[str], duration: int, package_type: str):
    """保存激活码到数据库"""
    conn = sqlite3.connect('activation_codes.db')
    cursor = conn.cursor()
    
    generate_date = datetime.utcnow().isoformat()
    
    for code in auth_codes:
        cursor.execute('''
        INSERT OR IGNORE INTO activation_codes (auth_code, duration, package_type, generate_date)
        VALUES (?, ?, ?, ?)
        ''', (code, duration, package_type, generate_date))
    
    conn.commit()
    conn.close()

def get_auth_code_info(auth_code: str) -> Optional[Dict]:
    """获取激活码信息"""
    conn = sqlite3.connect('activation_codes.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM activation_codes WHERE auth_code = ?
    ''', (auth_code,))
    
    row = cursor.fetchone()
    if row:
        return {
            'id': row[0],
            'auth_code': row[1],
            'duration': row[2],
            'package_type': row[3],
            'generate_date': row[4],
            'activated_date': row[5],
            'machine_code': row[6],
            'expiry_date': row[7],
            'is_used': row[8],
            'is_expired': row[9]
        }
    
    conn.close()
    return None

def update_auth_code(auth_code: str, data: Dict):
    """更新激活码信息"""
    conn = sqlite3.connect('activation_codes.db')
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    values = list(data.values()) + [auth_code]
    
    cursor.execute(f'''
    UPDATE activation_codes SET {set_clause} WHERE auth_code = ?
    ''', values)
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# API 接口
@app.post("/v1/auth/verify", response_model=VerifyResponse)
async def verify_auth_code(request: VerifyRequest, api_key: str = Depends(get_api_key)):
    """验证激活码"""
    # 解析激活码
    if '_' not in request.auth_code:
        raise HTTPException(status_code=400, detail="激活码格式错误")
    
    duration_part, encrypted_part = request.auth_code.split('_', 1)
    
    # 检查激活码是否存在
    auth_code_info = get_auth_code_info(request.auth_code)
    if not auth_code_info:
        return VerifyResponse(
            status="invalid",
            message="激活码不存在",
            data=None
        )
    
    # 检查是否已过期
    now = datetime.utcnow()
    
    if auth_code_info['is_expired']:
        return VerifyResponse(
            status="expired",
            message="激活码已过期",
            data=None
        )
    
    # 检查是否已被其他设备使用
    if auth_code_info['is_used'] and auth_code_info['machine_code'] != request.machine_code:
        return VerifyResponse(
            status="used",
            message="激活码已被其他设备使用",
            data=None
        )
    
    # 计算过期时间
    expiry_date = None
    if auth_code_info['is_used']:
        # 已使用，验证当前过期时间是否一致
        if request.current_expiry_date and auth_code_info['expiry_date'] != request.current_expiry_date:
            return VerifyResponse(
                status="invalid",
                message="过期时间不一致",
                data=None
            )
        expiry_date = auth_code_info['expiry_date']
    else:
        # 未使用，计算过期时间
        duration = auth_code_info['duration']
        if duration == -1:
            # 永久有效
            expiry_date = None
        else:
            activated_date = now
            expiry_date = (activated_date + timedelta(days=duration)).isoformat()
            
            # 更新激活码信息
            update_auth_code(request.auth_code, {
                'activated_date': activated_date.isoformat(),
                'machine_code': request.machine_code,
                'expiry_date': expiry_date,
                'is_used': 1
            })
    
    # 检查是否过期
    if expiry_date and datetime.fromisoformat(expiry_date) < now:
        update_auth_code(request.auth_code, {'is_expired': 1})
        return VerifyResponse(
            status="expired",
            message="激活码已过期",
            data=None
        )
    
    # 返回成功响应
    return VerifyResponse(
        status="valid",
        message="激活码验证成功",
        data={
            "expiry_date": expiry_date,
            "activated_date": auth_code_info['activated_date'] or now.isoformat(),
            "machine_code": auth_code_info['machine_code'] or request.machine_code
        }
    )

@app.post("/v1/auth/generate", response_model=GenerateResponse)
async def generate_auth_codes(request: GenerateRequest, api_key: str = Depends(get_api_key)):
    """生成激活码"""
    # 验证参数
    valid_durations = [1, 7, 30, 365, -1]
    if request.duration not in valid_durations:
        raise HTTPException(status_code=400, detail=f"无效的有效期天数，有效值：{valid_durations}")
    
    if request.count < 1 or request.count > 100:
        raise HTTPException(status_code=400, detail="生成数量必须在1-100之间")
    
    # 生成激活码
    auth_codes = []
    for _ in range(request.count):
        while True:
            code = generate_auth_code(request.duration)
            # 确保唯一性
            if not get_api_key(code):
                auth_codes.append(code)
                break
    
    # 保存到数据库
    save_auth_codes(auth_codes, request.duration, request.package_type)
    
    # 返回响应
    return GenerateResponse(
        status="success",
        message="激活码生成成功",
        data={
            "auth_codes": auth_codes,
            "duration": request.duration,
            "generate_date": datetime.utcnow().isoformat()
        }
    )

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "服务运行正常"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)