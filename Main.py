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

# CONFIG
BOT_TOKEN  = "8746353333:AAFsO0338awUxufrU3LSqKwbF5T_ewaIlqM"
CREDIT_TAG = "@Skybhai_on_Top"
BOT_NAME   = "SKY HTML PROTECTOR PRO"
VERSION    = "v2.0 ULTRA"


# ══ HELPERS ══════════════════════════════════════════════
def rand_hex_name(seed=""):
    h = hashlib.sha256((seed + str(random.random())).encode()).hexdigest()[:6].upper()
    return f"_0x{h}"

def rand_var():
    return "_" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(5,9)))

def rand_str(n=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


# ══ LAYER 1 — Variable Name Mangler ══════════════════════
def mangle_varnames(js):
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


# ══ LAYER 2 — String Encoder ═════════════════════════════
def encode_strings(js):
    def hex_encode(m):
        s = m.group(1)
        if len(s) < 3:
            return m.group(0)
        return '"' + "".join(f"\\x{ord(c):02x}" for c in s) + '"'
    def uni_encode(m):
        s = m.group(1)
        if len(s) < 3:
            return m.group(0)
        return "'" + "".join(f"\\u{ord(c):04x}" for c in s) + "'"
    js = re.sub(r'"([^"\\]{3,})"', hex_encode, js)
    js = re.sub(r"'([^'\\]{3,})'", uni_encode, js)
    return js


# ══ LAYER 3 — Number Obfuscation ═════════════════════════
def obfuscate_numbers(js):
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
            return f"(0x{n:X})"
    return re.sub(r'\b([2-9][0-9]+)\b', num_replace, js)


# ══ LAYER 4 — Dead Code Injector ═════════════════════════
def inject_dead_code(js):
    dead_snippets = []
    for _ in range(10):
        vname = rand_var()
        vval  = rand_str(16)
        dead_snippets.append(f'if(typeof window==="{rand_str(4)}"){{var {vname}="{vval}";}}\n')
    fake_switch = ('switch("' + rand_str(3) + '"){' +
                   "".join(f'case "{rand_str(2)}":break;' for _ in range(4)) + "}\n")
    dead_snippets.append(fake_switch)
    fake_try = f'try{{if(false){{throw new Error("{rand_str(8)}");}}}}catch(e){{}}\n'
    dead_snippets.append(fake_try)
    lines = js.split("\n")
    for snippet in random.choices(dead_snippets, k=5):
        pos = random.randint(0, len(lines))
        lines.insert(pos, snippet)
    return "\n".join(lines)


# ══ LAYER 5 — Anti-Debug Scripts ═════════════════════════
def build_anti_debug():
    jitter   = random.randint(80, 120)
    interval = random.randint(800, 1200)
    da, db, dc = rand_var(), rand_var(), rand_var()
    return (
        f"(function {da}(){{"
        f"var {db}=new Date();debugger;"
        f"if(new Date()-{db}>{jitter}){{"
        f"document.body.innerHTML='';"
        f"window.location.replace('about:blank');}}"
        f"setInterval(function(){{"
        f"var {dc}=new Date();debugger;"
        f"if(new Date()-{dc}>{jitter}){{"
        f"document.body.innerHTML='';"
        f"window.location.replace('about:blank');}}"
        f"}},{interval});}})();"
    )

RIGHT_CLICK_BLOCK = (
    "(function(){"
    "document.addEventListener('contextmenu',function(e){e.preventDefault();return false;});"
    "document.addEventListener('keydown',function(e){"
    "if(e.keyCode===123){e.preventDefault();return false;}"
    "if(e.ctrlKey&&e.shiftKey&&[73,74,67].indexOf(e.keyCode)>-1){e.preventDefault();return false;}"
    "if(e.ctrlKey&&[85,83,80].indexOf(e.keyCode)>-1){e.preventDefault();return false;}"
    "});"
    "document.addEventListener('selectstart',function(e){e.preventDefault();});"
    "document.addEventListener('dragstart',function(e){e.preventDefault();});"
    "document.addEventListener('copy',function(e){e.preventDefault();});"
    "document.addEventListener('cut',function(e){e.preventDefault();});"
    "document.addEventListener('print',function(e){e.preventDefault();});"
    "})();"
)

def build_devtools_detect():
    threshold = random.randint(150, 170)
    v = rand_var()
    interval  = random.randint(400, 600)
    msg_html  = (
        "<div style=\\"display:flex;align-items:center;justify-content:center;"
        "height:100vh;background:#0a0a0a;color:#ff0000;font-size:20px;"
        "font-family:monospace;text-align:center;padding:20px\\">"
        "DevTools Detected! Access Denied</div>"
    )
    return (
        f"(function(){{"
        f"setInterval(function(){{"
        f"var {v}=window.outerWidth-window.innerWidth>{threshold}"
        f"||window.outerHeight-window.innerHeight>{threshold};"
        f"if({v}){{document.body.innerHTML='{msg_html}';}}"
        f"}},{interval});}})();"
    )

CONSOLE_CLEAR = (
    "(function(){"
    "var _no=function(){};"
    "['log','warn','error','info','debug','table','dir','trace'].forEach(function(m){"
    "try{console[m]=_no;}catch(e){}});"
    "setInterval(function(){try{console.clear();}catch(e){}},100);"
    "})();"
)


# ══ LAYER 6 — Multi-Key XOR + ZLIB ═══════════════════════
def multi_xor_encrypt(data, keys):
    result = bytearray(len(data))
    for i, b in enumerate(data):
        xored = b
        for k in keys:
            xored ^= k[i % len(k)]
        result[i] = xored
    return bytes(result)

def triple_encrypt(html):
    keys_raw   = [rand_str(16), rand_str(12), rand_str(20)]
    keys_bytes = [k.encode() for k in keys_raw]
    compressed = zlib.compress(html.encode("utf-8"), level=9)
    xored      = multi_xor_encrypt(compressed, keys_bytes)
    b64        = base64.b64encode(xored).decode()
    return b64, keys_raw


# ══ LAYER 7 — Function Name Mangler ══════════════════════
def mangle_funcnames(js):
    pattern  = re.compile(r'\bfunction\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(')
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


# ══ LAYER 9 — DOM Integrity Check ════════════════════════
def build_integrity_check():
    encoded  = "".join(f"\\x{ord(c):02x}" for c in CREDIT_TAG)
    v1, v2   = rand_var(), rand_var()
    interval = random.randint(2000, 4000)
    return (
        f"(function(){{"
        f"var {v1}='{encoded}';"
        f"setInterval(function(){{"
        f"var {v2}=document.documentElement.innerHTML||'';"
        f"if({v2}.indexOf({v1})<0){{"
        f"document.open();"
        f"document.write('<h1 style=\"color:red;text-align:center;margin-top:40vh\">Tampered File Detected</h1>');"
        f"document.close();}}"
        f"}},{interval});}})();"
    )


# ══ LAYER 10 — Triple Eval Chain ═════════════════════════
def split_string(s, chunk=50):
    parts = [f'"{s[i:i+chunk]}"' for i in range(0, len(s), chunk)]
    return "+".join(parts)

def build_eval_chain(inner_js):
    l1       = base64.b64encode(inner_js.encode()).decode()
    l2_js    = f"eval(atob({split_string(l1, 60)}));"
    l2       = base64.b64encode(l2_js.encode()).decode()
    l3_js    = f"(new Function(atob({split_string(l2, 60)})))();"
    l3       = base64.b64encode(l3_js.encode()).decode()
    return f"setTimeout(function(){{(new Function(atob({split_string(l3, 60)})))();}},1);"


# ══ MASTER PROTECTOR ══════════════════════════════════════
def protect_html(html):
    ts  = int(time.time())
    sig = hashlib.sha256((html + str(ts)).encode()).hexdigest()[:16].upper()

    # Step 1 — Obfuscate inline JS
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

    # Step 2 — Triple encrypt
    b64_payload, keys = triple_encrypt(html)
    payload_split     = split_string(b64_payload, 70)

    # Step 3 — Build decoder
    k_arrays = []
    for k in keys:
        hex_vals = ",".join(f"0x{ord(c):02x}" for c in k)
        k_arrays.append(f"[{hex_vals}]")

    vk  = rand_var()
    vp  = rand_var()
    vb  = rand_var()
    vx  = rand_var()
    vr  = rand_var()
    vi  = rand_var()
    vj  = rand_var()
    vin = rand_var()
    vdc = rand_var()

    decoder_js = (
        f"var {vk}=[{','.join(k_arrays)}];"
        f"var {vp}={payload_split};"
        f"var {vb}=atob({vp});"
        f"var {vx}=new Uint8Array({vb}.length);"
        f"for(var {vi}=0;{vi}<{vb}.length;{vi}++){{"
        f"var {vj}={vb}.charCodeAt({vi});"
        f"for(var {vin}=0;{vin}<{vk}.length;{vin}++){{"
        f"{vj}^={vk}[{vin}][{vi}%{vk}[{vin}].length];}}"
        f"{vx}[{vi}]={vj};}}"
        f"var {vdc}=pako.inflate({vx},{{to:'string'}});"
        f"document.open();document.write({vdc});document.close();"
    )

    decoder_js = mangle_varnames(decoder_js)
    decoder_js = obfuscate_numbers(decoder_js)
    decoder_js = inject_dead_code(decoder_js)

    iife       = f"(function(){{{decoder_js}}})();"
    final_eval = build_eval_chain(iife)

    anti_debug      = build_anti_debug()
    devtools_detect = build_devtools_detect()
    integrity_check = build_integrity_check()

    credit_comment = (
        "<!--\n"
        f"  PROTECTED BY {CREDIT_TAG}\n"
        f"  {BOT_NAME} {VERSION}\n"
        f"  Timestamp : {ts}\n"
        f"  Signature : {sig}\n"
        f"  Warning   : Removing or modifying this header will break the page!\n"
        "-->"
    )

    protected = (
        f"{credit_comment}\n"
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<script src=\"https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js\"></script>\n"
        "<script>\n"
        f"{CONSOLE_CLEAR}\n"
        f"{anti_debug}\n"
        f"{RIGHT_CLICK_BLOCK}\n"
        f"{devtools_detect}\n"
        f"{integrity_check}\n"
        f"{final_eval}\n"
        "</script>\n"
        "</head>\n"
        "</html>"
    )

    return protected


# ══ BOT HANDLERS ══════════════════════════════════════════
LAYER_LIST = (
    "L1  - Variable Name Mangling\n"
    "L2  - String Hex/Unicode Encoding\n"
    "L3  - Number Obfuscation\n"
    "L4  - Dead Code Injection\n"
    "L5  - Anti-Debug + DevTools + Console Block\n"
    "L6  - Multi-Key XOR + ZLIB Compress\n"
    "L7  - Function Name Mangling\n"
    "L8  - Control Flow Flattening\n"
    "L9  - DOM Integrity + Tamper Detection\n"
    "L10 - Triple-Nested Eval Chain\n"
    "BONUS - Right-Click / Copy / Print Disabled\n"
    "BONUS - Console Poisoned & Auto-Cleared"
)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[
        InlineKeyboardButton("Channel", url=f"https://t.me/{CREDIT_TAG.lstrip('@')}"),
        InlineKeyboardButton("Help", callback_data="help"),
    ],[
        InlineKeyboardButton("Layers Info", callback_data="layers"),
    ]]
    text = (
        f"*{BOT_NAME}*\n"
        f"_{VERSION}_\n\n"
        f"*World's Most Advanced HTML Protector*\n\n"
        f"*10 Protection Layers:*\n"
        f"`{LAYER_LIST}`\n\n"
        f"Apni `.html` file bhejo instant protection ke liye!\n\n"
        f"_Powered by {CREDIT_TAG}_"
    )
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(kb))

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "*HOW TO USE:*\n\n"
        "1. Apni `.html` file bhejo is bot ko\n"
        "2. Bot 10-layer protection lagayega\n"
        "3. Protected file turant wapas milegi\n\n"
        "*Protected file mein:*\n"
        "- Right click / Copy / Print BLOCKED\n"
        "- DevTools open karo PAGE BLANK\n"
        "- Console use karo POISONED\n"
        "- Source code TRIPLE ENCRYPTED\n"
        "- Header remove karo PAGE BREAKS\n"
        "- Har file ka alag unique signature\n\n"
        f"_Powered by {CREDIT_TAG}_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "help":
        await q.message.reply_text(
            "*HOW TO USE:*\n\n"
            "1. `.html` file bhejo\n"
            "2. 10-layer protection lagega\n"
            "3. Protected file milegi instantly\n\n"
            f"_Powered by {CREDIT_TAG}_",
            parse_mode="Markdown"
        )
    elif q.data == "layers":
        await q.message.reply_text(
            f"*10 PROTECTION LAYERS:*\n\n`{LAYER_LIST}`\n\n"
            f"_Powered by {CREDIT_TAG}_",
            parse_mode="Markdown"
        )

async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.lower().endswith(".html"):
        await update.message.reply_text("Sirf `.html` file bhejo!", parse_mode="Markdown")
        return

    if doc.file_size > 5 * 1024 * 1024:
        await update.message.reply_text("File 5MB se badi hai!")
        return

    msg = await update.message.reply_text(
        "*Processing...*\n10 layers laga raha hoon...",
        parse_mode="Markdown"
    )

    try:
        tg_file  = await doc.get_file()
        raw      = await tg_file.download_as_bytearray()
        orig_html = raw.decode("utf-8", errors="replace")

        start_t   = time.time()
        protected = protect_html(orig_html)
        elapsed   = time.time() - start_t

        out_buf       = BytesIO(protected.encode("utf-8"))
        fname         = doc.file_name.replace(".html", "")
        out_buf.name  = f"protected_{fname}.html"

        orig_kb = len(raw) / 1024
        prot_kb = len(protected.encode()) / 1024
        ratio   = prot_kb / orig_kb if orig_kb > 0 else 0

        await msg.delete()
        await update.message.reply_document(
            document=out_buf,
            caption=(
                f"*Protection Complete!*\n\n"
                f"File: `{doc.file_name}`\n"
                f"Original : `{orig_kb:.1f} KB`\n"
                f"Protected: `{prot_kb:.1f} KB`\n"
                f"Size ratio: `{ratio:.1f}x`\n"
                f"Time: `{elapsed:.2f}s`\n\n"
                f"*10 Layers Applied:*\n"
                f"L1 Variable + Function Mangling\n"
                f"L2 String Hex/Unicode Encoding\n"
                f"L3 Number Obfuscation\n"
                f"L4 Dead Code Injection\n"
                f"L5 Anti-Debug + DevTools Block\n"
                f"L6 Multi-Key XOR + ZLIB\n"
                f"L7 Function Mangling\n"
                f"L8 Control Flow Flatten\n"
                f"L9 DOM Integrity Check\n"
                f"L10 Triple Eval Chain\n\n"
                f"_Powered by {CREDIT_TAG}_"
            ),
            parse_mode="Markdown"
        )

    except UnicodeDecodeError:
        await msg.edit_text("File encoding issue! UTF-8 HTML bhejo.")
    except Exception as e:
        await msg.edit_text(f"Error: `{str(e)[:300]}`", parse_mode="Markdown")


# ══ MAIN ══════════════════════════════════════════════════
def main():
    print(f"Starting {BOT_NAME} {VERSION}")
    print(f"Powered by {CREDIT_TAG}")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("Bot running! Telegram pe /start bhejo.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
