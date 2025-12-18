from flask import Flask, request, jsonify
from fuzzywuzzy import fuzz
import requests
import re
import urllib.parse
import os

app = Flask(__name__)

# --- الإعدادات (تأكد من صحتها) ---
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"
WHATSAPP_NUMBER = "201090636076"

def clean_arabic_text(text):
    if not text: return ""
    text = text.strip().lower()
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r'[^\w\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

# --- قاعدة البيانات الشاملة بنظام الكلمات المفتاحية ---
FAQ = [
    {
        'keywords': ['منيو', 'اسعار', 'بكام', 'سعر', 'قائمه', 'فسيخ', 'رنجه', 'تونه', 'بطارخ', 'ملوحه', 'سردين', 'اصناف'],
        'answer': "أهلاً بك! تفضل المنيو المحدث بجميع الأصناف والأسعار:\nhttps://heyzine.com/flip-book/31946f16d5.html"
    },
    {
        'keywords': ['توصيل', 'دليفري', 'شحن', 'يوصل', 'قاهره', 'اسكندريه', 'محافظات', 'عنوان'],
        'answer': "التوصيل متاح لـ (بورسعيد، القاهرة، إسكندرية، الغردقة). للطلبات كلمنا على: 01212166660."
    },
    {
        'keywords': ['غالي', 'السعر مرتفع', 'اوفر', 'اسعاركم زادت'],
        'answer': "نحن نضمن لك جودة عالمية؛ تمليح بمحلول براين وتدخين على البارد بنشارة ألماني لضمان منتج صحي وآمن وجاهز للأكل مباشرة."
    },
    {
        'keywords': ['دود', 'طفيليات', 'حاجه غريبه', 'بايظه', 'دودت'],
        'answer': "دي طفيليات طبيعية في التجويف البطني ولا تصيب الإنسان. نحن نجمد الأسماك عند -40 درجة لضمان الأمان التام."
    },
    {
        'keywords': ['مواعيد', 'بتفتحوا', 'الساعه كام', 'شغالين', 'وقت'],
        'answer': "فروعنا مفتوحة يومياً من الساعة 10 صباحاً وحتى 12 منتصف الليل."
    },
    {
        'keywords': ['فاكيوم', 'مغلف', 'مفرغ', 'تغليف'],
        'answer': "تغليف الفاكيوم يعني سحب الهواء تماماً من العبوة للحفاظ على الطعم والجودة ومنع البكتيريا."
    },
    {
        'keywords': ['تصدير', 'خارج مصر', 'شحن دولي', 'احمد'],
        'answer': "لطلبات التصدير، تواصل مع أستاذ أحمد (واتساب): 01272475555"
    },
    {
        'keywords': ['جمله', 'كميات', 'مصنع', 'مطعم', 'توزيع'],
        'answer': "لطلبات الجملة والمصنع، يرجى الاتصال بـ: 01211113882"
    },
    {
        'keywords': ['حسابات', 'الشماع', 'فاتوره', 'فلوس'],
        'answer': "أستاذ محمد الشماع (مدير الحسابات): 01204464066"
    },
    {
        'keywords': ['شغل', 'توظيف', 'اتش ار', 'hr', 'وظائف'],
        'answer': "للتواصل مع إدارة الـ HR ببورسعيد: 01200056103"
    },
    # يمكنك إضافة الـ 40 سؤال الباقية بنفس هذا النمط (كلمات دلالية قصيرة)
]

def get_answer(user_question):
    q = clean_arabic_text(user_question)
    
    # تحيات سريعة
    if any(word in q for word in ['سلام', 'هلو', 'ازيك', 'صباح', 'مساء', 'يا']):
        return "أهلاً بك في رنجة أبو السيد، كيف يمكننا مساعدتك اليوم؟"

    best_answer = None
    max_matches = 0

    # نظام البحث بالكلمات المفتاحية (أقوى من الجمل الكاملة)
    for item in FAQ:
        matches = 0
        for kw in item['keywords']:
            clean_kw = clean_arabic_text(kw)
            # إذا كانت الكلمة المفتاحية موجودة داخل رسالة العميل
            if clean_kw in q or fuzz.partial_ratio(clean_kw, q) > 85:
                matches += 1
        
        if matches > max_matches:
            max_matches = matches
            best_answer = item['answer']

    if best_answer:
        return best_answer
    else:
        encoded_msg = urllib.parse.quote(f"استفسار: {user_question}")
        return f"لم أفهم طلبك بدقة، يمكنك التواصل معنا مباشرة عبر الواتساب:\nhttps://wa.me/{WHATSAPP_NUMBER}?text={encoded_msg}"

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args["hub.challenge"], 200
        return "Verification token mismatch", 403
    return "Bot is Online", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
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
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    requests.post(url, json=payload)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
