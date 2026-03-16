# 激活码管理API服务部署指南

## 部署到腾讯云的三种方式

### 方式一：使用腾讯云轻量应用服务器（推荐）

#### 1. 购买轻量应用服务器
- 登录腾讯云控制台，选择「轻量应用服务器」
- 选择合适的配置：建议2核2G以上，系统选择Ubuntu 22.04 LTS
- 设置登录密码或SSH密钥

#### 2. 连接服务器
```bash
# 使用SSH连接
ssh root@your_server_ip
```

#### 3. 安装依赖
```bash
# 更新系统
apt update && apt upgrade -y

# 安装Python 3.11和pip
apt install python3.11 python3.11-pip -y

# 安装git
apt install git -y
```

#### 4. 部署应用
```bash
# 克隆代码（或者上传代码到服务器）
git clone <your_repo_url>
cd activation-service

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建环境变量文件
cp .env.example .env
# 编辑.env文件，修改API_KEY为安全的随机字符串
nano .env
```

#### 5. 启动服务
```bash
# 方式一：直接启动（用于测试）
python main.py

# 方式二：使用systemd管理服务（推荐）
sudo tee /etc/systemd/system/activation-service.service <<EOF
[Unit]
Description=Activation Code Service
After=network.target

[Service]
User=root
WorkingDirectory=/root/activation-service
Environment="PATH=/root/activation-service/venv/bin"
ExecStart=/root/activation-service/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务并设置开机自启
sudo systemctl daemon-reload
sudo systemctl start activation-service
sudo systemctl enable activation-service

# 查看服务状态
sudo systemctl status activation-service
```

#### 6. 配置防火墙
- 在腾讯云控制台的轻量应用服务器页面，找到「防火墙」配置
- 添加规则：允许8000端口的TCP入站流量

### 方式二：使用腾讯云容器服务TKE

#### 1. 创建Docker镜像
```bash
# 构建镜像
docker build -t activation-service:v1 .

# 推送到腾讯云镜像仓库
# 先登录腾讯云容器镜像服务
docker login ccr.ccs.tencentyun.com
# 标记镜像
docker tag activation-service:v1 ccr.ccs.tencentyun.com/your_namespace/activation-service:v1
# 推送镜像
docker push ccr.ccs.tencentyun.com/your_namespace/activation-service:v1
```

#### 2. 创建Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: activation-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: activation-service
  template:
    metadata:
      labels:
        app: activation-service
    spec:
      containers:
      - name: activation-service
        image: ccr.ccs.tencentyun.com/your_namespace/activation-service:v1
        ports:
        - containerPort: 8000
        env:
        - name: API_KEY
          value: "your_secure_api_key_here"
```

#### 3. 创建Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: activation-service-service
spec:
  type: LoadBalancer
  selector:
    app: activation-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

### 方式三：使用腾讯云Serverless云函数SCF

#### 1. 安装Serverless Framework
```bash
npm install -g serverless
```

#### 2. 创建serverless.yml
```yaml
component: scf
name: activation-service
app: activation-app
slsVersion: 3.0

inputs:
  src: ./
  runtime: Python3.11
  region: ap-guangzhou
  handler: index.handler
  events:
    - apigw:
        parameters:
          protocols:
            - https
          environment: release
```

#### 3. 部署
```bash
serverless deploy
```

## 测试服务

### 健康检查
```bash
curl http://your_server_ip:8000/health
```

### 生成激活码
```bash
curl -X POST http://your_server_ip:8000/v1/auth/generate \
  -H "X-API-Key: your_secure_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 30,
    "count": 5,
    "package_type": "premium"
  }'
```

### 验证激活码
```bash
curl -X POST http://your_server_ip:8000/v1/auth/verify \
  -H "X-API-Key: your_secure_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "auth_code": "30_your_generated_code_here",
    "machine_code": "abc123def456",
    "plugin_version": "1.0.0"
  }'
```

## 安全建议

1. **API Key**：务必使用强随机字符串作为API Key，不要使用默认值
2. **HTTPS**：生产环境务必使用HTTPS，可以通过腾讯云SSL证书服务申请免费证书
3. **防火墙**：仅开放必要的端口（80/443/8000）
4. **数据库备份**：定期备份SQLite数据库文件
5. **监控告警**：配置腾讯云监控，设置CPU、内存、磁盘使用率告警