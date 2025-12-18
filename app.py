from flask import Flask, request, jsonify
from fuzzywuzzy import fuzz
import requests
import re
import urllib.parse
import os

app = Flask(__name__)

# --- الإعدادات (تأكد من مطابقتها لحسابك) ---
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

# --- قاعدة البيانات الكاملة لجميع أسئلتك ---
FAQ = [
    {
        'keywords': ['منيو', 'اسعار', 'بكام', 'سعر', 'قائمه', 'فسيخ', 'رنجه', 'تونه', 'بطارخ', 'ملوحه', 'سردين', 'اصناف', 'نظامكم'],
        'answer': "أهلاً بك! تفضل المنيو المحدث بجميع الأصناف والأسعار من هنا:\nhttps://heyzine.com/flip-book/31946f16d5.html"
    },
    {
        'keywords': ['دود', 'طفيليات', 'حاجه غريبه', 'بايظه', 'الرنجه فيها'],
        'answer': "لا يا فندم، دي طفيليات مش دود. الطفيليات بتوجد في التجويف البطني للسمكة بشكل طبيعي، ولا تصيب الإنسان، وبيتم القضاء عليها تماماً بالتجميد العميق عند -40 درجة قبل البيع."
    },
    {
        'keywords': ['ساندوتشات', 'سلطات', 'وجبات', 'سندوتش', 'سلطه'],
        'answer': "منيو الساندوتشات والسلطات غير متاح حاليًا للأسف، ولا يوجد خدمة توصيل لها في الوقت الحالي."
    },
    {
        'keywords': ['اصليه', 'ازاي اعرف', 'التقليد', 'كرتونه', 'صناديق', 'خشب'],
        'answer': "رنجة أبو السيد الأصلية بتكون في كراتين مش صناديق خشب، ويُفضّل دائماً الشراء من فروعنا الرسمية أو مصادر موثوقة لضمان الجودة."
    },
    {
        'keywords': ['توصيل', 'دليفري', 'شحن', 'بتوصلوا فين', 'محافظات', 'عنوانكم'],
        'answer': "التوصيل متاح في: (القاهرة، بورسعيد، الإسكندرية، الغردقة). للطلبات يرجى الاتصال على رقم الدليفري: 01212166660."
    },
    {
        'keywords': ['جمله', 'تجار', 'كميات', 'مصنع', 'مطعم', 'توزيع'],
        'answer': "للاستفسار عن طلبات الجملة فقط، يرجى التواصل مع المصنع مباشرة على رقم: 01211113882"
    },
    {
        'keywords': ['تسخين', 'اسخن', 'نار', 'بوتاجاز', 'سخنه', 'تتطبخ', 'اشوي'],
        'answer': "لا يا فندم، المنتج جاهز للأكل مباشرة (Ready to eat) ولا يفضل تعرضه لأي حرارة حتى لا يتغير طعمه أو جودته."
    },
    {
        'keywords': ['فرق', 'مجمده', 'فريش', 'صلاحيه', 'احفظها ازاي'],
        'answer': "المجمدة: تُحفظ في الفريزر عند -18 وصلاحيتها 3 شهور.\nالفريش: تُحفظ في الثلاجة من 0 لـ 4 درجات وصلاحيتها شهر واحد."
    },
    {
        'keywords': ['وزن', 'كيلو', 'الكرتونه كام', 'حجم الكرتونه'],
        'answer': "وزن كرتونة الرنجة المجمدة يتراوح من 7.5 إلى 8 كيلو تقريباً (متاحة قطاعي وليس جملة)."
    },
    {
        'keywords': ['عيار 24', 'الفرق بين', 'العاديه وعيار'],
        'answer': "رنجة عيار 24 تتميز بتدخين لفترة أطول، حجم السمكة يكون أصغر قليلاً، وطعم التدخين فيها أقوى ومركز أكثر."
    },
    {
        'keywords': ['مواد حافظه', 'طبيعي', 'كيماوي'],
        'answer': "كل منتجات أبو السيد طبيعية 100% وبدون أي مواد حافظة نهائياً."
    },
    {
        'keywords': ['زيت', 'ميه', 'محلول'],
        'answer': "كل أنواع التونة لدينا معبأة في زيت نباتي نقي فقط لضمان أفضل طعم."
    },
    {
        'keywords': ['مستورده', 'صناعه', 'مصري'],
        'answer': "العبوات مستوردة لضمان أفضل جودة تغليف، لكن التونة نفسها مصرية 100% ومصطادة من مياه البحر المتوسط."
    },
    {
        'keywords': ['مواعيد', 'بتفتحوا', 'الساعه كام', 'شغالين'],
        'answer': "فروعنا تعمل يوميًا من الساعة 10 صباحًا حتى الساعة 12 منتصف الليل."
    },
    {
        'keywords': ['شغل', 'توظيف', 'مندوب', 'اعمل اوردر', 'تقديم'],
        'answer': "للعمل كمندوب مبيعات بالقاهرة، يرجى التواصل (واتساب أو اتصال) على رقم التوظيف: 01210188882"
    },
    {
        'keywords': ['تصدير', 'خارج مصر', 'شحن دولي', 'احمد'],
        'answer': "لطلبات التصدير، يرجى التواصل مع أستاذ أحمد (مسؤول التصدير) على: 01272475555"
    },
    {
        'keywords': ['مشتريات', 'توريد'],
        'answer': "للتواصل مع قسم المشتريات، يرجى الاتصال على: 01223066445"
    },
    {
        'keywords': ['موارد بشريه', 'hr', 'اتش ار'],
        'answer': "للتواصل مع إدارة الموارد البشرية (HR): 01200056103"
    }
]

def get_answer(user_question):
    q = clean_arabic_text(user_question)
    
    # تحيات سريعة
    if any(word in q for word in ['سلام', 'هلو', 'ازيك', 'صباح', 'مساء']):
        return "أهلاً بك في أبو السيد، كيف يمكننا مساعدتك اليوم؟"

    best_answer = None
    max_matches = 0

    for item in FAQ:
        matches = 0
        for kw in item['keywords']:
            clean_kw = clean_arabic_text(kw)
            if clean_kw in q: # فحص مباشر للكلمة
                matches += 1
        
        if matches > max_matches:
            max_matches = matches
            best_answer = item['answer']

    if best_answer:
        return best_answer
    else:
        # إذا لم يفهم البوت، يرد برابط المنيو كحل وسط
        return "عذراً، لم أفهم طلبك بدقة. يمكنك الاطلاع على المنيو بجميع الأسعار من هنا:\nhttps://heyzine.com/flip-book/31946f16d5.html\n\nأو توضيح سؤال حضرتك بشكل أفضل حتي أستطيع مساعدتك."

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args["hub.challenge"], 200
        return "Verification token mismatch", 403
    return "Bot Online", 200

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

