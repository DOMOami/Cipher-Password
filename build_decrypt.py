"""
将 decrypt.html 的 JS 逻辑混淆打包：
1. AES-256-CTR 加密核心代码（口令错误则无法解密，源码不可读）
2. 变量名随机化
3. 字符串拆解
4. 注入死代码
5. 最终输出一个锁定的 HTML，需输入解锁口令才能进入
"""
import base64
import os
import secrets
import string

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def rand_name():
    """生成无意义的随机变量名"""
    prefix = secrets.choice(["_", "$", "a", "b", "x", "t", "n", "m", "f", "d"])
    pool = "abcdef0123456789"
    suffix = "".join(secrets.choice(pool) for _ in range(secrets.choice([4, 6, 8])))
    return prefix + suffix


def str_to_charcode_array(s):
    """把字符串拆成 charCode 数组，eg: String.fromCharCode(65,66,67)"""
    codes = ",".join(str(ord(c)) for c in s)
    return f"String.fromCharCode({codes})"


# ============================================================
# 核心解密 JS（变量名已被随机化，字符串已拆解）
# ============================================================
def build_core_js():
    _a = rand_name()  # b64ToBytes
    _b = rand_name()   # bytesToChars (CHAR_SET[b % 63])
    _cs = rand_name()  # charSet variable
    _c = rand_name()  # deriveKey
    _d = rand_name()  # decrypt
    _e = rand_name()  # escapeHtml
    _f = rand_name()  # copyPassword
    _g = rand_name()  # TextEncoder
    _h = rand_name()  # importKey
    _i = rand_name()  # deriveKey (subtle)
    _j = rand_name()  # decrypt (subtle)
    _k = rand_name()  # result element
    _l = rand_name()  # passphrase value
    _m = rand_name()  # token value
    _n = rand_name()  # combined bytes
    _o = rand_name()  # salt
    _p = rand_name()  # nonce
    _q = rand_name()  # ciphertext
    _r = rand_name()  # key
    _s = rand_name()  # plaintext
    _t = rand_name()  # password output

    charSet = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!"
    code = f"""
var {_cs}={str_to_charcode_array(charSet)};
var {_a}=function(b64){{return Uint8Array.from(atob(b64),function(c){{return c.charCodeAt(0)}})}};
var {_b}=function(b){{var s={_cs};return Array.from(b,function(v){{return s[v%{len(charSet)}]}}).join({str_to_charcode_array("")})}};
async function {_c}(pw,salt){{
    var enc=new {str_to_charcode_array("TextEncoder")}()[{str_to_charcode_array("encode")}](pw);
    var km=await crypto.subtle[{str_to_charcode_array("importKey")}]({str_to_charcode_array("raw")},enc,{str_to_charcode_array("PBKDF2")},false,[{str_to_charcode_array("deriveKey")}]);
    return crypto.subtle[{str_to_charcode_array("deriveKey")}]({{name:{str_to_charcode_array("PBKDF2")},salt:salt,iterations:600000,hash:{str_to_charcode_array("SHA-256")}}},km,{{name:{str_to_charcode_array("AES-CTR")},length:256}},false,[{str_to_charcode_array("decrypt")}]);
}}
async function {_d}(){{
    var r=document[{str_to_charcode_array("getElementById")}]({str_to_charcode_array("result")});
    r.className={str_to_charcode_array("result")};r.innerHTML={str_to_charcode_array("")};
    var pw=document[{str_to_charcode_array("getElementById")}]({str_to_charcode_array("passphrase")}).value;
    var tok=document[{str_to_charcode_array("getElementById")}]({str_to_charcode_array("token")}).value.trim();
    if(!pw||!tok){{return}}
    var comb;try{{comb={_a}(tok)}}catch(e){{return}}
    var salt=comb.slice(0,16);
    var nonce=comb.slice(16,32);
    var ct=comb.slice(32);
    var key=await {_c}(pw,salt);
    var pt=await crypto.subtle[{str_to_charcode_array("decrypt")}]({{name:{str_to_charcode_array("AES-CTR")},counter:nonce,length:128}},key,ct);
    var out={_b}(new Uint8Array(pt));
    r.className={str_to_charcode_array("result show")};
    r.innerHTML={str_to_charcode_array("<div class='password'>")}+{_e}(out)+{str_to_charcode_array("</div><button class='copy-btn' onclick='")}+{_f}+{str_to_charcode_array("(")}+{str_to_charcode_array("'")}+{_e}(out).replace(/'/g,{str_to_charcode_array("\\'")})+{str_to_charcode_array("'")}+{str_to_charcode_array(")")}+{str_to_charcode_array("'>复制密码</button>")};
}}
function {_e}(s){{return s.replace(/&/g,{str_to_charcode_array("&amp;")}).replace(/</g,{str_to_charcode_array("&lt;")}).replace(/>/g,{str_to_charcode_array("&gt;")})}}
function {_f}(p){{navigator.clipboard.writeText(p).then(function(){{var b=event.target;b.textContent={str_to_charcode_array("已复制")};setTimeout(function(){{b.textContent={str_to_charcode_array("复制密码")}}},2000)}})}}
window.{_d}={_d};
"""
    return code


# ============================================================
# 死代码注入
# ============================================================
def build_dead_code():
    """生成一堆看起来在做事但其实只是耗时的无用代码"""
    snippets = []
    for _ in range(secrets.choice([3, 5])):
        name = rand_name()
        arr = [secrets.randbelow(0xFFFF) for _ in range(secrets.choice([8, 16]))]
        calc = " ^ ".join(str(x) for x in arr) + " ^ 0x" + secrets.token_hex(2)
        snippets.append(f"var {name}=({calc});")
    # 再加一个无用的循环
    snippets.append(f"for(var {rand_name()}=0;{rand_name()}<{secrets.choice([100,200,500])};{rand_name()}++){{var {rand_name()}=Math.random()}};")
    return "\n".join(snippets)


# ============================================================
# 构建最终 HTML（核心 JS 用解锁口令 AES-256-CTR 加密）
# ============================================================
def build_html(unlock_passphrase: str):
    core_js = build_core_js()
    dead_js = build_dead_code()
    inner_js = (dead_js + "\n" + core_js).encode()

    # 用解锁口令加密核心 JS
    salt = os.urandom(16)
    key = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600_000,
    ).derive(unlock_passphrase.encode())
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    encryptor = cipher.encryptor()
    ct = encryptor.update(inner_js) + encryptor.finalize()
    encoded = base64.b64encode(salt + nonce + ct).decode()

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>.</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f5f5;display:flex;justify-content:center;padding:16px;min-height:100vh}}
.container{{max-width:420px;width:100%}}
h1{{text-align:center;font-size:1.4em;margin:16px 0 24px;color:#333}}
.card{{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.1);margin-bottom:12px}}
label{{display:block;font-size:.85em;color:#666;margin-bottom:6px;font-weight:500}}
input,textarea{{width:100%;padding:10px 12px;border:1.5px solid #ddd;border-radius:8px;font-size:15px;outline:none;transition:border-color .2s;-webkit-appearance:none}}
input:focus,textarea:focus{{border-color:#4a90d9}}
textarea{{height:90px;resize:vertical;font-family:monospace;font-size:13px}}
button{{width:100%;padding:12px;background:#4a90d9;color:#fff;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;margin-top:16px;transition:background .2s}}
button:active{{background:#3a7bc8}}
.result{{margin-top:16px;padding:14px;border-radius:8px;text-align:center;display:none}}
.result.show{{display:block;background:#e8f5e9}}
.result .password{{font-size:1.5em;font-weight:700;letter-spacing:2px;margin-top:6px;word-break:break-all}}
.result .copy-btn{{margin-top:10px;padding:8px 20px;font-size:14px;width:auto}}
.info{{font-size:.8em;color:#999;text-align:center;margin-top:24px}}
.hidden{{display:none!important}}
</style>
</head>
<body>
<div id="gate" class="container">
    <h1>.</h1>
    <div class="card">
        <label for="unlock">解锁口令</label>
        <input id="unlock" type="password" placeholder="输入解锁口令" autocomplete="off">
    </div>
    <button onclick="tryUnlock()">解锁</button>
    <div id="gateMsg" style="text-align:center;margin-top:12px;color:#c62828;display:none"></div>
</div>
<div id="app" class="container hidden">
    <h1>.</h1>
    <div class="card">
        <label for="passphrase">共享口令</label>
        <input id="passphrase" type="password" placeholder="输入和发送者约定的共享口令" autocomplete="off">
    </div>
    <div class="card">
        <label for="token">加密密码</label>
        <textarea id="token" placeholder="粘贴邮件中的加密密码"></textarea>
    </div>
    <button onclick="decrypt()">解密</button>
    <div id="result" class="result"></div>
</div>
<div class="info">本地运算，不上传服务器</div>

<script>
var _b=atob("{encoded}");
async function tryUnlock(){{
    var pw=document.getElementById("unlock").value;
    var raw=new Uint8Array(_b.length);for(var i=0;i<_b.length;i++)raw[i]=_b.charCodeAt(i);
    var salt=raw.slice(0,16);
    var nonce=raw.slice(16,32);
    var ct=raw.slice(32);
    try{{
        var enc=new TextEncoder().encode(pw);
        var km=await crypto.subtle.importKey("raw",enc,"PBKDF2",false,["deriveKey"]);
        var key=await crypto.subtle.deriveKey({{name:"PBKDF2",salt:salt,iterations:600000,hash:"SHA-256"}},km,{{name:"AES-CTR",length:256}},false,["decrypt"]);
        var pt=await crypto.subtle.decrypt({{name:"AES-CTR",counter:nonce,length:128}},key,ct);
        var js=new TextDecoder().decode(pt);
        new Function(js)();
        document.getElementById("gate").classList.add("hidden");
        document.getElementById("app").classList.remove("hidden");
    }}catch(e){{
        var m=document.getElementById("gateMsg");
        m.style.display="block";
        m.textContent=String.fromCharCode(38169,35823,30340,35299,38145,21475,20196);
        setTimeout(function(){{m.style.display="none"}},2000);
    }}
}}
</script>
</body>
</html>"""
    return html


if __name__ == "__main__":
    unlock = input("设置 HTML 解锁口令: ").strip()
    if not unlock:
        print("口令不能为空")
        exit(1)
    html = build_html(unlock)
    with open("decrypt.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"decrypt.html 已生成（解锁口令: {unlock}）")
    print("核心 JS 已 AES-256-CTR 加密，无解锁口令无法查看算法。")
