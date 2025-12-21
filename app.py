from flask import Flask, request
from fuzzywuzzy import fuzz
import requests
import re
import os

app = Flask(__name__)

# ================== الإعدادات ==================
PAGE_ACCESS_TOKEN = "PUT_YOUR_TOKEN"
VERIFY_TOKEN = "my_secret_token"
WHATSAPP_NUMBER = "201090636076"
MENU_LINK = "https://heyzine.com/flip-book/31946f16d5.html"

# ================== ذاكرة محادثة مؤقتة ==================
USER_CONTEXT = {}  # user_id -> last_product

# ================== أدوات اللغة ==================
def clean_arabic_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text)

def smart_similarity(a, b):
    return max(
        fuzz.token_set_ratio(a, b),
        fuzz.partial_ratio(a, b)
    )

# ================== سلام ذكي ==================
SMART_GREETINGS = {
    "صباح": "صباح النور يا فندم 🌞",
    "مساء": "مساء النور يا فندم 🌙",
    "السلام": "وعليكم السلام ورحمة الله 🤍",
    "ازيك": "أهلاً بحضرتك 🌹 عامل ايه؟",
    "اهلا": "أهلاً وسهلاً بحضرتك 👋",
    "هاي": "أهلاً بيك 👋"
}

# ================== المنتجات ==================
PRODUCTS = [
    {'kw': ['رنجه مدخنه'], 'price': '200 EGP', 'w': '1 KG'},
    {'kw': ['رنجه 24'], 'price': '300 EGP', 'w': '1 KG'},
    {'kw': ['فسيخ طبي'], 'price': '460 EGP', 'w': '1 KG'},
    {'kw': ['ماكريل'], 'price': '410 EGP', 'w': '1 KG'},
]

# ================== FAQ ==================
FAQ = [
    {
        'keywords': ['دود', 'طفيليات'],
        'answer': "دي مش دود يا فندم، دي طفيليات طبيعية في التجويف البطني ومش بتضر الإنسان نهائياً."
    },
    {
        'keywords': ['فاكيوم'],
        'answer': "فاكيوم يعني مفرغ هواء عشان يحافظ على جودة المنتج."
    }
]

# ================== المنطق الذكي ==================
def get_answer(user_id, text):
    q = clean_arabic_text(text)

    # 1️⃣ رد السلام الذكي
    for k, v in SMART_GREETINGS.items():
        if k in q:
            return {"text": v, "qr": None}

    # 2️⃣ سؤال سعر مباشر
    if any(x in q for x in ['بكام', 'سعر', 'قد ايه']):
        last = USER_CONTEXT.get(user_id)
        if last:
            return {
                "text": f"📌 {last['kw'][0]}\n💰 السعر: {last['price']}\n⚖️ الوزن: {last['w']}",
                "qr": None
            }
        else:
            return {
                "text": "تحب تعرف سعر أنهي صنف بالظبط؟ 😊",
                "qr": None
            }

    # 3️⃣ FAQ
    for f in FAQ:
        for kw in f['keywords']:
            if smart_similarity(q, kw) > 80:
                return {"text": f['answer'], "qr": None}

    # 4️⃣ البحث عن منتج
    matches = []
    for p in PRODUCTS:
        for kw in p['kw']:
            if smart_similarity(q, clean_arabic_text(kw)) > 85:
                matches.append(p)
                break

    if len(matches) == 1:
        USER_CONTEXT[user_id] = matches[0]
        return {
            "text": f"تمام 👍 تحب تعرف السعر ولا عندك استفسار عن:\n📌 {matches[0]['kw'][0]}",
            "qr": None
        }

    if len(matches) > 1:
        return {
            "text": "تقصد أنهي نوع فيهم يا فندم؟ 😊",
            "qr": None
        }

    # 5️⃣ غير مفهوم
    return {
        "text": (
            "تحب أوضح لحضرتك 👍\n"
            "هل سؤالك عن:\n"
            "💰 السعر؟\n"
            "❓ ولا استفسار عن منتج؟\n\n"
             f"📱 واتساب الطلبات: {WHATSAPP_NUMBER}"
        ),
        "qr": None
    }

# ================== Webhook ==================
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    for entry in data.get("entry", []):
        for msg_event in entry.get("messaging", []):
            sender = msg_event["sender"]["id"]
            if "message" in msg_event and "text" in msg_event["message"]:
                res = get_answer(sender, msg_event["message"]["text"])
                send_message(sender, res["text"])
    return "ok", 200

def send_message(user_id, text):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": user_id}, "message": {"text": text}}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
