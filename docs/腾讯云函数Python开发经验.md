# 腾讯云函数 Python 开发踩坑总结

## 1. 版本兼容性

### 类型语法
- Python 3.9 不支持 `dict | None` 这种 PEP 604 联合类型语法
- 兼容性写法：使用 `typing.Optional[dict]` 或者直接去掉类型提示（云函数运行不需要类型提示）
- 如果要兼容 3.9，**不要** 使用 3.10+ 新增的类型语法

### Datetime ISO 格式解析
- Python 3.9 `datetime.fromisoformat()` 不支持以 `Z` 结尾的 UTC 格式（`2026-03-16T10:00:00Z`）
- 解决方法：手动去掉末尾的 `Z` 再解析：
  ```python
  if expiry_str.endswith('Z'):
      expiry_str = expiry_str[:-1]
  expiry = datetime.fromisoformat(expiry_str)
  ```

### 时区比较
- `datetime.utcnow()` 返回的是 *offset-naive* 不带时区信息
- `datetime.fromisoformat()` 如果解析出带时区信息，会返回 *offset-aware*
- naive 和 aware 不能直接比较，会报错 `can't compare offset-naive and offset-aware datetimes`
- 解决方法：全程使用 naive UTC 时间，存储去掉 `Z`，直接用 `datetime.utcnow()` 比较

## 2. 部署打包

### 入口文件
- 压缩包根目录必须直接放入口文件，不能嵌套一层目录
- 错误：`tencent-cloud-scf-activation-sqlite/index.py` → 云函数找不到入口文件
- 正确：直接打包 `index.py` 在zip根目录

### 依赖
- Python 标准库（如 `sqlite3`、`json`、`hashlib` 等）不需要写到 `requirements.txt`
- 如果不需要第三方依赖，`requirements.txt` 可以留空或者只放注释
- 云函数会自动安装 `requirements.txt` 中的依赖

## 3. 配置要点

### 日志服务
- 默认会自动创建日志服务，会产生费用
- 创建函数时**一定要取消勾选**启用日志
- 如果已经创建，可以通过更新配置清空 `ClsLogsetId` 和 `ClsTopicId` 关闭：
  ```bash
  tccli scf UpdateFunctionConfiguration \
    --FunctionName xxx \
    --ClsLogsetId "" \
    --ClsTopicId ""
  ```

### 环境变量
- 敏感信息（API Key、密钥）一定要通过环境变量传入，不要硬编码到代码里
- 腾讯云控制台 → 云函数 → 配置 → 环境变量 添加

### 区域
- 需要明确指定 `--region ap-beijing` 在北京区域创建
- tccli 默认区域不一定是北京，命令行要指定

## 4. 存储

### SQLite 注意
- `/tmp` 是临时存储，云函数实例释放后数据会丢失
- 需要持久化 → 挂载腾讯云 CFS 文件存储，把 SQLite 文件放到 CFS 挂载路径
- 轻度使用、数据可接受丢失 → `/tmp` 足够用，免费

### 降级设计
- 数据库连接失败时，降级到内存存储，保证服务可用不宕机
- 即使数据库出问题，接口还是能正常工作

## 5. 测试

### 本地测试
- 写完代码本地先跑完整流程测试，再上传云函数
- 可以写自动化测试脚本从头到尾走一遍：生成 → 激活 → 重复验证 → 多设备测试
- 避免本地能跑，云上不能跑的情况

### 线上测试
- 使用完整单行curl命令，换行反斜杠容易出问题（zsh对反斜杠后面有空格要求严格）
- 报错 `Expecting value: line 1 column 1 (char 0)` 一般是请求体JSON格式错了，不是服务端错
- 报错 `Malformed input to a URL function` 一般是命令换行语法错了，不是URL错了

## 6. 调试

- 关闭日志后没法看日志，所以本地测试一定要充分
- 通过API返回详细错误信息 `message` 帮助定位问题
- 完整错误信息返回来，调试更快

## 7. HTTP请求头陷阱

### 请求头大小写
- 不同客户端、curl写法不同，可能传 `X-API-Key` 也可能传 `x-api-key`
- 腾讯云函数会**保留原始大小写**，代码不能写死只取小写 `x-api-key`
- 解决方法：不区分大小写匹配：
  ```python
  # 兼容大小写不同的header名称
  request_api_key = None
  for header_name, header_value in event.get("headers", {}).items():
      if header_name.lower() == "x-api-key":
          request_api_key = header_value
          break
  ```

### tccli 命令行参数
- 不同版本tccli参数格式不同，有的要驼峰 `--FunctionName`，有的要小写 `--function-name`
- 参数顺序也有讲究，先 `tccli scf <action>` 再跟参数
- 遇到参数错误多试几种写法，或者看 `tccli scf help` 和 `tccli scf <action> help`

### 上传代码包
- `UpdateFunctionCode` 需要把zip文件base64编码后直接传参数，不能用文件URL
- 正确传参：`--ZipFile "$(base64 -w0 /path/to/deployment.zip)"`

## 8. 最终 Checklist 部署前检查

- [ ] 运行环境选择正确（Python 3.9）
- [ ] 关闭日志服务（省钱）
- [ ] 入口文件在zip根目录
- [ ] 处理好了datetime兼容性问题
- [ ] 请求头兼容大小写（`X-API-Key` / `x-api-key`）
- [ ] 环境变量配置正确
- [ ] 本地完整流程测试通过
- [ ] 线上测试生成和验证都正常

---

记住这些坑，下次开发腾讯云函数就能少踩雷，快速交付 ✅
