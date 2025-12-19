from flask import Flask, request
from fuzzywuzzy import fuzz
import requests
import re
import os
from datetime import datetime
import pyodbc
print("Available ODBC Drivers:", pyodbc.drivers())
app = Flask(__name__)
# ================== الإعدادات ==================
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"
WHATSAPP_NUMBER = "201090636076"
MENU_LINK = "https://heyzine.com/flip-book/31946f16d5.html"

FUZZY_THRESHOLD = 70
FAILED_LOG = "failed_questions.log"

PRICE_WORDS = ['سعر', 'بكام', 'كام', 'عامل', 'تكلفه', 'ثمن', 'قيمة', 'سعره', 'الاسعار']

# ================== إعداد الاتصال بالـ SQL Server ==================
SQL_SERVER = "212.129.20.85"
SQL_DB = "bot_db"
SQL_USER = "bot_user"
SQL_PASS = "Aa#123456789#"

conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DB};"
    f"UID={SQL_USER};"
    f"PWD={SQL_PASS};"
    "TrustServerCertificate=yes;"
    "Timeout=5;" # مهلة الاتصال 5 ثوانٍ
)

def get_db_connection():
    """فتح اتصال جديد بالقاعدة"""
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")
        return None

# ================== أدوات مساعدة ==================
def normalize_numbers(text):
    return text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))

def clean_arabic_text(text):
    if not text: return ""
    text = normalize_numbers(text.lower().strip())
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text)

def clean_for_product(text):
    text = clean_arabic_text(text)
    for w in PRICE_WORDS:
        text = text.replace(w, "")
    return text.strip()

def similarity(a, b):
    return fuzz.token_set_ratio(a, b)

def log_failed(question):
    try:
        with open(FAILED_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} | {question}\n")
    except:
        pass

# ================== جلب البيانات من قاعدة البيانات ==================
def get_products():
    products = []
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, description, price FROM products")
            rows = cursor.fetchall()
            for r in rows:
                products.append({
                    'kw': [r[0]],
                    'price': r[2],
                    'w': r[1] or ""
                })
        except Exception as e:
            print(f"❌ Query Error (Products): {e}")
        finally:
            conn.close()
    return products

def get_faq():
    faq_list = []
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT question, answer FROM faqs")
            rows = cursor.fetchall()
            for r in rows:
                faq_list.append({
                    'keywords': [r[0]],
                    'answer': r[1]
                })
        except Exception as e:
            print(f"❌ Query Error (FAQ): {e}")
        finally:
            conn.close()
    return faq_list

# ================== منطق الرد ==================
def get_answer(user_text):
    # جلب البيانات الحديثة عند كل رسالة
    PRODUCTS = get_products()
    FAQ = get_faq()
    
    q_original = clean_arabic_text(user_text)
    q_product = clean_for_product(user_text)

    # 1. فحص إذا كان السؤال عن المنيو فقط
    if q_original in PRICE_WORDS or q_original.strip() == "سعر":
        return f"تفضل المنيو الكامل بالأسعار:\n{MENU_LINK}"

    # 2. البحث عن المنتجات
    matches = []
    for p in PRODUCTS:
        for kw in p['kw']:
            score = similarity(q_product, clean_arabic_text(kw))
            if score >= FUZZY_THRESHOLD:
                matches.append(p)
                break

    if len(matches) > 1:
        names = [m['kw'][0] for m in matches]
        return "حضرتك تقصد أي منتج بالظبط؟\n" + "\n".join(f"- {n}" for n in names)

    if len(matches) == 1:
        p = matches[0]
        return (
            f"✔️ المنتج متوفر\n"
            f"📌 {p['kw'][0]}\n"
            f"💰 السعر: {p['price']}\n"
            f"⚖️ الوزن: {p['w']}\n\n"
            f"📖 المنيو الكامل:\n{MENU_LINK}"
        )

    # 3. البحث في الأسئلة الشائعة
    for item in FAQ:
        for kw in item['keywords']:
            if similarity(q_original, clean_arabic_text(kw)) >= FUZZY_THRESHOLD:
                return item['answer']

    # 4. التحيات
    if any(w in q_original for w in ['اهلا', 'سلام', 'هاي', 'ازيك']):
        return "أهلاً بحضرتك 👋 ممكن أعرف تحب تستفسر عن ايه؟"

    log_failed(user_text)
    return (
        "معلش يا فندم، مش قادر أفهم طلبك بدقة.\n"
        f"📖 المنيو الكامل:\n{MENU_LINK}\n"
        f"📲 واتساب خدمة العملاء:\nhttps://wa.me/{WHATSAPP_NUMBER}"
    )

# ================== Webhook ==================
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and data.get("object") == "page":
        for entry in data.get("entry", []):
            for msg in entry.get("messaging", []):
                if "text" in msg.get("message", {}):
                    sender = msg["sender"]["id"]
                    reply = get_answer(msg["message"]["text"])
                    send_message(sender, reply)
    return "ok", 200

def send_message(user_id, text):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": user_id}, "message": {"text": text}}
    try:
        r = requests.post(url, json=payload)
        print(f"FB Status: {r.status_code}")
    except Exception as e:
        print(f"Send Error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

