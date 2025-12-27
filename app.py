import os
import requests
from flask import Flask, request

app = Flask(__name__)

# استدعاء المتغيرات - تأكد من وجودها في Railway Settings
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# الداتا اليدوية (مختصرة هنا، حافظ على النسخة الكاملة عندك)
FAQ_MAP = {
    "منيو": "لينك المنيو: https://heyzine.com/flip-book/31946f16d5.html",
    "الرنجة فيها دود": "فندم ده مش دود، دي طفيليات طبيعية..."
}

def get_ai_answer(user_text):
    """دالة الـ AI مع حماية من الانهيار"""
    if not GROQ_API_KEY:
        print("!!! عيب: GROQ_API_KEY مش موجود في الـ Variables !!!")
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": "أنت خدمة عملاء رنجة أبو السيد بورسعيد. رد بلهجة بورسعيدية خفيفة."},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.7
        }
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        else:
            print(f"!!! Groq Error {r.status_code}: {r.text} !!!")
            return None
    except Exception as e:
        print(f"!!! AI Crash: {str(e)} !!!")
        return None

def normalize(text):
    return text.lower().replace("ة", "ه").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").strip()

def get_answer(text):
    q = normalize(text)
    
    # 1. جرب الـ AI الأول في الأسئلة الطويلة أو الدردشة
    if len(q.split()) > 2 or any(w in q for w in ["رايك", "ازاي", "اعمل"]):
        res = get_ai_answer(text)
        if res: return res

    # 2. لو الـ AI فشل أو السؤال كلمة واحدة، استخدم اليدوي
    if "فسيخ" in q: return "سعر الفسيخ يبدأ من 460ج. تحب نجهزلك أوردر؟"
    if "رنج" in q: return "الرنجة السوبر بـ 200ج. تحب أبعتلك المنيو؟"
    if "منيو" in q: return FAQ_MAP["منيو"]
    
    return "نورت رنجة أبو السيد! أؤمرني أساعدك إزاي؟"

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "fail", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if data.get("object") == "page":
            for entry in data['entry']:
                for ev in entry.get('messaging', []):
                    sender = ev['sender']['id']
                    if 'message' in ev and 'text' in ev['message']:
                        text = ev['message']['text']
                        reply = get_answer(text)
                        send_message(sender, reply)
    except Exception as e:
        print(f"!!! Webhook Error: {str(e)} !!!")
    return "ok", 200

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
