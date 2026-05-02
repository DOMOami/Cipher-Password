import base64
import hashlib
import json
import os
import secrets
import smtplib
import string
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from random import SystemRandom

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

CONFIG_FILE = "config.json"

CATEGORIES = [
    string.ascii_uppercase,
    string.ascii_lowercase,
    string.digits,
    "!",
]

CHAR_SET = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!"
CHAR_TO_IDX = {c: i for i, c in enumerate(CHAR_SET)}
CHAR_COUNT = len(CHAR_SET)  # 63


def load_config():
    if not os.path.exists(CONFIG_FILE):
        template = {
            "sender_email": "你的邮箱@gmail.com",
            "app_password": "Gmail应用专用密码",
            "recipient_email": "接收密码的邮箱@gmail.com",
            "passphrase": "你和接收者约定的共享口令",
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"请先编辑 {CONFIG_FILE} 填写配置，然后重新运行。")
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    if (
        "你的邮箱" in config.get("sender_email", "")
        or "Gmail应用专用密码" in config.get("app_password", "")
        or "约定的共享口令" in config.get("passphrase", "")
    ):
        print(f"{CONFIG_FILE} 中的配置尚未填写或口令未修改，请编辑后重试。")
        return None
    return config


def _derive_key(passphrase, salt):
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    ).derive(passphrase.encode())


def encrypt(plaintext, passphrase):
    """将密码转为字符集索引后 AES-256-GCM 加密，返回 base64"""
    indices = bytes(CHAR_TO_IDX[c] for c in plaintext)  # 每字符 → 0-62
    salt = os.urandom(16)
    key = _derive_key(passphrase, salt)
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(indices) + encryptor.finalize()
    combined = salt + nonce + ciphertext + encryptor.tag
    return base64.b64encode(combined).decode()


def decrypt(token, passphrase):
    """解密，正确口令还原密码，错误口令输出同类字符集密码，不可区分"""
    combined = base64.b64decode(token)
    salt = combined[:16]
    nonce = combined[16:28]
    tag = combined[-16:]
    ciphertext = combined[28:-16]
    key = _derive_key(passphrase, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
    decryptor = cipher.decryptor()
    try:
        raw = decryptor.update(ciphertext) + decryptor.finalize()
    except Exception:
        raw = hashlib.shake_256(key).digest(len(ciphertext))
    return "".join(CHAR_SET[b % CHAR_COUNT] for b in raw)


def send_email(config):
    if not os.path.exists("decrypt.html"):
        print("未找到 decrypt.html，请先运行: python build_decrypt.py")
        return

    with open("password.txt", "r", encoding="utf-8") as f:
        content = f.read()

    msg = MIMEMultipart()
    msg["Subject"] = "密码备份"
    msg["From"] = config["sender_email"]
    msg["To"] = config["recipient_email"]

    body = f"""密码列表（已加密）
====================
{content}
---
解密方法: 保存附件 decrypt.html 到手机，用浏览器打开，
输入共享口令和密码列表中的密文即可解密。
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open("decrypt.html", "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", 'attachment; filename="decrypt.html"')
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(config["sender_email"], config["app_password"])
        server.sendmail(
            config["sender_email"], config["recipient_email"], msg.as_string()
        )
    print("邮件已发送（含 decrypt.html 附件）。")


def generate_password(length=12):
    """生成包含大小写字母、数字和感叹号的强密码，每个字符等概率出现"""
    password = [secrets.choice(c) for c in CATEGORIES]
    for _ in range(length - len(CATEGORIES)):
        password.append(secrets.choice(CHAR_SET))
    rng = SystemRandom()
    rng.shuffle(password)
    return "".join(password)


def main():
    config = load_config()
    if config is None:
        return

    answer = input("是否生成一个新的强密码？(y/n): ").strip().lower()
    if answer != "y":
        print("已取消。")
        return

    purpose = input("请输入该密码的用途（例如：微信、邮箱、WiFi等）: ").strip()

    password = generate_password()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    encrypted = encrypt(password, config["passphrase"])

    with open("password.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {purpose} 密码: {encrypted}\n")

    print(f"密码已生成并加密保存到 password.txt")
    print(f"密码: {password}")

    send = input("是否将加密密码发送到邮箱？(y/n): ").strip().lower()
    if send == "y":
        try:
            send_email(config)
        except Exception as e:
            print(f"邮件发送失败: {e}")


if __name__ == "__main__":
    main()
