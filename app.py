from flask import Flask, request, jsonify
from fuzzywuzzy import fuzz
import requests
import re
import urllib.parse
import os

app = Flask(__name__)

# --------------------------------------------------------------------------------
# ⚠️ الإعدادات - تأكد من مطابقتها لإعدادات Facebook Developers
# --------------------------------------------------------------------------------
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"  # يجب أن يكون مطابقاً للـ Verify Token في فيسبوك
WHATSAPP_NUMBER = "201090636076"

# --------------------------------------------------------------------------------
# دالة معالجة النصوص العربية
# --------------------------------------------------------------------------------
def clean_arabic_text(text):
    if not text: return ""
    text = text.strip().lower()
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r'[^\w\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

# --------------------------------------------------------------------------------
# قاعدة البيانات الذكية (FAQ)
# --------------------------------------------------------------------------------
FAQ = [
    {'questions': ['الاسعار غاليه', 'ليه غالي', 'غالي اوي'], 'answer': "أهلاً بك، نحن نضمن لك جودة عالمية؛ تمليح بمحلول براين وتدخين على البارد بنشارة ألماني لضمان منتج صحي وآمن."},
    {'questions': ['المنيو', 'الاسعار كام', 'بكام الرنجه', 'عايز اشتري'], 'answer': "تفضل لينك المنيو المحدث بجميع الأسعار: https://heyzine.com/flip-book/31946f16d5.html"},
    {'questions': ['التوصيل', 'دليفري', 'شحن', 'بتوصلوا فين'], 'answer': "التوصيل متاح لـ (بورسعيد، القاهرة، إسكندرية، الغردقة). للطلبات: 01212166660."},
    {'questions': ['دود في الرنجه', 'طفيليات', 'حاجه غريبه في البطن'], 'answer': "هذه طفيليات طبيعية في الأمعاء ولا تضر الإنسان، ونحن نجمد الأسماك عند -40 درجة لضمان الأمان التام."},
    {'questions': ['يعني ايه فاكيوم', 'تغليف فاكيوم'], 'answer': "الفاكيوم هو تغليف مفرغ من الهواء تماماً للحفاظ على المنتج طازجاً ولذيذًا لأطول فترة."},
    {'questions': ['مواعيد العمل', 'بتفتحوا امتى', 'الساعه كام'], 'answer': "فروعنا مفتوحة يومياً من الساعة 10 صباحاً وحتى 12 منتصف الليل."},
    {'questions': ['التصدير', 'تلفون التصدير'], 'answer': "لطلبات التصدير، يرجى التواصل مع أستاذ أحمد (واتساب): 01272475555"},
    {'questions': ['مدير الحسابات', 'الشماع'], 'answer': "أستاذ محمد الشماع (مدير الحسابات): 01204464066"},
    {'questions': ['التوظيف', 'شغل', 'اتش ار'], 'answer': "للتواصل مع إدارة الـ HR ببورسعيد: 01200056103"},
    {'questions': ['جمله', 'طلب كبير', 'المصنع'], 'answer': "لطلبات الجملة والمصنع، يرجى الاتصال بـ: 01211113882"}
]

# --------------------------------------------------------------------------------
# منطق الرد الذكي
# --------------------------------------------------------------------------------
def get_answer(user_question):
    q = clean_arabic_text(user_question)
    
    # الرد على التحيات
    if any(word in q for word in ['سلام', 'هلو', 'ازيك', 'صباح', 'مساء']):
        return "أهلاً بك في رنجة أبو السيد، كيف يمكننا مساعدتك اليوم؟"

    best_score = 0
    selected_answer = None

    for item in FAQ:
        for question_key in item['questions']:
            score = fuzz.token_set_ratio(q, clean_arabic_text(question_key))
            if score > best_score:
                best_score = score
                selected_answer = item['answer']

    if best_score >= 70:
        return selected_answer
    else:
        encoded_msg = urllib.parse.quote(f"استفسار: {user_question}")
        return f"لم أفهم طلبك بدقة، يمكنك التواصل معنا مباشرة عبر الواتساب:\nhttps://wa.me/{WHATSAPP_NUMBER}?text={encoded_msg}"

# --------------------------------------------------------------------------------
# المسارات (Routes) - تم تعديلها إلى /webhook لحل خطأ 404
# --------------------------------------------------------------------------------
@app.route('/webhook', methods=['GET'])
def verify():
    # التحقق من الربط مع فيسبوك
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args["hub.challenge"], 200
        return "Verification token mismatch", 403
    return "Hello Bot Running", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    # طباعة البيانات في اللوج للتأكد من وصولها
    print(f"Incoming Data: {data}")
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    text = messaging_event["message"].get("text")
                    if text:
                        response = get_answer(text)
                        send_message(sender_id, response)
    return "ok", 200

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post(url, json=payload)
    print(f"Facebook Response: {response.status_code} - {response.text}")

if __name__ == '__main__':
    # استخدام بورت 8080 وهو المفضل لمنصة Railway و Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
