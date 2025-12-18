from flask import Flask, request, jsonify
from fuzzywuzzy import fuzz
import requests
import re
import urllib.parse

# --------------------------------------------------------------------------------
# علامة تأكيد قراءة الكود المطور
print(">>> CODE VERSION 8.0: SEMANTIC SEARCH & ARABIC NORMALIZATION ENABLED <<<")
# --------------------------------------------------------------------------------

app = Flask(__name__)

# ⚠️ المتغيرات الحيوية
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
WHATSAPP_NUMBER = "201090636076"

# --------------------------------------------------------------------------------
# دالة تنظيف وتوحيد النص العربي (لجعل البحث ذكياً)
# --------------------------------------------------------------------------------
def clean_arabic_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    # توحيد الألفات
    text = re.sub(r"[إأآا]", "ا", text)
    # توحيد التاء المربوطة والهاء
    text = re.sub(r"ة", "ه", text)
    # توحيد الياء والألف المقصورة
    text = re.sub(r"ى", "ي", text)
    # إزالة علامات الترقيم والرموز
    text = re.sub(r'[^\w\s]', '', text)
    # إزالة المسافات الزائدة
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# --------------------------------------------------------------------------------
# ردود التحية
# --------------------------------------------------------------------------------
GREETINGS = {
    'morning': ['صباح الخير', 'صباح الفل', 'صباح النور'],
    'evening': ['مساء الخير', 'مساء النور', 'مساء الفل'],
    'greetings': ['سلام عليكم', 'السلام عليكم', 'ازيك', 'يا بوت', 'هلو'],
}

# --------------------------------------------------------------------------------
# قاعدة البيانات (FAQ)
# --------------------------------------------------------------------------------
FAQ = [
    {
        'questions': ['الاسعار غاليه', 'ليه غالي', 'السعر عالي', 'ليه اسعاركم مرتفعه', 'prices high'],
        'answer': "اهلا بحضرتك، نحن نضمن لك جودة منتج مختلفة حيث يتم التمليح بمحلول براين والتدخين على البارد بنشارة ألماني لضمان منتج صحي وجاهز للأكل."
    },
    {
        'questions': ['دود في الرنجه', 'لقيت دود', 'فيها طفيليات', 'الرنجه مدوده', 'الرنجه بايظه'],
        'answer': "مساء الخير يا فندم، اللي ظهر ده مش دود، دي طفيليات طبيعية في التجويف البطني ولا تصيب الإنسان. نحن نجمد الأسماك عند -40 درجة لضمان القضاء تماماً على أي أثر لها."
    },
    {
        'questions': ['يعني ايه فاكيوم', 'الفاكيوم ده ايه', 'vacuum'],
        'answer': "فاكيوم يعني مغلف في عبوات مفرغة الهواء، مما يساعد على الحفاظ على المنتج طازجاً لأطول فترة ممكنة."
    },
    {
        'questions': ['المنتج مصري', 'صنع فين', 'مستورد ولا مصري'],
        'answer': "منتجاتنا مصرية 100%، يتم التصنيع والتعبئة في مصنعنا ببورسعيد (بورسعيد ستار)."
    },
    {
        'questions': ['التوصيل', 'دليفري', 'شحن', 'في توصيل للقاهره', 'delivery'],
        'answer': "التوصيل متاح في (بورسعيد، القاهرة، إسكندرية، الغردقة). للطلبات اتصل على: 01212166660."
    },
    {
        'questions': ['المنيو', 'الاسعار كام', 'بكام الرنجه', 'menu'],
        'answer': "تفضل لينك المنيو المحدث بجميع الأسعار: https://heyzine.com/flip-book/31946f16d5.html"
    },
    {
        'questions': ['التصدير', 'تلفون التصدير', 'مسئول التصدير'],
        'answer': "لطلبات التصدير، يرجى التواصل مع أستاذ أحمد واتساب: 01272475555"
    },
    {
        'questions': ['رقم الحسابات', 'مدير الحسابات', 'الشماع'],
        'answer': "الأستاذ محمد الشماع – مدير الحسابات: 01204464066"
    },
    {
        'questions': ['التوظيف', 'اتش ار', 'شغل', 'hr'],
        'answer': "للتواصل مع إدارة الـ HR في بورسعيد: 01200056103"
    },
    {
        'questions': ['ملح الرنجه', 'ملحه عالي', 'الرنجه حدقه', 'نسبه الملوحه'],
        'answer': "نسبة الملوحة تختلف حسب تقبل كل شخص، ولكننا نحرص على تقديم تمليح متوازن يرضي أغلب الأذواق."
    }
    # ملاحظة: يمكنك إضافة باقي الـ 52 سؤالاً بنفس النمط هنا
]

# --------------------------------------------------------------------------------
# منطق البحث الذكي
# --------------------------------------------------------------------------------
def get_answer(user_question):
    raw_query = user_question.strip().lower()
    cleaned_query = clean_arabic_text(raw_query)

    # 1. فحص التحيات أولاً
    for key, phrases in GREETINGS.items():
        for p in phrases:
            if clean_arabic_text(p) in cleaned_query:
                if key == 'morning': return "صباح النور يا فندم، تحت أمرك."
                if key == 'evening': return "مساء الخير يا فندم، كيف يمكنني مساعدتك؟"
                return "وعليكم السلام ورحمة الله، كيف يمكنني مساعدتك اليوم؟"

    # 2. البحث الذكي في الأسئلة
    best_score = 0
    selected_answer = None

    for item in FAQ:
        for q in item['questions']:
            # نستخدم token_set_ratio لأنه يتجاهل ترتيب الكلمات والكلمات الزائدة
            score = fuzz.token_set_ratio(cleaned_query, clean_arabic_text(q))
            if score > best_score:
                best_score = score
                selected_answer = item['answer']

    # عتبة الثقة (75% تعتبر جيدة جداً للفهم المرن)
    if best_score >= 75:
        return selected_answer
    else:
        # التحويل للواتساب في حال عدم الفهم
        encoded_msg = urllib.parse.quote(f"استفسار عميل: {user_question}")
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded_msg}"
        return f"أهلاً بك. لم أفهم طلبك بدقة، يمكنك التواصل مع الموظف المختص مباشرة عبر الواتساب للمساعدة:\n\n{whatsapp_url}"

# --------------------------------------------------------------------------------
# إعدادات فيسبوك (Webhooks)
# --------------------------------------------------------------------------------
@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == "my_secret_token":
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello Bot", 200

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text")
                    
                    if message_text:
                        response_text = get_answer(message_text)
                        send_message(sender_id, response_text)
    return "ok", 200

def send_message(recipient_id, message_text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post("https://graph.facebook.com/v12.0/me/messages", params=params, headers=headers, json=data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
