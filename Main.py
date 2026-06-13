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

BOT_TOKEN  = "8746353333:AAFsO0338awUxufrU3LSqKwbF5T_ewaIlqM"
CREDIT_TAG = "@Skybhai_on_Top"
BOT_NAME   = "SKY HTML PROTECTOR PRO"
VERSION    = "v2.0 ULTRA"


def rand_hex_name(seed=""):
    h = hashlib.sha256((seed + str(random.random())).encode()).hexdigest()[:6].upper()
    return "_0x" + h

def rand_var():
    return "_" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(5,9)))

def rand_str(n=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def mangle_varnames(js):
    pattern = re.compile(r'\b(var|let|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\b')
    name_map = {}
    def replacer(m):
        kw, name = m.group(1), m.group(2)
        if name not in name_map:
            name_map[name] = rand_hex_name(name)
        return kw + " " + name_map[name]
    js = pattern.sub(replacer, js)
    for orig, mangled in name_map.items():
        js = re.sub(r'\b' + re.escape(orig) + r'\b', mangled, js)
    return js


def encode_strings(js):
    def hex_encode(m):
        s = m.group(1)
        if len(s) < 3:
            return m.group(0)
        return '"' + "".join("\\x{:02x}".format(ord(c)) for c in s) + '"'
    def uni_encode(m):
        s = m.group(1)
        if len(s) < 3:
            return m.group(0)
        return "'" + "".join("\\u{:04x}".format(ord(c)) for c in s) + "'"
    js = re.sub(r'"([^"\\]{3,})"', hex_encode, js)
    js = re.sub(r"'([^'\\]{3,})'", uni_encode, js)
    return js


def obfuscate_numbers(js):
    def num_replace(m):
        n = int(m.group(0))
        if n == 0:
            return "(0x0^0x0)"
        s = random.randint(0, 2)
        if s == 0:
            a = random.randint(1, min(n, 0xFF))
            b = n ^ a
            return "(0x{:X}^0x{:X})".format(a, b)
        elif s == 1:
            a = random.randint(1, min(n, 0xFF))
            b = n - a
            return "(0x{:X}+0x{:X})".format(a, b)
        else:
            return "(0x{:X})".format(n)
    return re.sub(r'\b([2-9][0-9]+)\b', num_replace, js)


def inject_dead_code(js):
    snippets = []
    for _ in range(6):
        vname = rand_var()
        vval  = rand_str(12)
        snippets.append("if(false){var " + vname + "='" + vval + "';}\n")
    snippets.append("try{if(false){throw new Error('x');}}catch(e){}\n")
    lines = js.split("\n")
    for snippet in random.choices(snippets, k=4):
        pos = random.randint(0, len(lines))
        lines.insert(pos, snippet)
    return "\n".join(lines)


def build_anti_debug():
    jitter   = str(random.randint(80, 120))
    interval = str(random.randint(800, 1200))
    da = rand_var()
    db = rand_var()
    dc = rand_var()
    return (
        "(function " + da + "(){"
        + "var " + db + "=new Date();debugger;"
        + "if(new Date()-" + db + ">" + jitter + "){"
        + "document.body.innerHTML='';"
        + "window.location.replace('about:blank');}"
        + "setInterval(function(){"
        + "var " + dc + "=new Date();debugger;"
        + "if(new Date()-" + dc + ">" + jitter + "){"
        + "document.body.innerHTML='';"
        + "window.location.replace('about:blank');}"
        + "}," + interval + ");})();"
    )


RIGHT_CLICK_BLOCK = (
    "(function(){"
    + "document.addEventListener('contextmenu',function(e){e.preventDefault();});"
    + "document.addEventListener('keydown',function(e){"
    + "if(e.keyCode===123){e.preventDefault();return false;}"
    + "if(e.ctrlKey&&e.shiftKey&&[73,74,67].indexOf(e.keyCode)>-1){e.preventDefault();return false;}"
    + "if(e.ctrlKey&&[85,83,80].indexOf(e.keyCode)>-1){e.preventDefault();return false;}"
    + "});"
    + "document.addEventListener('selectstart',function(e){e.preventDefault();});"
    + "document.addEventListener('copy',function(e){e.preventDefault();});"
    + "document.addEventListener('cut',function(e){e.preventDefault();});"
    + "})();"
)


def build_devtools_detect():
    threshold = str(random.randint(150, 170))
    interval  = str(random.randint(400, 600))
    v = rand_var()
    blocked = (
        "<div style='display:flex;align-items:center;justify-content:center;"
        "height:100vh;background:#0a0a0a;color:#ff0000;font-size:20px;"
        "font-family:monospace'>DevTools Detected</div>"
    )
    return (
        "(function(){"
        + "setInterval(function(){"
        + "var " + v + "=window.outerWidth-window.innerWidth>" + threshold
        + "||window.outerHeight-window.innerHeight>" + threshold + ";"
        + "if(" + v + "){"
        + "document.body.innerHTML='" + blocked + "';}"
        + "}," + interval + ");})();"
    )


CONSOLE_CLEAR = (
    "(function(){"
    + "var _no=function(){};"
    + "['log','warn','error','info','debug','table','dir'].forEach(function(m){"
    + "try{console[m]=_no;}catch(e){}});"
    + "setInterval(function(){try{console.clear();}catch(e){}},100);"
    + "})();"
)


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


def mangle_funcnames(js):
    pattern  = re.compile(r'\bfunction\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(')
    name_map = {}
    def replacer(m):
        name = m.group(1)
        if name not in name_map:
            name_map[name] = rand_hex_name(name)
        return "function " + name_map[name] + "("
    js = pattern.sub(replacer, js)
    for orig, mangled in name_map.items():
        js = re.sub(r'\b' + re.escape(orig) + r'\b', mangled, js)
    return js


def build_integrity_check():
    encoded  = "".join("\\x{:02x}".format(ord(c)) for c in CREDIT_TAG)
    v1 = rand_var()
    v2 = rand_var()
    interval = str(random.randint(2000, 4000))
    tamper_html = "<h1 style='color:red;text-align:center;margin-top:40vh'>Tampered File Detected</h1>"
    return (
        "(function(){"
        + "var " + v1 + "='" + encoded + "';"
        + "setInterval(function(){"
        + "var " + v2 + "=document.documentElement.innerHTML||'';"
        + "if(" + v2 + ".indexOf(" + v1 + ")<0){"
        + "document.open();"
        + "document.write('" + tamper_html + "');"
        + "document.close();}"
        + "}," + interval + ");})();"
    )


def split_string(s, chunk=50):
    parts = ['"' + s[i:i+chunk] + '"' for i in range(0, len(s), chunk)]
    return "+".join(parts)

def build_eval_chain(inner_js):
    l1    = base64.b64encode(inner_js.encode()).decode()
    l2_js = "eval(atob(" + split_string(l1, 60) + "));"
    l2    = base64.b64encode(l2_js.encode()).decode()
    l3_js = "(new Function(atob(" + split_string(l2, 60) + ")))();"
    l3    = base64.b64encode(l3_js.encode()).decode()
    return "setTimeout(function(){(new Function(atob(" + split_string(l3, 60) + ")))();},1);"


def protect_html(html):
    ts  = int(time.time())
    sig = hashlib.sha256((html + str(ts)).encode()).hexdigest()[:16].upper()

    def obf_script(m):
        inner = m.group(1).strip()
        if not inner:
            return m.group(0)
        inner = mangle_funcnames(inner)
        inner = mangle_varnames(inner)
        inner = encode_strings(inner)
        inner = obfuscate_numbers(inner)
        inner = inject_dead_code(inner)
        return "<script>" + inner + "</script>"

    html = re.sub(
        r"<script(?:\s[^>]*)?>(\s*)([\s\S]*?)</script>",
        obf_script, html, flags=re.IGNORECASE
    )

    b64_payload, keys = triple_encrypt(html)
    payload_split     = split_string(b64_payload, 70)

    k_arrays = []
    for k in keys:
        hex_vals = ",".join("0x{:02x}".format(ord(c)) for c in k)
        k_arrays.append("[" + hex_vals + "]")

    vk  = rand_var()
    vp  = rand_var()
    vb  = rand_var()
    vx  = rand_var()
    vi  = rand_var()
    vj  = rand_var()
    vin = rand_var()
    vdc = rand_var()

    decoder_js = (
        "var " + vk + "=[" + ",".join(k_arrays) + "];"
        + "var " + vp + "=" + payload_split + ";"
        + "var " + vb + "=atob(" + vp + ");"
        + "var " + vx + "=new Uint8Array(" + vb + ".length);"
        + "for(var " + vi + "=0;" + vi + "<" + vb + ".length;" + vi + "++){"
        + "var " + vj + "=" + vb + ".charCodeAt(" + vi + ");"
        + "for(var " + vin + "=0;" + vin + "<" + vk + ".length;" + vin + "++){"
        + vj + "^=" + vk + "[" + vin + "][" + vi + "%" + vk + "[" + vin + "].length];}"
        + vx + "[" + vi + "]=" + vj + ";}"
        + "var " + vdc + "=pako.inflate(" + vx + ",{to:'string'});"
        + "document.open();document.write(" + vdc + ");document.close();"
    )

    decoder_js = mangle_varnames(decoder_js)
    decoder_js = obfuscate_numbers(decoder_js)
    decoder_js = inject_dead_code(decoder_js)

    iife       = "(function(){" + decoder_js + "})();"
    final_eval = build_eval_chain(iife)

    anti_debug      = build_anti_debug()
    devtools_detect = build_devtools_detect()
    integrity_check = build_integrity_check()

    credit_comment = (
        "<!--\n"
        + "  PROTECTED BY " + CREDIT_TAG + "\n"
        + "  " + BOT_NAME + " " + VERSION + "\n"
        + "  Timestamp : " + str(ts) + "\n"
        + "  Signature : " + sig + "\n"
        + "  Warning: Removing this header will break the page!\n"
        + "-->"
    )

    protected = (
        credit_comment + "\n"
        + "<!DOCTYPE html>\n"
        + "<html>\n"
        + "<head>\n"
        + '<meta charset="UTF-8">\n'
        + '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        + '<script src="https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js"></script>\n'
        + "<script>\n"
        + CONSOLE_CLEAR + "\n"
        + anti_debug + "\n"
        + RIGHT_CLICK_BLOCK + "\n"
        + devtools_detect + "\n"
        + integrity_check + "\n"
        + final_eval + "\n"
        + "</script>\n"
        + "</head>\n"
        + "</html>"
    )

    return protected


LAYER_LIST = (
    "L1  - Variable Name Mangling\n"
    "L2  - String Hex Encoding\n"
    "L3  - Number Obfuscation\n"
    "L4  - Dead Code Injection\n"
    "L5  - Anti-Debug + DevTools Block\n"
    "L6  - Multi-Key XOR + ZLIB\n"
    "L7  - Function Name Mangling\n"
    "L8  - Integrity Tamper Check\n"
    "L9  - Triple Nested Eval Chain\n"
    "BONUS - Right-Click + Copy Disabled\n"
    "BONUS - Console Poisoned"
)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[
        InlineKeyboardButton("Channel", url="https://t.me/" + CREDIT_TAG.lstrip("@")),
        InlineKeyboardButton("Help", callback_data="help"),
    ],[
        InlineKeyboardButton("Layers Info", callback_data="layers"),
    ]]
    text = (
        "*" + BOT_NAME + "*\n"
        + "_" + VERSION + "_\n\n"
        + "*World's Most Advanced HTML Protector*\n\n"
        + "*Protection Layers:*\n"
        + "`" + LAYER_LIST + "`\n\n"
        + "Apni `.html` file bhejo instant protection ke liye!\n\n"
        + "_Powered by " + CREDIT_TAG + "_"
    )
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(kb))

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "*HOW TO USE:*\n\n"
        + "1. Apni `.html` file bhejo is bot ko\n"
        + "2. Bot 10-layer protection lagayega\n"
        + "3. Protected file turant wapas milegi\n\n"
        + "*Protected file mein:*\n"
        + "- Right click / Copy BLOCKED\n"
        + "- DevTools open PAGE BLANK\n"
        + "- Console POISONED\n"
        + "- Source code TRIPLE ENCRYPTED\n"
        + "- Header remove PAGE BREAKS\n\n"
        + "_Powered by " + CREDIT_TAG + "_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "help":
        await q.message.reply_text(
            "*HOW TO USE:*\n\n"
            + "1. `.html` file bhejo\n"
            + "2. 10-layer protection lagega\n"
            + "3. Protected file milegi\n\n"
            + "_Powered by " + CREDIT_TAG + "_",
            parse_mode="Markdown"
        )
    elif q.data == "layers":
        await q.message.reply_text(
            "*10 PROTECTION LAYERS:*\n\n`" + LAYER_LIST + "`\n\n"
            + "_Powered by " + CREDIT_TAG + "_",
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
        tg_file   = await doc.get_file()
        raw       = await tg_file.download_as_bytearray()
        orig_html = raw.decode("utf-8", errors="replace")

        start_t   = time.time()
        protected = protect_html(orig_html)
        elapsed   = time.time() - start_t

        out_buf      = BytesIO(protected.encode("utf-8"))
        fname        = doc.file_name.replace(".html", "")
        out_buf.name = "protected_" + fname + ".html"

        orig_kb = len(raw) / 1024
        prot_kb = len(protected.encode()) / 1024
        ratio   = prot_kb / orig_kb if orig_kb > 0 else 0

        await msg.delete()
        await update.message.reply_document(
            document=out_buf,
            caption=(
                "*Protection Complete!*\n\n"
                + "File: `" + doc.file_name + "`\n"
                + "Original : `" + "{:.1f}".format(orig_kb) + " KB`\n"
                + "Protected: `" + "{:.1f}".format(prot_kb) + " KB`\n"
                + "Ratio: `" + "{:.1f}".format(ratio) + "x`\n"
                + "Time: `" + "{:.2f}".format(elapsed) + "s`\n\n"
                + "*Layers Applied:*\n"
                + "`" + LAYER_LIST + "`\n\n"
                + "_Powered by " + CREDIT_TAG + "_"
            ),
            parse_mode="Markdown"
        )

    except UnicodeDecodeError:
        await msg.edit_text("File encoding issue! UTF-8 HTML bhejo.")
    except Exception as e:
        await msg.edit_text("Error: `" + str(e)[:300] + "`", parse_mode="Markdown")


def main():
    print("Starting " + BOT_NAME + " " + VERSION)
    print("Powered by " + CREDIT_TAG)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("Bot running! Telegram pe /start bhejo.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
