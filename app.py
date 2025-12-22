from flask import Flask, request
from fuzzywuzzy import fuzz
import requests
import re
import os

app = Flask(__name__)

# ================== الإعدادات ==================
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"
WHATSAPP_NUMBER = "01090636076"

# ================== ذاكرة محادثة ==================
USER_CONTEXT = {}  # user_id -> last_product OR last_products_list

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

# ================== سلام ==================
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

# ================== INTENTS ==================
INTENTS = [
    {
        "name": "hours",
        "examples": [
            "مواعيد الفروع","الفروع شغاله لحد امتي","الفروع شغاله للساعه كام"
        ],
        "answer": (
            "أهلا بحضرتك 🌹\n"
            "🕙 مواعيد فروعنا من 10 صباحاً حتى 12 منتصف الليل"
        )
    },
    {
        "name": "export",
        "examples": ["التصدير","رقم التصدير","مسئول التصدير"],
        "answer": (
            "أهلا بحضرتك 🌹\n"
            "ده رقم أ/ أحمد مسئول التصدير واتساب:\n"
            "📱 01272475555"
        )
    },
    {
        "name": "purchases",
        "examples": ["المشتريات","رقم المشتريات","ادارة المشتريات"],
        "answer": (
            "أهلا بحضرتك 🌹\n"
            "📱 رقم إدارة المشتريات: 01223066445"
        )
    },
    {
        "name": "hr",
        "examples": ["hr","الاتش ار","وظائف","التوظيف"],
        "answer": (
            "أهلا بحضرتك 🌹\n"
            "📱 رقم HR بورسعيد: 01200056103"
        )
    },
    {
        "name": "smoking24",
        "examples": ["رنجه 24","عيار 24","الفرق بين الرنجة"],
        "answer": (
            "رنجة عيار 24:\n"
            "✔️  عدد ساعات التدخين اطول\n"
            "✔️ حجم السمكة أصغر\n"
            "✔️ طعم التدخين أقوى"
        )
    }
]

# ================== استخراج نية ==================
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
def get_related_products(user_text):
    related = []
    for p in PRODUCTS:
        for kw in p['kw']:
            if kw.split()[0] in user_text or smart_similarity(user_text, kw) >= 65:
                related.append(p)
                break
    return related

# ================== منطق الرد ==================
def get_answer(user_id, text):
    q = clean_arabic_text(text)

    # 1️⃣ السلام
    for k, v in SMART_GREETINGS.items():
        if k in q:
            return {"text": v, "qr": None}

    # 2️⃣ سؤال سعر (أعلى أولوية)
    if any(x in q for x in ['سعر','بكام','قد ايه','كام']):

        # حاول نطلع منتجات من السؤال
        related = get_related_products(q)

        # لو مفيش منتجات في السؤال → رجوع لآخر منتج
        if not related and user_id in USER_CONTEXT:
            p = USER_CONTEXT[user_id]
            return {
                "text": (
                    f"📌 {p['kw'][0]}\n"
                    f"💰 السعر: {p['price']}\n"
                    f"⚖️ الوزن: {p['w']}"
                ),
                "qr": None
            }

        # منتج واحد واضح
        if len(related) == 1:
            USER_CONTEXT[user_id] = related[0]
            p = related[0]
            return {
                "text": (
                    f"📌 {p['kw'][0]}\n"
                    f"💰 السعر: {p['price']}\n"
                    f"⚖️ الوزن: {p['w']}"
                ),
                "qr": None
            }

        # أكتر من منتج → أزرار
        if len(related) > 1:
            USER_CONTEXT[user_id] = related
            quick_replies = []
            for p in related[:10]:
                quick_replies.append({
                    "content_type": "text",
                    "title": p['kw'][0][:20],
                    "payload": f"PRICE|{PRODUCTS.index(p)}"
                })
            return {
                "text": "تحب أنهي نوع بالظبط؟ 👇",
                "qr": quick_replies
            }

        return {"text": "تحب تعرف سعر أنهي صنف؟ 😊", "qr": None}

    # 3️⃣ INTENTS (بعد السعر)
    intent = detect_intent(q)
    if intent:
        return {"text": intent["answer"], "qr": None}

    # 4️⃣ ذكر منتج بدون سعر
    related = get_related_products(q)
    if len(related) == 1:
        USER_CONTEXT[user_id] = related[0]
        return {
            "text": f"تمام 👍 تحب تعرف السعر ولا عندك استفسار عن:\n📌 {related[0]['kw'][0]}",
            "qr": None
        }

    # 5️⃣ غير مفهوم
    return {
        "text": "ممكن توضح استفسارك أكتر يا فندم؟ 😊",
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

            if "message" in msg_event:
                msg = msg_event["message"]

                if "quick_reply" in msg:
                    payload = msg["quick_reply"]["payload"]
                    if payload.startswith("PRICE"):
                        idx = int(payload.split("|")[1])
                        p = PRODUCTS[idx]
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

