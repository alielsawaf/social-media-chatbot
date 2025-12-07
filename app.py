from flask import Flask, request, jsonify
import os
import requests # مكتبة لإرسال ردود (POST requests) إلى فيسبوك

app = Flask(__name__)

# --- 1. قراءة متغيرات البيئة من Railway ---
# يجب التأكد من وجود هذه المتغيرات في Railway (Variables)
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')

# --- 2. قائمة الأسئلة الشائعة والإجابات (FAQ) ---
# يمكنك تعديل هذا القاموس ليناسب عملك
FAQ = {
    "مواعيد العمل": "مواعيد عملنا هي من الأحد إلى الخميس، من الساعة 9 صباحاً حتى 5 مساءً.",
    "الاسترجاع": "لدينا سياسة استرجاع خلال 14 يومًا من تاريخ الشراء. يرجى مراجعة شروط الاسترجاع الكاملة.",
    "عنوان المتجر": "يقع متجرنا الرئيسي في [اسم المدينة]، [عنوان تفصيلي].",
    "الشحن": "يستغرق الشحن عادةً من 3 إلى 5 أيام عمل داخل [البلد]."
}

# --- 3. دالة البحث عن الإجابة ---
def get_answer(user_message):
    """تبحث عن إجابة مطابقة للسؤال أو عن كلمة مفتاحية."""
    user_message_lower = user_message.lower()
    
    for question_key, answer in FAQ.items():
        # بحث بسيط عن الكلمات المفتاحية
        if question_key in user_message_lower or user_message_lower in question_key.lower():
            return answer
    
    return None # لم يتم العثور على إجابة

# --- 4. دالة إرسال الرد إلى فيسبوك ماسنجر ---
def send_message(recipient_id, message_text):
    """تستخدم Access Token لإرسال رسالة إلى المستخدم."""
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    }
    # إرسال طلب POST إلى API فيسبوك
    response = requests.post(
        "https://graph.facebook.com/v19.0/me/messages", # تأكد من تحديث نسخة API
        params=params,
        headers=headers,
        json=data
    )
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

# --- 5. نقطة نهاية الويب (Webhook Endpoint) ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # --- كود التحقق الأولي لفيسبوك (GET Request) ---
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # التأكد من تطابق الرمز
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200 # نجاح التحقق
        else:
            return "Verification token mismatch", 403

    # --- كود معالجة الرسائل العادي (POST Request) ---
    if request.method == 'POST':
        data = request.json
        
        # تصفح بيانات فيسبوك لاستخراج الرسالة
        try:
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message']['text']
                        
                        # 1. البحث في الأسئلة الشائعة
                        response_text = get_answer(message_text)
                        
                        if response_text:
                            # 2. إجابة آلية جاهزة
                            send_message(sender_id, response_text)
                        else:
                            # 3. تحويل للمشرف البشري
                            handoff_message = "عذراً، لم أجد إجابة محددة. تم تحويل استفسارك إلى فريق الدعم لدينا، وسيرد عليك أحد الموظفين في أقرب وقت ممكن!"
                            send_message(sender_id, handoff_message)
                            print(f"*** تنبيه: تم تحويل السؤال التالي للمشرف: {message_text} ***")
        except Exception as e:
            print(f"Error processing message: {e}")
            
        return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)
