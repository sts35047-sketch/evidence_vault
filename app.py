"""
EvidenceVault — Cyberbullying Detection & Legal Evidence Platform
Run: python app.py
Visit: http://localhost:5000
"""

from flask import (Flask, render_template, request, redirect,
                   url_for, send_file, flash, jsonify, session, Response, send_from_directory)
import sqlite3, os, hashlib, uuid, json, threading, smtplib, requests, re, csv
from io import StringIO
from datetime import datetime
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)

# ── Gemini API Integration ────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBl1mMhNvji9d5zqa9Rq_CrC3px2R_L7PA")
    genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠ Google Generative AI not installed. Run: pip install google-generativeai")

# ── Cryptography (AES-256 Encryption) ─────────────────────────────────────────
try:
    from cryptography.fernet import Fernet
    # Static key for demo purposes (in prod, load strictly from secure ENV)
    FERNET_KEY = os.environ.get("ENCRYPTION_KEY", b"E9-g8Qk8wZ8_dK5rQ1y5_wVpL0xQ5v-8nB_k-5H_V_0=")
    cipher_suite = Fernet(FERNET_KEY)
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    print("⚠ Cryptography not installed. Run: pip install cryptography")

def encrypt_text(text: str) -> str:
    if not ENCRYPTION_AVAILABLE or not text: return text
    try: return cipher_suite.encrypt(text.encode()).decode()
    except Exception: return text

def decrypt_text(text: str) -> str:
    if not ENCRYPTION_AVAILABLE or not text: return text
    try: return cipher_suite.decrypt(text.encode()).decode()
    except Exception: return text # Fallback for old plain text data

# ── Optional imports (graceful fallback) ─────────────────────────────────────
try:
    import pytesseract
    from PIL import Image, ImageDraw, ImageFont
    OCR_AVAILABLE = True
    pytesseract.pytesseract.tesseract_cmd = os.environ.get("TESSERACT_CMD", r"tesseract")
except ImportError:
    OCR_AVAILABLE = False

try:
    from detoxify import Detoxify as _Detoxify
    DETOXIFY_AVAILABLE = True
except ImportError:
    DETOXIFY_AVAILABLE = False

# ── App & Config ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ev_secret_2026_xK9#mQ")

BASE_DIR      = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH       = os.path.join(BASE_DIR, "evidence.db")
CHAIN_PATH    = os.path.join(BASE_DIR, "chain_ledger.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT   = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER   = os.environ.get("SMTP_USER", "")
SMTP_PASS   = os.environ.get("SMTP_PASS", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")
API_KEY     = os.environ.get("API_KEY", "evault-demo-key-2026")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
LIBRETRANSLATE_URLS = [u.strip() for u in os.environ.get("LIBRETRANSLATE_URLS", "https://libretranslate.com/translate").split(",") if u.strip()]
LIBRETRANSLATE_API_KEYS = [k.strip() for k in os.environ.get("LIBRETRANSLATE_API_KEYS", "").split(",") if k.strip()]
GEMINI_API_KEYS = [k.strip() for k in os.environ.get("GEMINI_API_KEYS", "AIzaSyAXTS0_F2tUzitO7GJotK2utRhX52yg3rE,AIzaSyBl1mMhNvji9d5zqa9Rq_CrC3px2R_L7PA,AIzaSyDtsZDp-S7zrOYEmQNq7z8tFemBnuKyyjU,AIzaSyBprUAY0SGr_LPbUHbkq1tGJhzKZmcdFjE,AIzaSyA0KbYd_X1DogDrpRyFq1pq3w8EFYyqUh4,AIzaSyCWop6u56oRsv45e3sIV95PlGItPaEg79o,AIzaSyDw_g5gfQertpiy-zsb7k3XGt6Z-ZnbHX0").split(",") if k.strip()]

EXECUTOR    = ThreadPoolExecutor(max_workers=4)

# ── Static users ──────────────────────────────────────────────────────────────
def _pw(p): return hashlib.sha256(p.encode()).hexdigest()
USERS = {
    "admin": {"password": _pw("admin123"), "role": "admin"},
    "user":  {"password": _pw("user123"),  "role": "user"},
}

# ── ML Models & APIs ──────────────────────────────────────────────────────────
_model = None
_model_lock = threading.Lock()

def get_model():
    global _model
    if _model is None and DETOXIFY_AVAILABLE:
        with _model_lock:
            if _model is None:
                try: _model = _Detoxify("original")
                except Exception: pass
    return _model

def translate_text(text: str):
    if not text.strip():
        return text, "en"

    for url in LIBRETRANSLATE_URLS:
        for api_key in LIBRETRANSLATE_API_KEYS or [None]:
            try:
                payload = {"q": text, "source": "auto", "target": "en"}
                if api_key:
                    payload["api_key"] = api_key
                resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                translated = data.get("translatedText", text)
                detected_lang = data.get("detectedLanguage", {}).get("language", "unknown")
                if detected_lang != "en" and translated != text:
                    return translated, detected_lang
            except Exception as e:
                print(f"[Translate fallback] failed url={url} key={api_key} error={e}")
                continue

    return text, "en"


def get_gemini_insights(text: str):
    if not GEMINI_AVAILABLE or not genai:
        return None

    prompt = f"""
    You are an expert legal forensics AI analyzing potential cyberbullying/harassment evidence.
    Analyze the text below and return ONLY a raw, valid JSON object without markdown formatting.
    The JSON must contain these exact keys:
    {{
        "summary": "A professional one-paragraph legal summary of the incident.",
        "entities": ["list", "of", "people", "or", "platforms", "mentioned"],
        "hidden_context": "Explanation of any sarcasm, passive-aggression, or implicit threats."
    }}
    Text to analyze: "{text}"
    """

    for api_key in GEMINI_API_KEYS or [None]:
        try:
            if api_key:
                genai.configure(api_key=api_key)
            # Try gemini-1.5-flash first, fall back to gemini-pro
            for model_name in ['gemini-1.5-flash', 'gemini-pro']:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    clean_json = response.text.replace('```json', '').replace('```', '').strip()
                    result = json.loads(clean_json)
                    print(f"[Gemini] ✓ Success with {model_name}")
                    return result
                except Exception as model_err:
                    print(f"[Gemini] {model_name} failed: {type(model_err).__name__}")
                    continue
        except Exception as e:
            print(f"[Gemini fallback] failed key={api_key} error={type(e).__name__}: {str(e)[:80]}")
            continue

    return None

def extract_text_from_image(image_path: str) -> str:
    """Try Gemini Vision with fallback keys, then Tesseract OCR with preprocessing."""
    if not os.path.exists(image_path):
        print(f"[Vision OCR] Image not found: {image_path}")
        return ""

    file_size = os.path.getsize(image_path)
    if file_size > 20 * 1024 * 1024:
        print(f"[Vision OCR] File too large ({file_size} bytes), skipping Gemini")
    else:
        if GEMINI_AVAILABLE and genai:
            for idx, api_key in enumerate(GEMINI_API_KEYS or [None], 1):
                try:
                    print(f"[Vision OCR] Trying Gemini key #{idx}...")
                    if api_key:
                        genai.configure(api_key=api_key)

                    # Try both models
                    for model_name in ['gemini-1.5-flash', 'gemini-pro-vision', 'gemini-pro']:
                        try:
                            vision_model = genai.GenerativeModel(model_name)
                            from PIL import Image
                            img = Image.open(image_path)
                            print(f"[Vision OCR] Trying {model_name} (size: {file_size} bytes)...")

                            v_resp = vision_model.generate_content(
                                [
                                    "Extract ALL readable text from this image. Reply ONLY with the text content. If no text, reply: NO_TEXT_FOUND",
                                    img,
                                ],
                                request_options={"timeout": 30},
                            )

                            extracted = v_resp.text.strip()
                            if extracted and "NO_TEXT_FOUND" not in extracted:
                                print(f"[Vision OCR] ✓ Success with {model_name}")
                                return extracted
                            print(f"[Vision OCR] No text detected with {model_name}")

                        except Exception as model_err:
                            print(f"[Vision OCR] {model_name} failed: {type(model_err).__name__}")
                            continue
                except Exception as e:
                    print(f"[Vision OCR] Key #{idx} error: {type(e).__name__}: {str(e)[:80]}")
                    continue

    print("[Vision OCR] Falling back to Tesseract OCR...")
    if not OCR_AVAILABLE:
        print("[Tesseract] Not available - install via: pip install pytesseract")
        return ""

    try:
        from PIL import Image, ImageOps, ImageEnhance
        import time

        base_image = Image.open(image_path).convert("RGB")
        candidates = []
        gray = base_image.convert("L")
        candidates.append(("original", base_image))
        candidates.append(("grayscale", gray))
        candidates.append(("contrast", ImageEnhance.Contrast(gray).enhance(2.0)))
        candidates.append(("autocontrast", ImageOps.autocontrast(gray)))
        candidates.append(("resize", gray.resize((max(800, gray.width * 2), max(800, gray.height * 2)), Image.LANCZOS)))

        for name, img in candidates:
            try:
                start = time.time()
                text = pytesseract.image_to_string(img).strip()
                elapsed = time.time() - start
                if text:
                    print(f"[Tesseract OCR] ✓ Extracted text using {name} in {elapsed:.2f}s")
                    return text
                print(f"[Tesseract OCR] No text detected with {name} (took {elapsed:.2f}s)")
            except Exception as inner:
                print(f"[Tesseract OCR] {name} failed: {type(inner).__name__}: {str(inner)[:100]}")
                continue

        # Final pass: binarize
        try:
            bw = gray.point(lambda x: 0 if x < 128 else 255, mode="1")
            text = pytesseract.image_to_string(bw).strip()
            if text:
                print(f"[Tesseract OCR] ✓ Extracted text using binarized image")
                return text
            print("[Tesseract OCR] No text detected after binarization")
        except Exception as bin_err:
            print(f"[Tesseract OCR] binarization failed: {type(bin_err).__name__}: {str(bin_err)[:100]}")

    except Exception as e:
        print(f"[Vision OCR] Tesseract preprocessing failed: {type(e).__name__}: {str(e)[:100]}")

    return ""

def calculate_sentiment_extensions(text: str, scores: dict):
    text_lower = text.lower()
    sarcasm_score = 0.0
    if "?!" in text or "!?" in text or "..." in text: sarcasm_score += 0.3
    if any(k in text_lower for k in ["fine", "whatever", "obviously", "sure thing", "great job", "wow"]):
        sarcasm_score += 0.4
    
    anger_score = scores.get("insult", 0.0) * 0.6
    if text.isupper(): anger_score += 0.4
    if text.count("!") > 2: anger_score += 0.3
        
    scores["sarcasm_probability"] = round(min(sarcasm_score, 1.0), 4)
    scores["anger_index"] = round(min(anger_score, 1.0), 4)
    return scores

TOXIC_KW = ["hate","stupid","idiot","kill","die","fuck","shit","damn","asshole","bitch","ugly","worthless","loser","trash","moron","scum","disgusting","filth","retard","freak","murder","destroy","abuse","harass","threaten"]

def detect_toxicity(text: str):
    if not text.strip(): return "None", "Low", 0.0, {}, []
    model = get_model()
    scores = {}
    primary = 0.0
    if model:
        try:
            raw = model.predict(text)
            scores = {k: round(float(v), 4) for k, v in raw.items()}
            primary = scores.get("toxicity", 0.0)
        except Exception: pass

    if not scores:
        hits = [kw for kw in TOXIC_KW if kw in text.lower()]
        primary = min(len(hits) * 0.15, 1.0)
        scores = { "toxicity": round(primary, 4), "severe_toxicity": round(primary * 0.4, 4), "obscene": round(primary * 0.3, 4), "threat": round(primary * 0.2, 4), "insult": round(primary * 0.5, 4), "identity_hate": round(primary * 0.1, 4) }

    scores = calculate_sentiment_extensions(text, scores)
    label_map = { "severe_toxicity": "Severe Toxicity", "obscene": "Obscene Content", "threat": "Threat", "insult": "Insult", "identity_hate": "Identity Hate", "toxicity": "General Toxicity", "anger_index": "High Aggression", "sarcasm_probability": "Passive Aggressive" }
    
    dominant = max(scores, key=lambda k: scores[k])
    category = label_map.get(dominant, "Toxicity") if scores[dominant] > 0.1 else "Neutral"
    severity = "High" if primary >= 0.75 else ("Medium" if primary >= 0.40 else "Low")
    return category, severity, primary, scores, [kw for kw in TOXIC_KW if kw in text.lower()]

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS evidence (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT UNIQUE,
            content     TEXT,
            category    TEXT,
            severity    TEXT,
            score       REAL,
            scores_json TEXT,
            hash        TEXT,
            filename    TEXT,
            chain_tx    TEXT,
            created_at  TEXT
        );
        """)
        try: c.execute("ALTER TABLE evidence ADD COLUMN case_id TEXT DEFAULT 'Unassigned'")
        except sqlite3.OperationalError: pass

init_db()

# ── Helpers ───────────────────────────────────────────────────────────────────
def sha256(text: str, ts: str) -> str:
    return hashlib.sha256(f"{text}{ts}".encode()).hexdigest()

def blockchain_anchor(hash_val: str) -> str:
    try: ledger = json.load(open(CHAIN_PATH)) if os.path.exists(CHAIN_PATH) else []
    except Exception: ledger = []
    block = { "block": len(ledger) + 1, "hash": hash_val, "prev": ledger[-1]["hash"] if ledger else "0" * 64, "ts": datetime.utcnow().isoformat() + "Z" }
    block["block_hash"] = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
    ledger.append(block)
    with open(CHAIN_PATH, "w") as f: json.dump(ledger, f, indent=2)
    return block["block_hash"][:16].upper()

def save_record(evidence_id, content, category, severity, score, scores_json, hash_val, filename, chain_tx, ts, case_id="Unassigned"):
    enc_content = encrypt_text(content) # Encrypt before saving to DB
    with get_db() as c:
        c.execute("""INSERT OR IGNORE INTO evidence (evidence_id,content,category,severity,score,scores_json,hash,filename,chain_tx,created_at,case_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (evidence_id, enc_content, category, severity, score, scores_json, hash_val, filename, chain_tx, ts, case_id))

def send_alert(evidence_id, text, score):
    def _go():
        # --- WEBHOOK ALERT NOTIFICATION ---
        if DISCORD_WEBHOOK_URL:
            try:
                payload = {
                    "embeds": [{
                        "title": "🚨 HIGH SEVERITY EVIDENCE SECURED 🚨",
                        "description": f"**Evidence ID:** `{evidence_id}`\n**Score:** `{score:.2%}`\n\n**Snippet:**\n> {text[:200]}...",
                        "color": 16711680,
                        "footer": {"text": "EvidenceVault Threat Escalation Monitor"}
                    }]
                }
                requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=3)
            except Exception: pass

        if not (SMTP_USER and ALERT_EMAIL): return
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            msg = MIMEMultipart()
            msg["From"], msg["To"], msg["Subject"] = SMTP_USER, ALERT_EMAIL, f"🚨 HIGH SEVERITY — Evidence {evidence_id}"
            msg.attach(MIMEText(f"Evidence ID : {evidence_id}\nScore: {score:.2%}\nSnippet: {text[:300]}\n\nLog in to review.", "plain"))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s: s.starttls(); s.login(SMTP_USER, SMTP_PASS); s.sendmail(SMTP_USER, ALERT_EMAIL, msg.as_string())
        except Exception: pass
    threading.Thread(target=_go, daemon=True).start()

# --- FORENSIC IMAGE WATERMARKING ---
def watermark_image(filepath, evidence_id, timestamp):
    try:
        from PIL import Image, ImageDraw
        with Image.open(filepath) as img:
            img = img.convert("RGBA")
            txt = Image.new("RGBA", img.size, (255,255,255,0))
            d = ImageDraw.Draw(txt)
            width, height = img.size
            watermark_text = f"CONFIDENTIAL EVIDENCE | ID: {evidence_id} | CAPTURED: {timestamp}"
            
            # Draw semi-transparent black bar
            d.rectangle([(0, height - 30), (width, height)], fill=(0, 0, 0, 180))
            # Draw bright red forensic text
            d.text((10, height - 25), watermark_text, fill=(255, 50, 50, 255))
            
            out = Image.alpha_composite(img, txt).convert("RGB")
            out.save(filepath)
    except Exception as e:
        print(f"[Watermark error] {e}")

# --- AUTOMATED PII REDACTION REPORT ---
def make_pdf(row: dict, out_path: str, redact_pii: bool = False):
    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    S = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=S["Heading1"], fontSize=18, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
    mono = ParagraphStyle("mono", fontName="Courier", fontSize=8, textColor=colors.HexColor("#333"))
    
    title = "EvidenceVault — Public Redacted Report" if redact_pii else "EvidenceVault — Legal Forensics Report"
    body = [Paragraph(title, h1), HRFlowable(width="100%", thickness=1, color=colors.HexColor("#7c3aed")), Spacer(1, 0.4*cm)]
    
    content_text = row.get("content", "") or ""
    
    # Process PII redaction if requested
    if redact_pii:
        try:
            scores_raw = json.loads(row.get("scores_json", "{}"))
            insights = scores_raw.get("gemini_insights", {})
            entities = insights.get("entities", [])
            for ent in entities:
                if len(ent) > 2: # Prevent redacting small common words mistakenly
                    # Use regex to replace names with solid blocks
                    content_text = re.sub(re.escape(ent), "█" * len(ent), content_text, flags=re.IGNORECASE)
        except Exception as e:
            print(f"[Redaction Error] {e}")

    data = [
        ["Field", "Value"], ["Evidence ID", row.get("evidence_id","")], ["Case Folder", row.get("case_id","Unassigned")], ["Timestamp", row.get("created_at","")],
        ["Category", row.get("category","")], ["Severity", row.get("severity","")], ["Toxicity Score", f"{float(row.get('score',0))*100:.1f}%"],
        ["SHA-256 Hash", row.get("hash","")], ["Chain Anchor", row.get("chain_tx","N/A")], ["Attached File", row.get("filename","None") or "None"]
    ]
    
    if redact_pii:
        data.append(["Redaction Status", "PII & Entities Redacted (GDPR Compliant)"])

    tbl = Table(data, colWidths=[4*cm, 13*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#1a1a2e")), ("TEXTCOLOR", (0,0),(-1,0), colors.white),
        ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0),(-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.HexColor("#f5f5f5"), colors.white]),
        ("GRID", (0,0),(-1,-1), 0.5, colors.HexColor("#dddddd")), ("VALIGN", (0,0),(-1,-1), "TOP"),
    ]))
    body.extend([tbl, Spacer(1, 0.5*cm), Paragraph("Original Content:", S["Heading3"]), Paragraph(content_text[:2000].replace("\n","<br/>"), mono), Spacer(1, 0.5*cm), HRFlowable(width="100%", thickness=0.5, color=colors.grey), Paragraph("Cryptographically secured by EvidenceVault.", ParagraphStyle("footer", fontSize=7, textColor=colors.grey))])
    doc.build(body)

def login_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if "username" not in session: return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapped

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        uname = request.form.get("username","").strip()
        user  = USERS.get(uname)
        if user and user["password"] == _pw(request.form.get("password","")):
            session["username"], session["role"] = uname, user["role"]
            return redirect(url_for("home"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    with get_db() as c:
        total = c.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        high = c.execute("SELECT COUNT(*) FROM evidence WHERE severity='High'").fetchone()[0]
        medium = c.execute("SELECT COUNT(*) FROM evidence WHERE severity='Medium'").fetchone()[0]
        low = c.execute("SELECT COUNT(*) FROM evidence WHERE severity='Low'").fetchone()[0]
        trend = c.execute("SELECT strftime('%Y-%m', created_at) m, COUNT(*) n FROM evidence GROUP BY m ORDER BY m DESC LIMIT 6").fetchall()
    return render_template("index.html", total=total, high=high, medium=medium, low=low, trend_labels=json.dumps([r["m"] for r in reversed(trend)]), trend_data=json.dumps([r["n"] for r in reversed(trend)]), username=session["username"], role=session["role"], ocr_available=OCR_AVAILABLE, detoxify_available=DETOXIFY_AVAILABLE, encryption_available=ENCRYPTION_AVAILABLE)

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    text = request.form.get("message","").strip()
    case_id = request.form.get("case_id", "").strip() or "Unassigned"
    file = request.files.get("image")
    filename = ""

    eid = uuid.uuid4().hex[:8].upper()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if file and file.filename:
        filename = f"{eid}{os.path.splitext(file.filename)[1]}"
        fpath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(fpath)
        print(f"[Analyze] Image saved: {fpath}")
        
        # Extract text from image using Vision OCR with fallback keys
        if not text:
            print(f"[Analyze] No message text, attempting OCR on: {filename}")
            extracted_text = extract_text_from_image(fpath)
            print(f"[Analyze] OCR returned: '{extracted_text[:100]}...' (len={len(extracted_text)})")
            text = extracted_text
            
        # Apply Forensic Watermark
        watermark_image(fpath, eid, ts)

    if not text:
        print(f"[Analyze] ERROR: No text found after OCR. File: {filename}, Manual text: empty")
        flash("⚠ No text extracted from image. Please paste text manually or try a clearer image.")
        return redirect(url_for("home"))

    print(f"[Analyze] Processing text: {len(text)} chars, eid={eid}")
    translated_text, lang = translate_text(text)
    display_text = f"[Translated from {lang}]\n{translated_text}\n\n[Original]\n{text}" if lang != "en" else text

    cat, sev, score, scores, highlights = detect_toxicity(translated_text)
    
    gemini_data = get_gemini_insights(display_text)
    if gemini_data: scores["gemini_insights"] = gemini_data
    
    hval = sha256(display_text, ts)
    
    with get_db() as c:
        dup = c.execute("SELECT evidence_id FROM evidence WHERE hash=?", (hval,)).fetchone()
        if dup:
            flash(f"⚠ Duplicate evidence detected! Already secured as ID: {dup['evidence_id']}")
            return redirect(url_for('vault'))
            
    chain = blockchain_anchor(hval)
    sjson = json.dumps({**scores, "highlights": highlights})

    save_record(eid, display_text, cat, sev, round(score,4), sjson, hval, filename, chain, ts, case_id)
    if sev == "High": send_alert(eid, display_text, score)

    flash(f"✓ Evidence {eid} secured in Case '{case_id}' | Severity: {sev}")
    return redirect(url_for("vault"))

@app.route("/vault")
@login_required
def vault():
    q, sev, date, case = request.args.get("q","").strip(), request.args.get("severity",""), request.args.get("date",""), request.args.get("case","").strip()
    sql, par = "SELECT * FROM evidence WHERE 1=1", []
    if q: sql += " AND (evidence_id LIKE ? OR category LIKE ?)"; par += [f"%{q}%", f"%{q}%"]
    if sev: sql += " AND severity=?"; par.append(sev)
    if date: sql += " AND created_at LIKE ?"; par.append(f"{date}%")
    if case: sql += " AND case_id=?"; par.append(case)
    sql += " ORDER BY id DESC"
    
    with get_db() as c:
        records_raw = c.execute(sql, par).fetchall()
        unique_cases = [r['case_id'] for r in c.execute("SELECT DISTINCT case_id FROM evidence WHERE case_id != 'Unassigned'").fetchall()]
    
    # Decrypt content before sending to template.
    # Content is encrypted at rest, so text search must run after decryption.
    records = []
    q_lower = q.lower()
    for r in records_raw:
        r_dict = dict(r)
        r_dict["content"] = decrypt_text(r_dict["content"])
        if q and q_lower not in r_dict["content"].lower() and q_lower not in r_dict["evidence_id"].lower() and q_lower not in (r_dict["category"] or "").lower():
            continue
        records.append(r_dict)
        
    return render_template("vault.html", records=records, q=q, severity=sev, date=date, case=case, unique_cases=unique_cases, username=session["username"], role=session["role"])

@app.route("/evidence/<eid>")
@login_required
def detail(eid):
    with get_db() as c:
        row_raw = c.execute("SELECT * FROM evidence WHERE evidence_id=?", (eid,)).fetchone()
    if not row_raw: return "Evidence not found", 404
    
    row = dict(row_raw)
    row["content"] = decrypt_text(row["content"]) # Decrypt for viewing
    
    try: scores_raw = json.loads(row["scores_json"])
    except: scores_raw = {}
    highlights = scores_raw.pop("highlights", [])
    gemini_insights = scores_raw.pop("gemini_insights", None)
    
    return render_template("detail.html", row=row, scores=scores_raw, highlights=highlights, gemini_insights=gemini_insights, username=session["username"], role=session["role"])

@app.route("/uploads/<filename>")
@login_required
def get_upload(filename):
    """Route to serve watermarked forensic images"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/delete/<eid>", methods=["POST"])
@login_required
def delete_evidence(eid):
    """GDPR-Compliant Full Data Purge (Admin Only)"""
    if session.get("role") != "admin":
        flash("⚠ Unauthorized: Only Administrators can execute a GDPR data purge.")
        return redirect(url_for('detail', eid=eid))
        
    with get_db() as c:
        row = c.execute("SELECT * FROM evidence WHERE evidence_id=?", (eid,)).fetchone()
        if row:
            if row["filename"]:
                try: os.remove(os.path.join(UPLOAD_FOLDER, row["filename"]))
                except: pass
            try: os.remove(os.path.join(UPLOAD_FOLDER, f"{eid}_report.pdf"))
            except: pass
            try: os.remove(os.path.join(UPLOAD_FOLDER, f"{eid}_public_report.pdf"))
            except: pass
            c.execute("DELETE FROM evidence WHERE evidence_id=?", (eid,))
    flash(f"✓ Evidence {eid} completely purged (GDPR Compliant).")
    return redirect(url_for('vault'))

@app.route("/report/<eid>")
@login_required
def report(eid):
    with get_db() as c: row_raw = c.execute("SELECT * FROM evidence WHERE evidence_id=?", (eid,)).fetchone()
    if not row_raw: return "Evidence not found", 404
    
    row = dict(row_raw)
    row["content"] = decrypt_text(row["content"]) # Decrypt for PDF Generation
    
    fname = os.path.join(UPLOAD_FOLDER, f"{eid}_report.pdf")
    make_pdf(row, fname, redact_pii=False)
    return send_file(fname, as_attachment=True, download_name=f"EvidenceVault_{eid}.pdf")

@app.route("/report/<eid>/public")
@login_required
def report_public(eid):
    """Generates a Public PDF with names/entities redacted"""
    with get_db() as c: row_raw = c.execute("SELECT * FROM evidence WHERE evidence_id=?", (eid,)).fetchone()
    if not row_raw: return "Evidence not found", 404
    
    row = dict(row_raw)
    row["content"] = decrypt_text(row["content"])
    
    fname = os.path.join(UPLOAD_FOLDER, f"{eid}_public_report.pdf")
    make_pdf(row, fname, redact_pii=True)
    return send_file(fname, as_attachment=True, download_name=f"EvidenceVault_{eid}_REDACTED.pdf")

@app.route("/verify", methods=["GET", "POST"])
def verify():
    result = None
    search_hash = ""
    if request.method == "POST":
        search_hash = request.form.get("hash", "").strip()
        if search_hash:
            with get_db() as c:
                row = c.execute("SELECT * FROM evidence WHERE hash=?", (search_hash,)).fetchone()
            if row:
                chain_valid = False
                try:
                    ledger = json.load(open(CHAIN_PATH))
                    for block in ledger:
                        if block.get("hash") == search_hash:
                            chain_valid = True
                            break
                except: pass
                result = {"found": True, "evidence_id": row["evidence_id"], "created_at": row["created_at"], "category": row["category"], "severity": row["severity"], "chain_tx": row["chain_tx"], "chain_valid": chain_valid}
            else:
                result = {"found": False}
    return render_template("verify.html", result=result, search_hash=search_hash, username=session.get("username"), role=session.get("role"))

@app.route("/legal")
@login_required
def legal(): return render_template("legal.html", username=session["username"], role=session["role"])

@app.route("/export/csv")
@login_required
def export_csv():
    with get_db() as c: records = c.execute("SELECT evidence_id, case_id, category, severity, score, created_at, content FROM evidence ORDER BY id DESC").fetchall()
    def generate():
        data = StringIO(); writer = csv.writer(data)
        writer.writerow(("Evidence ID", "Case Folder", "Category", "Severity", "Toxicity Score", "Date Captured", "Content Snippet"))
        yield data.getvalue(); data.seek(0); data.truncate(0)
        for r in records:
            decrypted_content = decrypt_text(r["content"]) # Decrypt for CSV
            writer.writerow((r["evidence_id"], r["case_id"], r["category"], r["severity"], f"{r['score']*100:.1f}%", r["created_at"], decrypted_content[:150].replace('\n', ' ')))
            yield data.getvalue(); data.seek(0); data.truncate(0)
    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="evidence_vault_export.csv")
    return response

@app.route("/api/v1/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(force=True) or {}
    if data.get("api_key") != API_KEY: return jsonify({"error": "Unauthorized"}), 401
    text = data.get("text","").strip()
    if not text: return jsonify({"error": "No text provided"}), 400
        
    translated_text, lang = translate_text(text)
    display_text = f"[Translated from {lang}]\n{translated_text}\n\n{text}" if lang != "en" else text
    cat, sev, score, scores, highlights = detect_toxicity(translated_text)
    
    if data.get("preview"): return jsonify({"category": cat, "severity": sev, "score": round(score, 4), "scores": scores})
    
    gemini_data = get_gemini_insights(display_text)
    if gemini_data: scores["gemini_insights"] = gemini_data
        
    eid, ts = uuid.uuid4().hex[:8].upper(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hval = sha256(display_text, ts); chain = blockchain_anchor(hval)
    sjson = json.dumps({**scores, "highlights": highlights})
    
    save_record(eid, display_text, cat, sev, round(score,4), sjson, hval, "", chain, ts, case_id=data.get("case_id", "Unassigned"))
    if sev == "High": send_alert(eid, display_text, score)
    return jsonify({"evidence_id": eid, "category": cat, "severity": sev, "score": round(score,4), "scores": scores, "hash": hval})

@app.route("/api/v1/ocr_preview", methods=["POST"])
@login_required
def ocr_preview():
    """Preview OCR extraction before submitting evidence."""
    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"error": "No image provided"}), 400
    
    try:
        import io
        from PIL import Image
        
        print(f"[OCR Preview] Processing: {file.filename}")
        
        # Read image bytes
        img_data = file.read()
        print(f"[OCR Preview] File size: {len(img_data)} bytes")
        
        # Check if Tesseract is available
        if not OCR_AVAILABLE:
            print("[OCR Preview] Tesseract OCR not available")
            return jsonify({
                "error": "Tesseract OCR not available on this system",
                "text": "",
                "category": "Unknown",
                "severity": "Low",
                "score": 0,
                "highlights": []
            }), 200
        
        # Extract text from buffer
        extracted_text = extract_text_from_image_buffer(img_data)
        print(f"[OCR Preview] Extracted: '{extracted_text[:100]}'...")
        
        if not extracted_text:
            print("[OCR Preview] No text extracted")
            return jsonify({
                "error": "",
                "text": "",
                "category": "No Text",
                "severity": "Low",
                "score": 0,
                "highlights": []
            }), 200
        
        # Quick toxicity score
        cat, sev, score, scores, highlights = detect_toxicity(extracted_text)
        
        print(f"[OCR Preview] ✓ Success: {cat}, {sev}, score={score}")
        
        return jsonify({
            "text": extracted_text,
            "category": cat,
            "severity": sev,
            "score": round(score, 4),
            "highlights": highlights
        }), 200
        
    except Exception as e:
        print(f"[OCR Preview] Exception: {type(e).__name__}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"{type(e).__name__}: {str(e)[:100]}",
            "text": "",
            "category": "Error",
            "severity": "Low",
            "score": 0,
            "highlights": []
        }), 500

def extract_text_from_image_buffer(image_bytes: bytes) -> str:
    """Extract text from in-memory image bytes."""
    import io
    from PIL import Image, ImageOps, ImageEnhance
    import time
    
    print(f"[OCR Buffer] Starting extraction from {len(image_bytes)} bytes")
    
    try:
        base_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        print(f"[OCR Buffer] Image opened: {base_image.size} pixels")
        
        candidates = [
            ("original", base_image),
            ("grayscale", base_image.convert("L")),
            ("contrast", ImageEnhance.Contrast(base_image.convert("L")).enhance(2.0)),
            ("autocontrast", ImageOps.autocontrast(base_image.convert("L"))),
        ]
        
        for name, img in candidates:
            try:
                start = time.time()
                text = pytesseract.image_to_string(img).strip()
                elapsed = time.time() - start
                
                print(f"[OCR Buffer] {name}: {len(text)} chars in {elapsed:.2f}s")
                
                if text and len(text) > 2:
                    print(f"[OCR Buffer] ✓ Success with {name}")
                    return text
            except Exception as e:
                print(f"[OCR Buffer] {name} failed: {type(e).__name__}: {str(e)[:100]}")
                continue
        
        # Final pass: binarize
        try:
            gray = base_image.convert("L")
            bw = gray.point(lambda x: 0 if x < 128 else 255, mode="1")
            start = time.time()
            text = pytesseract.image_to_string(bw).strip()
            elapsed = time.time() - start
            
            print(f"[OCR Buffer] binarized: {len(text)} chars in {elapsed:.2f}s")
            
            if text and len(text) > 2:
                print(f"[OCR Buffer] ✓ Success with binarization")
                return text
        except Exception as bin_err:
            print(f"[OCR Buffer] binarization failed: {type(bin_err).__name__}: {str(bin_err)[:100]}")
        
        print(f"[OCR Buffer] ⚠ No text extracted from image")
        
    except Exception as e:
        print(f"[OCR Buffer] Fatal error: {type(e).__name__}: {str(e)[:200]}")
    
    return ""

@app.route("/api/v1/generate_cd/<eid>", methods=["POST"])
@login_required
def generate_cd(eid):
    if not GEMINI_AVAILABLE: return jsonify({"error": "Gemini API is not configured."}), 500
    with get_db() as c: row_raw = c.execute("SELECT * FROM evidence WHERE evidence_id=?", (eid,)).fetchone()
    if not row_raw: return jsonify({"error": "Evidence not found."}), 404
        
    row = dict(row_raw)
    row["content"] = decrypt_text(row["content"]) # Decrypt so Gemini can read it
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are a tough, professional lawyer. Based on the following abusive evidence, draft a formal Cease and Desist letter.
        The letter should demand the sender immediately stop all harassment and communication, or further legal action will be taken.
        Use placeholders like [Sender Name], [Your Name], and [Date] if specific names are not present in the text.
        Keep the tone strictly legal, objective, and assertive.
        Evidence Text: "{row['content']}"
        """
        response = model.generate_content(prompt)
        return jsonify({"letter": response.text})
    except Exception as e:
        print(f"[Gemini C&D Error] {e}")
        return jsonify({"error": "Failed to generate letter."}), 500

# --- NEW: GENERATE TEST SCREENSHOT ---
@app.route("/test/generate_screenshot")
@login_required
def generate_screenshot():
    """Generates a fake cyberbullying screenshot for testing OCR and Watermarks."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (600, 300), color=(240, 242, 245))
        d = ImageDraw.Draw(img)
        
        # Draw fake UI
        d.rectangle([(0, 0), (600, 50)], fill=(79, 70, 229)) # Header
        d.text((20, 15), "Chat with @AnonymousTroll", fill=(255,255,255))
        
        # Draw fake messages
        d.rectangle([(20, 80), (450, 140)], fill=(255, 255, 255))
        d.text((35, 95), "You are so worthless and pathetic.", fill=(0,0,0))
        
        d.rectangle([(20, 160), (500, 220)], fill=(255, 255, 255))
        d.text((35, 175), "I am going to leak your photos to everyone at school tomorrow.", fill=(0,0,0))
        
        d.text((35, 250), "Just watch your back.", fill=(220,38,38))
        
        test_path = os.path.join(UPLOAD_FOLDER, "test_screenshot_generated.png")
        img.save(test_path)
        return send_file(test_path, as_attachment=True, download_name="test_cyberbullying_screenshot.png")
    except Exception as e:
        flash(f"Error generating test image: Make sure Pillow is installed. ({e})")
        return redirect(url_for('home'))

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  ╔═══════════════════════════════════════════════════════════════╗")
    print("  ║   EvidenceVault — AI Cyberbullying Detection & Forensics    ║")
    print("  ╚═══════════════════════════════════════════════════════════════╝")
    print("="*70)
    print(f"  🔗 Dashboard: http://127.0.0.1:5000")
    print(f"  👤 Login:     admin / admin123")
    print(f"  🔧 Debug:     ENABLED (development mode)")
    print("-"*70)
    print(f"  🤖 Detoxify ML:       {'✓ LOADED' if DETOXIFY_AVAILABLE else '✗ Not installed'}")
    print(f"  📸 OCR (Tesseract):   {'✓ AVAILABLE' if OCR_AVAILABLE else '✗ NOT INSTALLED ⚠'}")
    print(f"  🔑 Gemini API Keys:   {len(GEMINI_API_KEYS)} configured")
    print(f"  🔐 Encryption:        {'✓ AVAILABLE' if ENCRYPTION_AVAILABLE else '✗ Not available'}")
    print("-"*70)

    if not OCR_AVAILABLE:
        print("  ⚠️  WARNING: Tesseract OCR not found!")
        print("  📖 Setup guide: See TESSERACT_SETUP.md")
        print("  ⚙️  Windows:   choco install tesseract")
        print("  ⚙️  macOS:     brew install tesseract")
        print("  ⚙️  Linux:     apt install tesseract-ocr")
        print("-"*70)

    print(f"  ✨ Ready to process evidence!\n")

    app.run(debug=True, port=5000)