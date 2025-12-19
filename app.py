from flask import Flask, request
from fuzzywuzzy import fuzz
import requests
import re
import os
from datetime import datetime

app = Flask(__name__)

# ================== الإعدادات ==================
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"
WHATSAPP_NUMBER = "201090636076"
MENU_LINK = "https://heyzine.com/flip-book/31946f16d5.html"

FUZZY_THRESHOLD = 70
FAILED_LOG = "failed_questions.log"

PRICE_WORDS = [
    'سعر', 'بكام', 'كام', 'عامل', 'تكلفه', 'ثمن',
    'قيمة', 'سعره', 'الاسعار'
]

# ================== أدوات مساعدة ==================
def normalize_numbers(text):
    return text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))

def clean_arabic_text(text):
    if not text:
        return ""
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
    with open(FAILED_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {question}\n")

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
    {'kw': ['حنشان مدخن', 'تعبان مدخن'], 'price': '810 EGP', 'w': '1 KG'},
]

# ================== FAQ ==================
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

# ================== منطق الرد ==================
def get_answer(user_text):
    q_original = clean_arabic_text(user_text)
    q_product = clean_for_product(user_text)

    # ---------- سعر بس ----------
    if q_original in PRICE_WORDS or q_original.strip() == "سعر":
        return f"تفضل المنيو الكامل بالأسعار:\n{MENU_LINK}"

    # ---------- البحث عن المنتجات ----------
    matches = []

    for p in PRODUCTS:
        for kw in p['kw']:
            score = similarity(q_product, clean_arabic_text(kw))
            if score >= FUZZY_THRESHOLD:
                matches.append(p)
                break

    # ---------- أكتر من منتج ----------
    if len(matches) > 1:
        names = [m['kw'][0] for m in matches]
        return "حضرتك تقصد أي منتج بالظبط؟\n" + "\n".join(f"- {n}" for n in names)

    # ---------- منتج واحد ----------
    if len(matches) == 1:
        p = matches[0]
        return (
            f"✔️ المنتج متوفر\n"
            f"📌 {p['kw'][0]}\n"
            f"💰 السعر: {p['price']}\n"
            f"⚖️ الوزن: {p['w']}\n\n"
            f"📖 المنيو الكامل:\n{MENU_LINK}"
        )

    # ---------- FAQ ----------
    for item in FAQ:
        for kw in item['keywords']:
            if similarity(q_original, clean_arabic_text(kw)) >= FUZZY_THRESHOLD:
                return item['answer']

    # ---------- تحيات ----------
    if any(w in q_original for w in ['اهلا', 'سلام', 'هاي', 'ازيك']):
        return "أهلاً بحضرتك 👋 ممكن أعرف تحب تستفسر عن ايه؟"

    # ---------- فشل ----------
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

