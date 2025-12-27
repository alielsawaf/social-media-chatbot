import os
import requests
from flask import Flask, request

app = Flask(__name__)

# المتغيرات الأساسية من ريلواي
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

DATA_INFO = """
اسم المكان: رنجة أبو السيد.
المنتجات والأسعار: رنجة سوبر (200ج)، فسيخ زبدة ملح خفيف (460ج).
المكان: بورسعيد. الشحن: متاح لكل المحافظات.
الصلاحية: الفريش (شهر)، المجمد (3 شهور).
المنيو: https://heyzine.com/flip-book/31946f16d5.html
"""

def send_message(recipient_id, message_text):
    """دالة إرسال الرد لفيسبوك"""
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={FB_PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post(url, json=payload)
    return response.json()

def get_ai_answer(user_text):
    """دالة الحصول على رد من الـ AI"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": f"أنت خدمة عملاء رنجة أبو السيد بورسعيد. المعلومات: {DATA_INFO}. رد بمصرية عامية ودودة."},
                {"role": "user", "content": user_text}
            ]
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.json()['choices'][0]['message']['content']
    except:
        return "يا مساء الفل! نورت رنجة أبو السيد، أؤمرني أساعدك إزاي؟"

@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Verification token mismatch", 403
    return "Bot is Running", 200

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get('object') == 'page':
        for entry in data['entry']:
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text')
                    if message_text:
                        # 1. هات الرد من الـ AI
                        answer = get_ai_answer(message_text)
                        # 2. ابعت الرد فعلياً لفيسبوك
                        send_message(sender_id, answer)
    return "ok", 200

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)))
