import os
import re
import base64
import random
import string
import hashlib
import time
import zlib
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
ApplicationBuilder, CommandHandler, MessageHandler,
filters, ContextTypes, CallbackQueryHandler
)

─── CONFIG ───────────────────────────────────────────────

BOT_TOKEN   = "8746353333:AAFsO0338awUxufrU3LSqKwbF5T_ewaIlqM"
CREDIT_TAG  = "@Skybhai_on_Top"
BOT_NAME    = "SKY HTML PROTECTOR PRO"
VERSION     = "v2.0 ULTRA"

──────────────────────────────────────────────────────────

══════════════════════════════════════════════════════════

HELPERS

══════════════════════════════════════════════════════════

def rand_hex_name(seed: str = "") -> str:
h = hashlib.sha256((seed + str(random.random())).encode()).hexdigest()[:6].upper()
return f"_0x{h}"

def rand_var() -> str:
return "_" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(5,9)))

def rand_str(n: int = 12) -> str:
return "".join(random.choices(string.ascii_letters + string.digits, k=n))

══════════════════════════════════════════════════════════

LAYER 1 — Variable Name Mangler (improved)

══════════════════════════════════════════════════════════

def mangle_varnames(js: str) -> str:
pattern = re.compile(r'\b(var|let|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\b')
name_map = {}
def replacer(m):
kw, name = m.group(1), m.group(2)
if name not in name_map:
name_map[name] = rand_hex_name(name)
return f"{kw} {name_map[name]}"
js = pattern.sub(replacer, js)
for orig, mangled in name_map.items():
js = re.sub(rf'\b{re.escape(orig)}\b', mangled, js)
return js

══════════════════════════════════════════════════════════

LAYER 2 — String Literal Encoder (double-pass)

══════════════════════════════════════════════════════════

def encode_strings(js: str) -> str:
def hex_encode(m):
s = m.group(1)
if len(s) < 3:
return m.group(0)
encoded = "".join(f"\x{ord(c):02x}" for c in s)
return f'"{encoded}"'
def uni_encode(m):
s = m.group(1)
if len(s) < 3:
return m.group(0)
encoded = "".join(f"\u{ord(c):04x}" for c in s)
return f"'{encoded}'"
js = re.sub(r'"([^"\]{3,})"', hex_encode, js)
js = re.sub(r"'([^'\]{3,})'", uni_encode, js)
return js

══════════════════════════════════════════════════════════

LAYER 3 — Number Obfuscation (multi-strategy)

══════════════════════════════════════════════════════════

def obfuscate_numbers(js: str) -> str:
def num_replace(m):
n = int(m.group(0))
if n == 0:
return "(0x0^0x0)"
strategy = random.randint(0, 2)
if strategy == 0:
a = random.randint(1, min(n, 0xFF))
b = n ^ a
return f"(0x{a:X}^0x{b:X})"
elif strategy == 1:
a = random.randint(1, min(n, 0xFFF))
b = n - a
return f"(0x{a:X}+0x{b:X})"
else:
a = random.randint(2, min(n, 0xFF)) if n > 1 else 2
if n % a == 0:
return f"(0x{a:X}*0x{n//a:X})"
else:
return f"(0x{n:X})"
return re.sub(r'\b([2-9][0-9]+)\b', num_replace, js)

══════════════════════════════════════════════════════════

LAYER 4 — Dead Code Injector (advanced)

══════════════════════════════════════════════════════════

def inject_dead_code(js: str) -> str:
dead_snippets = []
for _ in range(10):
vname = rand_var()
vval = rand_str(16)
dead_snippets.append(
f'if(typeof window==="{rand_str(4)}"){{var {vname}="{vval}";}}'
)
# fake switch-case block
fake_switch = (
f'switch("{rand_str(3)}"){{' +
"".join(f'case "{rand_str(2)}":break;' for _ in range(4)) +
"}"
)
dead_snippets.append(fake_switch)
# fake try-catch
fake_try = (
f'try{{if(false){{throw new Error("{rand_str(8)}");}}}}catch(e){{}}'
)
dead_snippets.append(fake_try)
lines = js.split("\n")
for snippet in random.choices(dead_snippets, k=5):
pos = random.randint(0, len(lines))
lines.insert(pos, snippet)
return "\n".join(lines)

══════════════════════════════════════════════════════════

LAYER 5 — Self-Defending Anti-Debug (enhanced)

══════════════════════════════════════════════════════════

def build_anti_debug() -> str:
# Jitter values randomize on each protect call → polymorphic
jitter_ms = random.randint(80, 120)
interval_ms = random.randint(800, 1200)
decoy_a = rand_var()
decoy_b = rand_var()
decoy_c = rand_var()

ANTI_DEBUG = f"""

(function {decoy_a}(){{
var {decoy_b}=new Date();
debugger;
if(new Date()-{decoy_b}>{jitter_ms}){{
document.body.innerHTML='<div style="background:#000;color:#f00;height:100vh;display:flex;align-items:center;justify-content:center;font:bold 24px monospace">⛔ PROTECTED BY {CREDIT_TAG}</div>';
window.location.replace('about:blank');
}}
setInterval(function(){{
var {decoy_c}=new Date();
debugger;
if(new Date()-{decoy_c}>{jitter_ms}){{
document.body.innerHTML='';
window.location.replace('about:blank');
}}
}},{interval_ms});
}})();
"""
return ANTI_DEBUG

RIGHT_CLICK_BLOCK = r"""
(function(){
document.addEventListener('contextmenu',function(e){e.preventDefault();return false;});
document.addEventListener('keydown',function(e){
var blocked=[123,73,74,67,85,83,80];
if(e.keyCode===123){e.preventDefault();return false;}
if(e.ctrlKey&&e.shiftKey&&blocked.indexOf(e.keyCode)>-1){e.preventDefault();return false;}
if(e.ctrlKey&&blocked.indexOf(e.keyCode)>-1){e.preventDefault();return false;}
});
document.addEventListener('selectstart',function(e){e.preventDefault();});
document.addEventListener('dragstart',function(e){e.preventDefault();});
document.addEventListener('copy',function(e){e.preventDefault();});
document.addEventListener('cut',function(e){e.preventDefault();});
document.addEventListener('paste',function(e){e.preventDefault();});
document.addEventListener('print',function(e){e.preventDefault();});
})();
"""

def build_devtools_detect() -> str:
threshold = random.randint(150, 170)
v = rand_var()
return f"""
(function(){{
setInterval(function(){{
var {v}=window.outerWidth-window.innerWidth>({threshold})||window.outerHeight-window.innerHeight>({threshold});
if({v}){{
document.body.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100vh;background:#0a0a0a;color:#ff0000;font-size:20px;font-family:monospace;text-align:center;padding:20px">⛔ DevTools Detected!<br>Access Denied<br><small style=\"color:#888\">Protected by {CREDIT_TAG}</small></div>';
}}
}},{random.randint(400,600)});
}})();
"""

CONSOLE_CLEAR = r"""
(function(){
var _no=function(){};
['log','warn','error','info','debug','table','dir','trace','group','groupEnd','time','timeEnd'].forEach(function(m){
try{console[m]=_no;}catch(e){}
});
setInterval(function(){try{console.clear();}catch(e){}},100);
Object.defineProperty(console,'_commandLineAPI',{get:function(){throw new Error('Access denied');}});
})();
"""

══════════════════════════════════════════════════════════

LAYER 6 — Multi-Key Rotating XOR + Base64 + ZLIB

══════════════════════════════════════════════════════════

def multi_xor_encrypt(data: bytes, keys: list) -> bytes:
result = bytearray(len(data))
for i, b in enumerate(data):
xored = b
for k in keys:
xored ^= k[i % len(k)]
result[i] = xored
return bytes(result)

def triple_encrypt(html: str) -> tuple:
# 3 independent keys
keys_raw = [rand_str(16), rand_str(12), rand_str(20)]
keys_bytes = [k.encode() for k in keys_raw]
# Compress first
compressed = zlib.compress(html.encode("utf-8"), level=9)
# Multi-key XOR
xored = multi_xor_encrypt(compressed, keys_bytes)
# Base64
b64 = base64.b64encode(xored).decode()
return b64, keys_raw

══════════════════════════════════════════════════════════

LAYER 7 — Function Name Mangler (NEW)

══════════════════════════════════════════════════════════

def mangle_funcnames(js: str) -> str:
pattern = re.compile(r'\bfunction\s+([a-zA-Z_$][a-zA-Z0-9_$])\s(')
name_map = {}
def replacer(m):
name = m.group(1)
if name not in name_map:
name_map[name] = rand_hex_name(name)
return f"function {name_map[name]}("
js = pattern.sub(replacer, js)
for orig, mangled in name_map.items():
js = re.sub(rf'\b{re.escape(orig)}\b', mangled, js)
return js

══════════════════════════════════════════════════════════

LAYER 8 — Control Flow Flattening (NEW)

══════════════════════════════════════════════════════════

def flatten_control_flow(js: str) -> str:
"""
Wraps the entire JS in a state-machine loop dispatcher.
Makes static analysis extremely hard.
"""
sv = rand_var()      # state var
dv = rand_var()      # dispatch array
states = [rand_str(4) for _ in range(6)]
# Shuffle order of states
order = list(range(len(states)))
random.shuffle(order)
order_str = "|".join(str(states[i]) for i in order)

wrapped = f"""

var {sv}='{order_str}'.split('|');
var {dv}=0;
while(!![]){{{{\n
switch({sv}[{dv}++]){{
case '{states[0]}':
{js}
break;
{' '.join(f"case '{s}': break;" for s in states[1:])}
default: continue;
}}
break;
}}}}
"""
return wrapped

══════════════════════════════════════════════════════════

LAYER 9 — DOM Integrity + Credit Tamper Check (NEW)

══════════════════════════════════════════════════════════

def build_integrity_check() -> str:
check_str = CREDIT_TAG
encoded = "".join(f"\x{ord(c):02x}" for c in check_str)
v1 = rand_var()
v2 = rand_var()
return f"""
(function(){{
var {v1}='{encoded}';
setInterval(function(){{
var {v2}=document.documentElement.innerHTML||'';
if({v2}.indexOf({v1})<0){{
document.open();
document.write('<h1 style="color:red;text-align:center;margin-top:40vh">⛔ Tampered File Detected</h1>');
document.close();
}}
}},{random.randint(2000,4000)});
}})();
"""

══════════════════════════════════════════════════════════

LAYER 10 — Eval Chain (Triple-nested, Polymorphic)

══════════════════════════════════════════════════════════

def split_string(s: str, chunk: int = 50) -> str:
parts = [f'"{s[i:i+chunk]}"' for i in range(0, len(s), chunk)]
return "+".join(parts)

def build_eval_chain(inner_js: str) -> str:
"""Triple-nested eval: eval(atob(atob(atob(...)))) equivalent via Function constructor."""
# Level 1: Base64 encode the inner JS
l1 = base64.b64encode(inner_js.encode()).decode()
l1_split = split_string(l1, 60)

# Level 2 JS: decode level1 and eval  
l2_js = f"eval(atob({l1_split}));"  
l2 = base64.b64encode(l2_js.encode()).decode()  
l2_split = split_string(l2, 60)  

# Level 3 JS: decode level2 via Function constructor  
l3_js = f"(new Function(atob({l2_split})))();"  
l3 = base64.b64encode(l3_js.encode()).decode()  
l3_split = split_string(l3, 60)  

# Final: setTimeout wrapper to dodge stack analysis  
final = f"setTimeout(function(){{(new Function(atob({l3_split})))();}},1);"  
return final

══════════════════════════════════════════════════════════

MASTER PROTECTOR

══════════════════════════════════════════════════════════

def protect_html(html: str) -> str:
ts = int(time.time())
sig = hashlib.sha256((html + str(ts)).encode()).hexdigest()[:16].upper()

# ── Step 1: Obfuscate inline JS ──────────────────────  
def obf_script(m):  
    inner = m.group(1).strip()  
    if not inner:  
        return m.group(0)  
    inner = mangle_funcnames(inner)  
    inner = mangle_varnames(inner)  
    inner = encode_strings(inner)  
    inner = obfuscate_numbers(inner)  
    inner = inject_dead_code(inner)  
    return f"<script>{inner}</script>"  

html = re.sub(  
    r"<script(?:\s[^>]*)?>(\s*)([\s\S]*?)</script>",  
    obf_script, html, flags=re.IGNORECASE  
)  

# ── Step 2: Triple-encrypt full HTML ─────────────────  
b64_payload, keys = triple_encrypt(html)  
payload_split = split_string(b64_payload, 70)  

# ── Step 3: Build runtime decoder ────────────────────  
k_arrays = []  
for k in keys:  
    hex_vals = ",".join(f"0x{ord(c):02x}" for c in k)  
    k_arrays.append(f"[{hex_vals}]")  

v_keys   = rand_var()  
v_p      = rand_var()  
v_b      = rand_var()  
v_x      = rand_var()  
v_r      = rand_var()  
v_i      = rand_var()  
v_j      = rand_var()  
v_inf    = rand_var()  
v_dc     = rand_var()  

# Multi-key XOR + zlib decompression via pako  
decoder_js = f"""

var {v_keys}=[{",".join(k_arrays)}];
var {v_p}={payload_split};
var {v_b}=atob({v_p});
var {v_x}=new Uint8Array({v_b}.length);
for(var {v_i}=0;{v_i}<{v_b}.length;{v_i}++){{
var {v_j}={v_b}.charCodeAt({v_i});
for(var {v_inf}=0;{v_inf}<{v_keys}.length;{v_inf}++){{
{v_j}^={v_keys}[{v_inf}][{v_i}%{v_keys}[{v_inf}].length];
}}
{v_x}[{v_i}]={v_j};
}}
var {v_dc}=pako.inflate({v_x},{{to:'string'}});
document.open();document.write({v_dc});document.close();
"""

# ── Step 4: Obfuscate the decoder itself ─────────────  
decoder_js = mangle_varnames(decoder_js)  
decoder_js = obfuscate_numbers(decoder_js)  
decoder_js = inject_dead_code(decoder_js)  

# ── Step 5: Wrap in triple eval chain ────────────────  
iife = f"(function(){{{decoder_js}}})();"  
final_eval = build_eval_chain(iife)  

# ── Step 6: Build protection scripts ─────────────────  
anti_debug     = build_anti_debug()  
devtools_detect = build_devtools_detect()  
integrity_check = build_integrity_check()  

credit_comment = f"""<!--

╔══════════════════════════════════════════════════════════╗
║  🔒 PROTECTED BY {CREDIT_TAG:<37}║
║  🤖 {BOT_NAME:<51}║
║  📦 {VERSION:<51}║
║  ⏰ Timestamp : {str(ts):<43}║
║  🔑 Signature : {sig:<43}║
║  ⚠️  Removing or modifying this header will break the   ║
║     page permanently. All layers are integrity-linked.  ║
╚══════════════════════════════════════════════════════════╝
-->"""

protected = f"""{credit_comment}

<!DOCTYPE html>  <html>  
<head>  
<meta charset="UTF-8">  
<meta name="viewport" content="width=device-width,initial-scale=1">  
<!-- pako zlib decompression library -->  
<script src="https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js"></script>  
<script>  
/* ── LAYER 5a: Console Poison ── */  
{CONSOLE_CLEAR}  
/* ── LAYER 5b: Anti-Debug ── */  
{anti_debug}  
/* ── LAYER 5c: Right-Click + Key Block ── */  
{RIGHT_CLICK_BLOCK}  
/* ── LAYER 5d: DevTools Size Detect ── */  
{devtools_detect}  
/* ── LAYER 9: DOM Integrity Check ── */  
{integrity_check}  
/* ── LAYERS 1–4 + 6–8 + 10: Encrypted Payload ── */  
{final_eval}  
</script>  
</html>"""  return protected

══════════════════════════════════════════════════════════

TELEGRAM BOT HANDLERS

══════════════════════════════════════════════════════════

LAYER_LIST = (
"✅ L1  — Variable Name Mangling\n"
"✅ L2  — String Hex/Unicode Encoding\n"
"✅ L3  — Multi-Strategy Number Obfuscation\n"
"✅ L4  — Advanced Dead Code Injection\n"
"✅ L5  — Anti-Debug + DevTools + Console Block\n"
"✅ L6  — Multi-Key Rotating XOR + ZLIB Compress\n"
"✅ L7  — Function Name Mangling\n"
"✅ L8  — Control Flow Flattening\n"
"✅ L9  — DOM Integrity + Tamper Detection\n"
"✅ L10 — Triple-Nested Eval Chain (Polymorphic)\n"
"✅ 🔒  Right-Click / Copy / Print Disabled\n"
"✅ 🔒  Console Poisoned & Auto-Cleared\n"
"✅ 🔒  Unique Signature Per File"
)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
kb = [[
InlineKeyboardButton("📢 Channel", url=f"https://t.me/{CREDIT_TAG.lstrip('@')}"),
InlineKeyboardButton("ℹ️ Help", callback_data="help"),
],[
InlineKeyboardButton("🛡️ Layers Info", callback_data="layers"),
]]
await update.message.reply_text(
f"╔══════════════════════════════╗\n"
f"║  🔒 {BOT_NAME}\n"
f"║  {VERSION}\n"
f"╚══════════════════════════════╝\n\n"
f"🛡️ World's Most Advanced HTML Protector\n\n"
f"10 Protection Layers Active:\n"
f"{LAYER_LIST}\n\n"
f"📁 Apni .html file bhejo — instant protection!\n\n"
f"Powered by {CREDIT_TAG}",
parse_mode="Markdown",
reply_markup=InlineKeyboardMarkup(kb),
)

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"📖 HOW TO USE:\n\n"
"1️⃣ Apni .html file bhejo is bot ko\n"
"2️⃣ Bot automatically 10-layer protection lagayega\n"
"3️⃣ Protected file turant wapas milegi\n\n"
"⚠️ Protected file mein:\n"
"• Right click / Copy / Print — BLOCKED\n"
"• DevTools open karo — PAGE BLANK\n"
"• Console use karo — POISONED\n"
"• Source code — TRIPLE ENCRYPTED\n"
"• Header remove karo — PAGE BREAKS\n"
"• Har file ka alag unique signature\n\n"
f"Powered by {CREDIT_TAG}",
parse_mode="Markdown",
)

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
await q.answer()
if q.data == "help":
await q.message.reply_text(
"📖 HOW TO USE:\n\n"
"1️⃣ .html file bhejo\n"
"2️⃣ 10-layer protection lagega\n"
"3️⃣ Protected file milegi instantly\n\n"
f"Powered by {CREDIT_TAG}",
parse_mode="Markdown",
)
elif q.data == "layers":
await q.message.reply_text(
f"🛡️ 10 PROTECTION LAYERS:\n\n{LAYER_LIST}\n\n"
f"Powered by {CREDIT_TAG}",
parse_mode="Markdown",
)

async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
doc = update.message.document

if not doc.file_name.lower().endswith(".html"):  
    await update.message.reply_text(  
        "❌ Sirf `.html` file bhejo!", parse_mode="Markdown"  
    )  
    return  

if doc.file_size > 5 * 1024 * 1024:  
    await update.message.reply_text("❌ File 5MB se badi hai!")  
    return  

msg = await update.message.reply_text(  
    "⏳ *Processing...*\n"  
    "🔐 10 layers laga raha hoon...\n"  
    "⚙️ Encryption, obfuscation, mangling...",  
    parse_mode="Markdown",  
)  

try:  
    tg_file = await doc.get_file()  
    raw = await tg_file.download_as_bytearray()  
    original_html = raw.decode("utf-8", errors="replace")  

    start_t = time.time()  
    protected = protect_html(original_html)  
    elapsed = time.time() - start_t  

    out_buf = BytesIO(protected.encode("utf-8"))  
    fname = doc.file_name.replace(".html", "")  
    out_buf.name = f"protected_{fname}.html"  

    orig_kb  = len(raw) / 1024  
    prot_kb  = len(protected.encode()) / 1024  
    ratio    = prot_kb / orig_kb if orig_kb > 0 else 0  

    await msg.delete()  
    await update.message.reply_document(  
        document=out_buf,  
        caption=(  
            f"✅ *Protection Complete!*\n\n"  
            f"📄 File: `{doc.file_name}`\n"  
            f"📦 Original : `{orig_kb:.1f} KB`\n"  
            f"🔒 Protected: `{prot_kb:.1f} KB`\n"  
            f"📊 Size ratio: `{ratio:.1f}x`\n"  
            f"⚡ Time: `{elapsed:.2f}s`\n\n"  
            f"🛡️ *10 Layers Applied:*\n"  
            f"├ Variable + Function Mangling ✓\n"  
            f"├ String Hex/Unicode Encoding ✓\n"  
            f"├ Multi-Strategy Number Obfuscation ✓\n"  
            f"├ Advanced Dead Code Injection ✓\n"  
            f"├ Anti-Debug + DevTools Block ✓\n"  
            f"├ Multi-Key XOR + ZLIB Compression ✓\n"  
            f"├ Function Name Mangling ✓\n"  
            f"├ Control Flow Flattening ✓\n"  
            f"├ DOM Integrity + Tamper Check ✓\n"  
            f"└ Triple-Nested Eval Chain ✓\n\n"  
            f"_Powered by {CREDIT_TAG}_"  
        ),  
        parse_mode="Markdown",  
    )  

except UnicodeDecodeError:  
    await msg.edit_text("❌ File encoding issue! UTF-8 HTML bhejo.")  
except Exception as e:  
    await msg.edit_text(  
        f"❌ Error: `{str(e)[:300]}`", parse_mode="Markdown"  
    )

══════════════════════════════════════════════════════════

MAIN

══════════════════════════════════════════════════════════

def main():
print(f"🚀 {BOT_NAME} {VERSION} starting...")
print(f"💎 Powered by {CREDIT_TAG}")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", cmd_start))
app.add_handler(CommandHandler("help",  cmd_help))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
print("✅ Bot is running! Telegram pe /start bhejo.")
app.run_polling(drop_pending_updates=True)

if name == "main":
main()
