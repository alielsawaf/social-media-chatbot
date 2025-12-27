import os
import requests
from flask import Flask, request

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

# جلب البيانات من البيئة
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# معلومات المصنع (DATA_INFO) اللي الـ AI هيعتمد عليها
DATA_INFO = """
اسم المكان: رنجة أبو السيد.
المنتجات والأسعار: رنجة سوبر (200ج)، فسيخ زبدة ملح خفيف (460ج).
المكان: بورسعيد.
الشحن: متاح لكل محافظات مصر.
الصلاحية: الفريش (شهر في الثلاجة)، المجمد (3 شهور في الفريزر).
المنيو: https://heyzine.com/flip-book/31946f16d5.html
"""

def get_ai_answer(user_text):
    if not GROQ_API_KEY:
        return "يا مساء الفل! نورت رنجة أبو السيد، أؤمرني أساعدك إزاي؟"

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {
                "role": "system", 
                "content": f"أنت موظف استقبال ذكي في مصنع رنجة أبو السيد. المعلومات: {DATA_INFO}. رد بلهجة مصرية بورسعيدية خفيفة، كن ودوداً جداً ومرحاً، وشجع العميل على الطلب."
            },
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        
        if 'choices' in res_data:
            return res_data['choices'][0]['message']['content']
        else:
            # رد احتياطي ذكي في حال حدوث مشكلة في الـ API
            if "بكام" in user_text or "سعر" in user_text:
                return "الرنجة بـ 200ج والفسيخ بـ 460ج، تحب نجهزلك أوردر؟"
            return "يا مساء الورد! نورت رنجة أبو السيد، أؤمرني يا غالي أساعدك إزاي؟"

    except Exception:
        return "يا مساء الجمال! معاك رنجة أبو السيد، أؤمرني أساعدك في الأسعار أو الشحن؟"

@app.route('/', methods=['GET'])
def verify():
    # كود التحقق الخاص بفيسبوك (Webhook Verification)
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ.get("VERIFY_TOKEN"):
            return "Verification token mismatch", 403
        return request.args.get("hub.challenge"), 200
    return "Hello Abo Elseed Bot", 200

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        if data['object'] == 'page':
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message'].get('text')
                        
                        if message_text:
                            # الحصول على الرد من الـ AI
                            answer = get_ai_answer(message_text)
                            # هنا تضع كود إرسال الرسالة لفيسبوك (Send API)
                            # send_message(sender_id, answer) 
                            
    except:
        pass
    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT", default=5000))
