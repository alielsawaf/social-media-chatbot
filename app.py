from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ================== CONFIG ==================
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

DATA_INFO = "رنجة أبو السيد: مصنع رنجة وفسيخ، أسعارنا: رنجة 200ج، فسيخ 460ج. المنيو: https://heyzine.com/flip-book/31946f16d5.html"

# ================== AI LOGIC ==================
def get_ai_answer(user_text):
    if not GEMINI_API_KEY:
        return "⚠️ المفتاح غير موجود"

    # الرابط ده هو الوحيد اللي هيشغل Flash 1.5 حالياً مع Railway
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"أنت موظف استقبال في رنجة أبو السيد. المعلومات: {DATA_INFO}. رد بمصرية عامية على: {user_text}"
            }]
        }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        # زودنا الـ timeout لـ 30 ثانية عشان ندي فرصة للـ AI يفكر
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        res_data = response.json()

        if "candidates" in res_data and len(res_data["candidates"]) > 0:
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        
        elif "error" in res_data:
            # لو لسه مطلع 404، هنجرب الموديل القديم gemini-pro أوتوماتيكياً
            return retry_with_pro(user_text)
        
        else:
            return "منورنا في رنجة أبو السيد! أؤمرني أساعدك إزاي؟"

    except Exception as e:
        return f"⚠️ عذراً، حاول مرة أخرى: {str(e)[:30]}"

def retry_with_pro(user_text):
    # الخطة البديلة بموديل Gemini Pro المستقر
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"رد بمصرية كخدمة عملاء رنجة أبو السيد: {user_text}"}]}]
    }
    try:
        r = requests.post(url, json=payload, timeout=20)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "يا مساء الفل! نورتنا في رنجة أبو السيد."
        # ================== WEBHOOK ==================
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for ev in entry.get("messaging", []):
                sender_id = ev.get("sender", {}).get("id")
                if "message" in ev and "text" in ev["message"]:
                    msg_text = ev["message"]["text"]
                    
                    # الردود اليدوية السريعة
                    if "منيو" in msg_text:
                        reply = "اتفضل المنيو يا فندم: https://heyzine.com/flip-book/31946f16d5.html"
                    else:
                        reply = get_ai_answer(msg_text)
                    
                    send_message(sender_id, reply)
    return "ok", 200

def send_message(user_id, text):
    if not user_id: return
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": user_id}, "message": {"text": text}}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Facebook Send Error: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))






