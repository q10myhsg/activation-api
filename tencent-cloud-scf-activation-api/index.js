'use strict';

const crypto = require('crypto');

// 数据存储（腾讯云函数默认无持久化存储，这里使用内存存储，重启会丢失。生产环境建议对接云数据库如MongoDB/MySQL）
let activationCodes = new Map();

// 配置项
const CONFIG = {
  // API Key 验证密钥，请自行修改为复杂密钥
  apiKey: process.env.API_KEY || 'your-secret-api-key-here',
  // 加密密钥，请自行修改为随机字符串
  encryptionKey: process.env.ENCRYPTION_KEY || 'your-encryption-secret-key',
  // 请求频率限制（每分钟最大请求数）
  rateLimit: parseInt(process.env.RATE_LIMIT || '60', 10),
  // 频率限制存储
  rateLimitRequests: new Map()
};

/**
 * 生成加密的激活码数据
 */
function encryptActivationCode(duration, packageType) {
  const data = JSON.stringify({
    duration,
    packageType,
    timestamp: Date.now()
  });
  
  const cipher = crypto.createCipheriv('aes256', Buffer.from(CONFIG.encryptionKey.padEnd(32).slice(0, 32)), Buffer.alloc(16));
  let encrypted = cipher.update(data, 'utf8', 'base64');
  encrypted += cipher.final('base64');
  return encrypted;
}

/**
 * 解密激活码数据
 */
function decryptActivationCode(encryptedData) {
  try {
    const decipher = crypto.createDecipheriv('aes256', Buffer.from(CONFIG.encryptionKey.padEnd(32).slice(0, 32)), Buffer.alloc(16));
    let decrypted = decipher.update(encryptedData, 'base64', 'utf8');
    decrypted += decipher.final('utf8');
    return JSON.parse(decrypted);
  } catch (e) {
    return null;
  }
}

/**
 * 检查请求频率限制
 */
function checkRateLimit(clientIp) {
  const now = Date.now();
  const windowStart = now - 60 * 1000;
  
  // 清理过期请求
  if (!CONFIG.rateLimitRequests.has(clientIp)) {
    CONFIG.rateLimitRequests.set(clientIp, []);
  }
  
  let requests = CONFIG.rateLimitRequests.get(clientIp).filter(time => time > windowStart);
  if (requests.length >= CONFIG.rateLimit) {
    return false;
  }
  
  requests.push(now);
  CONFIG.rateLimitRequests.set(clientIp, requests);
  return true;
}

/**
 * 验证API Key
 */
function verifyApiKey(event) {
  const apiKey = event.headers['x-api-key'] || event.queryString?.apiKey || event.body?.apiKey;
  return apiKey === CONFIG.apiKey;
}

/**
 * 解析请求体
 */
function parseBody(event) {
  if (event.isBase64Encoded) {
    return JSON.parse(Buffer.from(event.body, 'base64').toString('utf8'));
  }
  if (typeof event.body === 'string') {
    return JSON.parse(event.body);
  }
  return event.body || {};
}

/**
 * 处理验证激活码请求
 */
function handleVerify(body) {
  const { auth_code, machine_code, plugin_version, current_expiry_date } = body;
  
  // 校验必填参数
  if (!auth_code || !machine_code) {
    return {
      status: 'invalid',
      message: '缺少必填参数 auth_code 或 machine_code',
      data: null
    };
  }
  
  // 拆分激活码格式
  const parts = auth_code.split('_');
  if (parts.length !== 2) {
    return {
      status: 'invalid',
      message: '激活码格式错误',
      data: null
    };
  }
  
  // 查询存储的激活码信息
  const existing = activationCodes.get(auth_code);
  
  if (!existing) {
    return {
      status: 'invalid',
      message: '激活码不存在',
      data: null
    };
  }
  
  // 检查是否被其他设备使用
  if (existing.machineCode && existing.machineCode !== machine_code) {
    return {
      status: 'used',
      message: '激活码已被其他设备绑定',
      data: null
    };
  }
  
  // 检查是否过期
  const now = new Date();
  const expiryDate = new Date(existing.expiryDate);
  if (now > expiryDate) {
    return {
      status: 'expired',
      message: '激活码已过期',
      data: null
    };
  }
  
  // 检查当前过期时间是否一致（可选参数校验）
  if (current_expiry_date && new Date(current_expiry_date).toISOString() !== existing.expiryDate) {
    return {
      status: 'invalid',
      message: '激活信息已失效，请重新验证',
      data: null
    };
  }
  
  // 首次激活，绑定机器码和计算过期时间
  if (!existing.machineCode) {
    existing.machineCode = machine_code;
    existing.activatedDate = new Date().toISOString();
    // 计算过期时间：激活时间 + 有效期
    const activatedDate = new Date(existing.activatedDate);
    if (existing.duration !== -1) { // -1 表示永久
      activatedDate.setDate(activatedDate.getDate() + existing.duration);
      existing.expiryDate = activatedDate.toISOString();
    } else {
      existing.expiryDate = '9999-12-31T23:59:59Z';
    }
    activationCodes.set(auth_code, existing);
  }
  
  return {
    status: 'valid',
    message: '激活码验证成功',
    data: {
      expiry_date: existing.expiryDate,
      activated_date: existing.activatedDate,
      machine_code: existing.machineCode
    }
  };
}

/**
 * 处理生成激活码请求
 */
function handleGenerate(body) {
  const { duration, count = 1, package_type } = body;
  
  // 校验必填参数
  if (duration === undefined || !package_type) {
    return {
      status: 'error',
      message: '缺少必填参数 duration 或 package_type',
      data: null
    };
  }
  
  // 校验duration是否合法
  const allowedDurations = [1, 7, 30, 365, -1];
  if (!allowedDurations.includes(duration)) {
    return {
      status: 'error',
      message: 'duration 必须为 1、7、30、365 或 -1（永久）',
      data: null
    };
  }
  
  const authCodes = [];
  const generateDate = new Date().toISOString();
  
  for (let i = 0; i < count; i++) {
    // 加密生成数据
    const encrypted = encryptActivationCode(duration, package_type);
    const authCode = `${duration}_${encrypted}`;
    
    // 存储激活码信息
    activationCodes.set(authCode, {
      duration,
      packageType,
      generateDate,
      activatedDate: null,
      machineCode: null,
      expiryDate: null
    });
    
    authCodes.push(authCode);
  }
  
  return {
    status: 'success',
    message: `成功生成 ${count} 个激活码`,
    data: {
      auth_codes: authCodes,
      duration,
      generate_date: generateDate
    }
  };
}

/**
 * 腾讯云函数入口
 */
exports.main_handler = async (event, context) => {
  // 获取客户端IP
  const clientIp = event.requestContext?.sourceIp || event.headers['x-forwarded-for'] || '127.0.0.1';
  
  // 检查频率限制
  if (!checkRateLimit(clientIp)) {
    return {
      statusCode: 429,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-API-Key'
      },
      body: JSON.stringify({
        status: 'error',
        message: '请求过于频繁，请稍后再试',
        data: null
      })
    };
  }
  
  // 处理跨域OPTIONS请求
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-API-Key'
      },
      body: ''
    };
  }
  
  // 验证API Key
  if (!verifyApiKey(event)) {
    return {
      statusCode: 401,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        status: 'error',
        message: 'API Key 无效',
        data: null
      })
    };
  }
  
  try {
    // 解析请求路径和方法
    const path = event.path || '';
    const method = event.httpMethod || event.method || 'GET';
    
    // 解析请求体
    const body = parseBody(event);
    
    let result;
    
    // 根据路径处理不同接口
    if (path.endsWith('/auth/verify') && method === 'POST') {
      result = handleVerify(body);
    } else if (path.endsWith('/auth/generate') && method === 'POST') {
      result = handleGenerate(body);
    } else {
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({
          status: 'error',
          message: '接口不存在',
          data: null
        })
      };
    }
    
    // 返回成功响应
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify(result)
    };
    
  } catch (e) {
    console.error('Server error:', e);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        status: 'error',
        message: `服务器内部错误: ${e.message}`,
        data: null
      })
    };
  }
};
