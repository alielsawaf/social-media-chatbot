from flask import Flask, request, send_file, abort
from fuzzywuzzy import fuzz
import requests
import re
import os
from datetime import datetime
import csv
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

app = Flask(__name__)

# ================== الإعدادات ==================
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"
MENU_LINK = "https://heyzine.com/flip-book/31946f16d5.html"

FUZZY_THRESHOLD = 70
CSV_FILE = os.path.join(os.path.dirname(__file__), "failed_questions.csv")
CSV_PASSWORD = "123321"

PRICE_WORDS = [
    'سعر','بكام','كام','عامل','تكلفه','ثمن','قيمة','سعره','الاسعار',
    'كم','هل عندكم','عايز','من فضلك','لو سمحت','حابب','عايزه','اريد'
]
GENERAL_TRIGGERS = [
    'منيو','المينيو','عايز المنيو','ابعت المنيو','بتبيعو ايه','ايه المنتجات',
    'ايه اللي عندكم','لو سمحت','اريد','من فضلك'
]
GREETINGS = [
    'اهلا','سلام','هاي','هلا','مرحبا','صباح الخير','مساء الخير',
    'صباح الفل','مساء الفل','يا فندم','يا حضرة','يا أستاذ'
]

# ================== تحميل نموذج NLP ==================
tokenizer = AutoTokenizer.from_pretrained("aubmindlab/bert-base-arabertv02")
model = AutoModelForSequenceClassification.from_pretrained("aubmindlab/bert-base-arabertv02")

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
    for w in PRICE_WORDS + ['بتبيعو','عندكو','ازاي','ممكن','عايز']:
        text = text.replace(w, "")
    return text.strip()

def similarity(a, b):
    return fuzz.token_set_ratio(a, b)

def log_failed(question):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["question", "created_at"])
        writer.writerow([question, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

def split_user_text(text):
    parts = re.split(r"[.؟!,؛]", text)
    return [p.strip() for p in parts if p.strip()]

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

FAQ = [
  {'keywords': ['دود', 'طفيليات', 'الرنجه فيها'], 'answer': "لا يا فندم، دي طفيليات مش دود. بتوجد في التجويف البطني ولا تصيب الإنسان، وبيتم القضاء عليها بالتجميد عند -40 درجة لضمان الأمان."},
   {'keywords': ['ساندوتشات', 'سلطات', 'وجبات'], 'answer': "منيو الساندوتشات والسلطات غير متاح حاليًا ولا يوجد توصيل لها."},
   {'keywords': ['اصليه', 'ازاي اعرف', 'كرتونه'], 'answer': "رنجة أبو السيد بتكون في كراتين مش صناديق خشب، ويُفضّل الشراء من فروعنا الرسمية."},
   {'keywords': ['توصيل', 'دليفري', 'شحن'], 'answer': "التوصيل متاح في: (القاهرة، بورسعيد، الإسكندرية، الغردقة). للطلبات: 01212166660."},
   {'keywords': ['جمله', 'تجار'], 'answer': "للاستفسار عن الجملة فقط: 01211113882"},
   {'keywords': ['تسخين', 'نار', 'اسخن'], 'answer': "لا يا فندم، المنتج جاهز للأكل مباشرة ولا يفضل تعرضه لأي حرارة."},
   {'keywords': ['فرق', 'مجمده', 'فريش'], 'answer': "المجمدة: -18 / صلاحية 3 شهور. الفريش: من 0 لـ 4 / صلاحية شهر."},
   {'keywords': ['مواد حافظه', 'طبيعي'], 'answer': "كل منتجاتنا طبيعية 100% وبدون أي مواد حافظة."},
   {'keywords': ['مواعيد', 'بتفتحوا'], 'answer': "يوميًا من 10 صباحًا إلى 12 منتصف الليل."},
   {'keywords': ['شغل', 'توظيف', 'مندوب'], 'answer': "للوظائف بالقاهرة: 01210188882 (واتساب + اتصال)"},
   {'keywords': ['تصدير', 'خارج مصر'], 'answer': "للتصدير: 01272475555 أ/ أحمد."},
   {'keywords': ['موارد بشريه', 'hr'], 'answer': "إدارة الـ HR: 01200056103"},
   {'keywords': ['منيو', 'اسعاركم', 'بكام'], 'answer': f"أهلاً بك! تفضل المنيو الكامل بالأسعار من هنا:\n{MENU_LINK}"}
]

# ================== تحليل النص بالـ NLP ==================
def analyze_text(user_text):
    text = clean_arabic_text(user_text)
    intent = None
    product_name = None
    matches = []
    
    # البحث عن المنتجات باستخدام Fuzzy
    for p in PRODUCTS:
        for kw in p['kw']:
            if similarity(text, clean_arabic_text(kw)) >= FUZZY_THRESHOLD:
                matches.append(p)
                break
    
    if matches:
        intent = "ask_price"
        product_name = matches
    else:
        for item in FAQ:
            for kw in item['keywords']:
                if kw in text or similarity(text, clean_arabic_text(kw)) >= FUZZY_THRESHOLD:
                    intent = "faq"
                    product_name = item['answer']
                    break
    
    if not intent and any(w in text for w in GREETINGS):
        intent = "greeting"
    
    return intent, product_name

def get_answer(user_text):
    intent, data = analyze_text(user_text)
    
    if intent == "ask_price":
        matches = data
        if len(matches) > 1:
            quick_replies = []
            for m in matches[:10]:
                quick_replies.append({
                    "content_type": "text",
                    "title": m['kw'][0][:20],
                    "payload": f"PRODUCT_INDEX|{PRODUCTS.index(m)}"
                })
            return {"text": "حضرتك تقصد أي منتج بالظبط؟", "quick_replies": quick_replies}
        else:
            p = matches[0]
            return {"text": f"✔️ {p['kw'][0]}\n💰 {p['price']}\n⚖️ {p['w']}", "quick_replies": None}
    
    elif intent == "faq":
        return {"text": data, "quick_replies": None}
    
    elif intent == "greeting":
        return {"text": "أهلاً بحضرتك 👋", "quick_replies": None}
    
    else:
        log_failed(user_text)
        return {"text": f"مش فاهم حضرتك قوي 😅\n📖 المنيو:\n{MENU_LINK}", "quick_replies": None}

def process_long_message(user_text):
    parts = split_user_text(user_text)
    responses = []
    for part in parts:
        ans = get_answer(part)
        if ans['text'] not in [r['text'] for r in responses]:
            responses.append(ans)
    return responses

# ================== Webhook ==================
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
                
                if "message" in msg_event and "quick_reply" in msg_event["message"]:
                    payload = msg_event["message"]["quick_reply"]["payload"]
                    if payload.startswith("PRODUCT_INDEX|"):
                        idx = int(payload.split("|")[1])
                        p = PRODUCTS[idx]
                        reply_text = f"✔️ المنتج متوفر\n📌 {p['kw'][0]}\n💰 السعر: {p['price']}\n⚖️ الوزن: {p['w']}"
                        send_message(sender, reply_text)
                
                elif "message" in msg_event and "text" in msg_event["message"]:
                    user_text = msg_event["message"]["text"]
                    responses = process_long_message(user_text)
                    for res in responses:
                        send_message(sender, res["text"], res.get("quick_replies"))
                    
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

# ================== تحميل CSV ==================
@app.route('/download_csv')
def download_csv():
    if request.args.get("password") != CSV_PASSWORD:
        return abort(403)
    if not os.path.isfile(CSV_FILE):
        return "لا يوجد ملف بعد"
    return send_file(CSV_FILE, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
