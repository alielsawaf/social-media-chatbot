from flask import Flask, request, send_file, abort
from fuzzywuzzy import fuzz
import requests
import re
import os
from datetime import datetime
import csv

app = Flask(__name__)

# ================== الإعدادات ==================
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"
WHATSAPP_NUMBER = "201090636076"
MENU_LINK = "https://heyzine.com/flip-book/31946f16d5.html"

FUZZY_THRESHOLD = 65  # خفضناه قليلاً لزيادة المرونة مع الصيغ الصعبة
CSV_FILE = os.path.join(os.path.dirname(__file__), "failed_questions.csv")

# كلمات الحشو اللي بنشيلها عشان نركز على "صلب" السؤال
STOP_WORDS = ['يا', 'غالي', 'بقولك', 'ممكن', 'اعرف', 'كنت', 'عايز', 'حابب', 'لو', 'سمحت', 'عندكم', 'بكام', 'سعر']

# ================== أدوات مساعدة متطورة ==================
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

def advanced_clean(text):
    """تنظيف عميق لاستخراج اسم المنتج فقط"""
    t = clean_arabic_text(text)
    words = t.split()
    # إزالة كلمات الحشو
    filtered = [w for w in words if w not in STOP_WORDS]
    return " ".join(filtered) if filtered else t

def get_similarity(user_text, target_text):
    """حساب التشابه بأكثر من خوارزمية لضمان الدقة"""
    s1 = fuzz.token_set_ratio(user_text, target_text) # بيفهم لو الكلمات متلخبطة
    s2 = fuzz.partial_ratio(user_text, target_text)  # بيفهم لو الكلمة جزء من جملة رغي
    return max(s1, s2)

# ================== المنتجات والأسئلة (نفس بياناتك) ==================
# ... (ضع قائمة PRODUCTS و FAQ الخاصة بك هنا) ...
# لضمان عمل الكود، وضعت عينة صغيرة، استبدلها ببياناتك كاملة
PRODUCTS = [
    {'kw': ['رنجه مدخنه مبطرخه مرمله', 'رنجه مبطرخه', 'رنجه مرمله'], 'price': '250 EGP', 'w': '1 KG'},
    {'kw': ['فسيخ فيليه زيت', 'فسيخ زيت'], 'price': '250 EGP', 'w': '250 G'},
    # أضف باقي القائمة هنا...
]

FAQ = [
    {'keywords': ['توصيل', 'دليفري', 'شحن'], 'answer': "التوصيل متاح في: (القاهرة، بورسعيد، الإسكندرية، الغردقة). للطلبات: 01212166660."},
    {'keywords': ['منيو', 'اسعاركم', 'بكام'], 'answer': f"أهلاً بك! تفضل المنيو الكامل بالأسعار من هنا:\n{MENU_LINK}"}
]

# ================== منطق الرد الذكي ==================
def get_answer(user_text):
    raw_clean = clean_arabic_text(user_text)
    prod_clean = advanced_clean(user_text)

    # 1. المنيو العام
    if any(w in raw_clean for w in ['منيو', 'المينيو', 'كتالوج']):
        return {"text": f"📖 تفضل المنيو الكامل بجميع الأصناف والأسعار:\n{MENU_LINK}", "quick_replies": None}

    # 2. البحث عن المنتجات (القلب الذكي للبوت)
    matches = []
    for p in PRODUCTS:
        highest_score = 0
        for kw in p['kw']:
            score = get_similarity(prod_clean, clean_arabic_text(kw))
            highest_score = max(highest_score, score)
        
        if highest_score >= FUZZY_THRESHOLD:
            matches.append((p, highest_score))

    # ترتيب النتائج حسب الأعلى تشابهاً
    matches = sorted(matches, key=lambda x: x[1], reverse=True)

    if len(matches) > 1:
        # لو فيه تشابه قوي جداً مع منتج واحد (أعلى من 90) نختاره هو
        if matches[0][1] > 90:
            p = matches[0][0]
            return {"text": f"✔️ {p['kw'][0]}\n💰 {p['price']}\n⚖️ {p['w']}", "quick_replies": None}
        
        # غير كدة نطلع خيارات
        qr = []
        for m, score in matches[:10]:
            qr.append({
                "content_type": "text",
                "title": m['kw'][0][:20],
                "payload": f"PRODUCT_INDEX|{PRODUCTS.index(m)}"
            })
        return {"text": "حضرتك تقصد أي منتج بالظبط من دول؟", "quick_replies": qr}

    if len(matches) == 1:
        p = matches[0][0]
        return {"text": f"✔️ {p['kw'][0]}\n💰 {p['price']}\n⚖️ {p['w']}", "quick_replies": None}

    # 3. FAQ
    for item in FAQ:
        if any(get_similarity(raw_clean, clean_arabic_text(kw)) >= 80 for kw in item['keywords']):
            return {"text": item['answer'], "quick_replies": None}

    # 4. فشل الفهم
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([user_text, datetime.now().isoformat()])
    
    return {"text": f"للاسف مش فاهم حضرتك قوي 😅.. بس تقدر تعرف كل حاجة من المنيو هنا:\n{MENU_LINK}", "quick_replies": None}

# ================== Webhook والوظائف الأخرى (نفس كودك المستقر) ==================
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for msg_event in entry.get("messaging", []):
                sender = msg_event["sender"]["id"]
                if "message" in msg_event:
                    msg = msg_event["message"]
                    if "quick_reply" in msg:
                        payload = msg["quick_reply"]["payload"]
                        if payload.startswith("PRODUCT_INDEX|"):
                            p = PRODUCTS[int(payload.split("|")[1])]
                            send_message(sender, f"📌 {p['kw'][0]}\n💰 السعر: {p['price']}\n⚖️ الوزن: {p['w']}")
                    elif "text" in msg:
                        # تقسيم الجمل الطويلة لزيادة الفهم
                        parts = re.split(r"[.؟!,؛]", msg["text"])
                        for part in parts:
                            if len(part.strip()) > 2:
                                res = get_answer(part)
                                send_message(sender, res["text"], res.get("quick_replies"))
    return "ok", 200

def send_message(user_id, text, quick_replies=None):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": user_id}, "message": {"text": text}}
    if quick_replies: payload["message"]["quick_replies"] = quick_replies
    requests.post(url, json=payload)

@app.route('/download_csv')
def download_csv():
    if request.args.get("password") == "123321":
        return send_file(CSV_FILE, as_attachment=True) if os.path.exists(CSV_FILE) else "No Data"
    abort(403)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
