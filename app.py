from flask import Flask, request
from fuzzywuzzy import fuzz
import requests
import re
import os

app = Flask(__name__)

# ================== الإعدادات ==================
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"
WHATSAPP_NUMBER = "201090636076"
MENU_LINK = "https://heyzine.com/flip-book/31946f16d5.html"

# ================== ذاكرة ==================
USER_CONTEXT = {}  # user_id -> last_product

# ================== أدوات ==================
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

def is_price_question(q):
    return any(x in q for x in ["سعر", "بكام", "كام", "قد ايه", "عامل كام"])

def is_greeting(q):
    greetings = ["السلام عليكم", "السلام", "اهلا", "أهلا", "ازيك", "هاي", "هلا"]
    return any(g == q or g in q for g in greetings)

# ================== المنتجات ==================
PRODUCTS = [
       # الرنجة
    {'kw': ['رنجه مدخنه مبطرخه مرمله', 'رنجه مبطرخه', 'رنجه مرمله'], 'price': '250 EGP', 'w': '1 KG'},
    {'kw': ['رنجه مدخنه', 'رنجه عاديه'], 'price': '200 EGP', 'w': '1 KG'},
    {'kw': ['رنجه مدخنه 24 قيراط', 'رنجه 24', 'رنجه عيار 24'], 'price': '300 EGP', 'w': '1 KG'},
    {'kw': ['رنجه 24 مبطرخه', 'رنجه 24 مرمله'], 'price': '320 EGP', 'w': '1 KG'},
    {'kw': ['رنجه منزوعه الاحشاء فاكيوم', 'رنجه فاكيوم'], 'price': '300 EGP', 'w': '1 KG'},
    {'kw': ['رنجه فيليه بدون زيت', 'رنجه فيليه ساده'], 'price': '600 EGP', 'w': '1 KG'},
    {'kw': ['رنجه فيليه صوص فلفل وكافيار'], 'price': '150 EGP', 'w': '200 G'},
    {'kw': ['رنجه فيليه كاري'], 'price': '250 EGP', 'w': '250 G'},
    {'kw': ['رنجه فيليه زيت'], 'price': '250 EGP', 'w': '250 G'},
    {'kw': ['رنجه فيليه مدخنه'], 'price': '85 EGP', 'w': '125 G'},
    {'kw': ['كافيار سبريد', 'رنجه كافيار سبريد'], 'price': '70 EGP', 'w': '200 G/130 G'},
    {'kw': ['بطارخ رنجه زيت كاملة'], 'price': '250 EGP', 'w': '250 G'},
    {'kw': ['بطارخ رنجه برتقال', 'بطارخ مهروسه'], 'price': '250 EGP', 'w': '250 G'},
    # الماكريل
    {'kw': ['ماكريل مدخن مملح', 'ماكريل'], 'price': '410 EGP', 'w': '1 KG'},
    {'kw': ['ماكريل فاكيوم'], 'price': '460 EGP', 'w': '1 KG'},
    {'kw': ['ماكريل فيليه'], 'price': '800 EGP', 'w': '1 KG'},
    # الفسيخ
    {'kw': ['فسيخ فيليه زيت', 'فسيخ زيت'], 'price': '250 EGP', 'w': '250 G'},
    {'kw': ['فسيخ فيليه دخان', 'فسيخ مدخن'], 'price': '250 EGP', 'w': '250 G'},
    {'kw': ['فسيخ سبريد بنجر'], 'price': '250 EGP', 'w': '250 G'},
    {'kw': ['فسيخ بدون بكتيريا', 'فسيخ طبي'], 'price': '460 EGP', 'w': '1 KG'},
    {'kw': ['فسيخ مبطرخ'], 'price': '560 EGP', 'w': '1 KG'},
    {'kw': ['شرائح بوري مدخنه', 'فيليه بوري مدخن'], 'price': '810 EGP', 'w': '1 KG'},
    # السلمون
    {'kw': ['سلمون حار', 'spicy salmon'], 'price': '150 EGP', 'w': '125 G'},
    {'kw': ['شرائح سلمون مدخنه', 'سلمون فيليه'], 'price': '3000 EGP', 'w': '1 KG'},
    {'kw': ['ستيك سلمون'], 'price': '1810 EGP', 'w': '1 KG'},
    {'kw': ['شوربه سلمون'], 'price': '90 EGP', 'w': '160 G'},
    # البطارخ والتونة
    {'kw': ['بطارخ بوري مملحه', 'بطارخ بوري'], 'price': '2850 EGP', 'w': '1 KG'},
    {'kw': ['تونه حمراء فيليه', 'تونه حمرا'], 'price': '155 EGP', 'w': '230 G'},
    {'kw': ['تونه قطع', ' chunks tuna'], 'price': '70 EGP', 'w': '125 G'},
    {'kw': ['تونه مطهيه'], 'price': '710 EGP', 'w': '1 KG'},
    # أخرى
    {'kw': ['انشوجه فيليه زيت', 'انشوجه'], 'price': '110 EGP', 'w': '125 G'},
    {'kw': ['سردين مملح'], 'price': '200 EGP', 'w': '250 G'},
    {'kw': ['حنشان مدخن', 'تعبان مدخن'], 'price': '810 EGP', 'w': '1 KG'}
]

# ================== منتجات مرتبطة ==================
def get_related_products(user_text):
    related = []
    for p in PRODUCTS:
        for kw in p['kw']:
            if smart_similarity(clean_arabic_text(user_text), clean_arabic_text(kw)) >= 75:
                related.append(p)
                break
    return related

# ================== المنطق ==================
def get_answer(user_id, text):
    q = clean_arabic_text(text)

    # 1️⃣ السلام
    if is_greeting(q):
        return {"text": "أهلاً بحضرتك 🌹 ", "qr": None}

    # 2️⃣ رقم فقط (تأكيد اختيار)
    if q.isdigit() and user_id in USER_CONTEXT:
        p = USER_CONTEXT[user_id]
        return {
            "text": f"📌 {p['kw'][0]}\n💰 السعر: {p['price']}\n⚖️ الوزن: {p['w']}",
            "qr": None
        }

    # 3️⃣ سؤال سعر
    if is_price_question(q):
        related = get_related_products(q)

        if not related and user_id in USER_CONTEXT:
            p = USER_CONTEXT[user_id]
            return {
                "text": f"📌 {p['kw'][0]}\n💰 السعر: {p['price']}\n⚖️ الوزن: {p['w']}",
                "qr": None
            }

        if len(related) == 1:
            USER_CONTEXT[user_id] = related[0]
            p = related[0]
            return {
                "text": f"📌 {p['kw'][0]}\n💰 السعر: {p['price']}\n⚖️ الوزن: {p['w']}",
                "qr": None
            }

        if len(related) > 1:
            qr = []
            for p in related[:10]:
                qr.append({
                    "content_type": "text",
                    "title": p['kw'][0][:20],
                    "payload": f"PRICE|{PRODUCTS.index(p)}"
                })
            return {
                "text": "تمام 👍 تقصد أنهي نوع بالظبط؟",
                "qr": qr
            }

        return {"text": "تحب تعرف سعر أنهي صنف؟ 😊", "qr": None}

    # 4️⃣ ذكر منتج بدون سعر
    related = get_related_products(q)
    if len(related) == 1:
        USER_CONTEXT[user_id] = related[0]
        return {
            "text": f"📌 {related[0]['kw'][0]}\nتحب تعرف السعر؟ 💰",
            "qr": None
        }

    # 5️⃣ غير مفهوم
    return {
        "text": "ممكن توضح أكتر يا فندم؟ 😊",
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
            msg = msg_event.get("message", {})

            if "quick_reply" in msg:
                payload = msg["quick_reply"]["payload"]
                if payload.startswith("PRICE"):
                    idx = int(payload.split("|")[1])
                    p = PRODUCTS[idx]
                    USER_CONTEXT[sender] = p
                    send_message(
                        sender,
                        f"📌 {p['kw'][0]}\n💰 السعر: {p['price']}\n⚖️ الوزن: {p['w']}"
                    )

            elif "text" in msg:
                res = get_answer(sender, msg["text"])
                send_message(sender, res["text"], res.get("qr"))

    return "ok", 200

def send_message(user_id, text, quick_replies=None):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": text}
    }
    if quick_replies:
        payload["message"]["quick_replies"] = quick_replies
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
