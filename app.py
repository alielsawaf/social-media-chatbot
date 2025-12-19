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

FUZZY_THRESHOLD = 70  # نسبة الفهم المسموح بها

# ================== أدوات مساعدة ==================
def clean_arabic_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text)

def similarity(a, b):
    return fuzz.token_set_ratio(a, b)

# ================== المنتجات ==================
PRODUCTS = [
    {'name': 'رنجه مدخنه', 'kw': ['رنجه', 'رنجه مدخنه'], 'price': '200 EGP', 'w': '1 KG'},
    {'name': 'رنجه 24', 'kw': ['رنجه 24', 'عيار 24'], 'price': '300 EGP', 'w': '1 KG'},
    {'name': 'رنجه فاكيوم', 'kw': ['رنجه فاكيوم', 'منزوعه الاحشاء'], 'price': '300 EGP', 'w': '1 KG'},
    {'name': 'فسيخ طبي', 'kw': ['فسيخ طبي', 'بدون بكتيريا'], 'price': '460 EGP', 'w': '1 KG'},
    {'name': 'ماكريل مدخن', 'kw': ['ماكريل'], 'price': '410 EGP', 'w': '1 KG'},
]

# ================== FAQ ==================
FAQ = [
    {
        'q': ['دود', 'طفيليات', 'الرنجه فيها'],
        'a': "دي طفيليات طبيعية لا تصيب الإنسان، وبيتم القضاء عليها بالتجميد -40 درجة."
    },
    {
        'q': ['توصيل', 'دليفري', 'شحن'],
        'a': "التوصيل متاح (القاهرة – بورسعيد – الإسكندرية – الغردقة)."
    },
    {
        'q': ['منيو', 'اسعار'],
        'a': f"تفضل المنيو الكامل:\n{MENU_LINK}"
    }
]

# ================== منطق الرد ==================
def get_answer(user_text):
    q = clean_arabic_text(user_text)

    # ---------- البحث في المنتجات ----------
    best_match = None
    best_score = 0

    for p in PRODUCTS:
        for kw in p['kw']:
            score = similarity(q, clean_arabic_text(kw))
            if score > best_score:
                best_score = score
                best_match = p

    if best_match and best_score >= FUZZY_THRESHOLD:
        return (
            f"✔️ المنتج متوفر\n"
            f"📌 {best_match['name']}\n"
            f"💰 السعر: {best_match['price']}\n"
            f"⚖️ الوزن: {best_match['w']}\n\n"
            f"المنيو الكامل:\n{MENU_LINK}"
        )

    # ---------- البحث في FAQ ----------
    for item in FAQ:
        for q_kw in item['q']:
            if similarity(q, clean_arabic_text(q_kw)) >= FUZZY_THRESHOLD:
                return item['a']

    # ---------- تحيات ----------
    if any(w in q for w in ['اهلا', 'سلام', 'هاي', 'ازيك']):
        return "أهلاً بحضرتك 👋 ممكن أعرف حضرتك عايز تستفسر عن ايه؟"

    # ---------- رد آمن ----------
    return (
        "معلش يا فندم، ممكن توضح طلبك أكتر؟\n"
        f"📖 المنيو الكامل:\n{MENU_LINK}\n"
        f"📲 واتساب خدمة العملاء:\nhttps://wa.me/{WHATSAPP_NUMBER}"
    )

# ================== Webhook ==================
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    for entry in data.get("entry", []):
        for msg in entry.get("messaging", []):
            if "text" in msg.get("message", {}):
                sender = msg["sender"]["id"]
                reply = get_answer(msg["message"]["text"])
                send_message(sender, reply)
    return "ok"

def send_message(user_id, text):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": user_id}, "message": {"text": text}}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

