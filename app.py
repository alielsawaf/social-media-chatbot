from flask import Flask, request
from fuzzywuzzy import fuzz
import requests
import re
import os

app = Flask(__name__)

# ================== الإعدادات ==================
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"

# ================== ذاكرة المحادثة ==================
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

# ================== السلام ==================
SMART_GREETINGS = {
    "صباح": "صباح النور يا فندم 🌞",
    "مساء": "مساء النور يا فندم 🌙",
    "السلام": "وعليكم السلام ورحمة الله 🤍",
    "ازيك": "أهلاً بحضرتك 🌹",
    "اهلا": "أهلاً وسهلاً 👋",
    "هاي": "أهلاً 👋"
}

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

]

# ================== INTENTS ==================
INTENTS = [
    {
        "name": "hours",
        "examples": [
            "مواعيد الفروع","الفروع شغاله","شغالين لحد امتي"
        ],
        "answer": "🕙 مواعيد فروعنا من 10 صباحاً حتى 12 منتصف الليل"
    },
    {
        "name": "smoking24",
        "examples": ["رنجه 24","عيار 24","24"],
        "answer": (
            "رنجة عيار 24:\n"
            "✔️ عدد ساعات التدخين اطول\n"
            "✔️ حجم السمكة أصغر\n"
            "✔️ طعم التدخين أقوى"
        ),
        "product_ref": "رنجه عيار 24"
    }
]

# ================== استخراج Intent ==================
def detect_intent(text):
    best = None
    score = 0
    for intent in INTENTS:
        for ex in intent["examples"]:
            s = smart_similarity(text, clean_arabic_text(ex))
            if s > score and s >= 75:
                score = s
                best = intent
    return best

# ================== استخراج منتجات ==================
def get_related_products(text):
    related = []
    for p in PRODUCTS:
        for kw in p['kw']:
            if smart_similarity(text, clean_arabic_text(kw)) >= 70:
                related.append(p)
                break
    return related

# ================== منطق الرد ==================
def get_answer(user_id, text):
    q = clean_arabic_text(text)

    # 1️⃣ سلام
    for k, v in SMART_GREETINGS.items():
        if k in q:
            return {"text": v, "qr": None}

    # 2️⃣ سؤال سعر (أعلى أولوية)
    if any(x in q for x in ['سعر','بكام','قد ايه','كام']):

        related = get_related_products(q)

        # رجوع لآخر منتج
        if not related and user_id in USER_CONTEXT:
            p = USER_CONTEXT[user_id]
            return {
                "text": f"📌 {p['kw'][0]}\n💰 السعر: {p['price']}\n⚖️ الوزن: {p['w']}",
                "qr": None
            }

        # منتج واحد
        if len(related) == 1:
            USER_CONTEXT[user_id] = related[0]
            p = related[0]
            return {
                "text": f"📌 {p['kw'][0]}\n💰 السعر: {p['price']}\n⚖️ الوزن: {p['w']}",
                "qr": None
            }

        return {"text": "تحب تعرف سعر أنهي صنف؟ 😊", "qr": None}

    # 3️⃣ Intent
    intent = detect_intent(q)
    if intent:

        # تخزين المنتج لو موجود
        if "product_ref" in intent:
            for p in PRODUCTS:
                if intent["product_ref"] in p["kw"][0]:
                    USER_CONTEXT[user_id] = p
                    break

        return {"text": intent["answer"], "qr": None}

    # 4️⃣ ذكر منتج
    related = get_related_products(q)
    if len(related) == 1:
        USER_CONTEXT[user_id] = related[0]
        return {
            "text": f"تمام 👍 تحب تعرف السعر ولا عندك استفسار عن:\n📌 {related[0]['kw'][0]}",
            "qr": None
        }

    return {"text": "ممكن توضح استفسارك أكتر؟ 😊", "qr": None}

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
