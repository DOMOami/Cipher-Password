# Cipher Password

生成强密码并且实现PC端与移动端互传。生成强密码 → PBKDF2 + AES-256-CTR 加密 → 本地存储 + Gmail 邮件备份 → 手机浏览器解密。

## 工作流程

```
┌─ 发送方 (PC) ──────────────────────────────┐
│                                             │
│  password_generator.py                      │
│  生成密码 → 转为字符集索引                    │
│  → AES-256-CTR 加密 → 存 password.txt        │
│  → 通过 Gmail SMTP 发送邮件                  │
│  → 附件: decrypt.html (混淆加密的HTML解密器)  │
│                                             │
└──────────────┬──────────────────────────────┘
               │  邮件 (Gmail)
               ▼
┌─ 接收方 (手机) ─────────────────────────────┐
│                                             │
│  打开附件 decrypt.html                       │
│  输入解锁口令 → 进入解密页面                  │
│  输入共享口令 + 粘贴密文 → 显示明文密码       │
│                                             │
│  全部运算在浏览器本地完成，不上传服务器        │
│                                             │
└─────────────────────────────────────────────┘
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成配置模板
python password_generator.py
# 首次运行会创建 config.json 模板，按提示填写

# 3. 编辑 config.json
# 详见下方配置说明

# 4. 构建解密器（设置解锁口令，发送邮件前必须执行）
python build_decrypt.py

# 5. 再次运行，生成密码并发送邮件
python password_generator.py
```

## 配置 config.json

```json
{
  "sender_email": "你的邮箱@gmail.com",
  "app_password": "Gmail应用专用密码",
  "recipient_email": "接收密码的邮箱@gmail.com",
  "passphrase": "你和接收者约定的共享口令"
}
```

**Gmail 应用专用密码获取：**
1. 开启 [两步验证](https://myaccount.google.com/security)
2. 前往 [应用专用密码](https://myaccount.google.com/apppasswords)
3. 选择"邮件" → "其他" → 生成 16 位密码（填入时去掉空格）

## 安全设计

| 环节 | 方案 |
|------|------|
| 加密算法 | PBKDF2 (SHA-256, 60万次迭代) → AES-256-CTR |
| 防御性设计 | 错误口令解密同样输出合法密码，无法通过输出格式判断口令对错 |
| 密码发送 | 仅发送密文，明文永不出现在邮件中 |
| decrypt.html | 核心JS经 AES-256-CTR 加密，解锁口令错误无法解密出算法 |
| 本地存储 | password.txt 仅存密文 |
| 浏览器安全 | Web Crypto API，密钥不离开浏览器 |

## 文件结构

```
├── password_generator.py   # 主程序
├── build_decrypt.py        # 混淆版 decrypt.html 构建脚本
├── decrypt.html            # 手机端解密页面 (由 build_decrypt.py 生成)
├── config.json.example     # 配置文件模板
├── requirements.txt        # Python 依赖
└── .gitignore              # 保护敏感文件
```

运行时生成（不上传 GitHub）：
- `config.json` — 邮箱和口令配置
- `password.txt` — 加密存储的密码记录
- `decrypt.html` — 手机端解密页面（由 build_decrypt.py 生成）

## 依赖

- Python 3.8+
- [cryptography](https://cryptography.io/) — PBKDF2, AES-CTR

## 最后的话

这是我的第一个作品，如果有什么错误或者是不好的地方，希望您能指出，谢谢!
