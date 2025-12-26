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
        return "⚠️ المفتاح ناقص"

    # الخطوة 1: هنسأل جوجل عن الموديلات المتاحة (زي ما عملنا ونجحت)
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    
    try:
        models_res = requests.get(list_url, timeout=10).json()
        available_models = [m['name'] for m in models_res.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        
        # هنستخدم الموديل اللي اشتغل معاك المرة اللي فاتت
        selected_model = ""
        for m in available_models:
            if "gemini-pro-latest" in m or "gemini-1.5" in m or "gemini-pro" in m:
                selected_model = m
                break
        
        if not selected_model:
            return "❌ جوجل مش مفعّل أي موديلات حالياً."

        # الخطوة 2: إرسال الطلب مع تعطيل فلاتر الأمان (عشان ميرفضش الرد)
        url = f"https://generativelanguage.googleapis.com/v1beta/{selected_model}:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": f"أنت مساعد في مصنع رنجة أبو السيد. المعلومات: {DATA_INFO}\nالعميل: {user_text}\nرد باللهجة المصرية العامية."}]
            }],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
        
        response = requests.post(url, json=payload, timeout=20)
        res_data = response.json()

        if "candidates" in res_data and "content" in res_data["candidates"][0]:
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # لو رفض برضه، هنطلّع سبب الرفض بالظبط عشان نعرف هو خايف من إيه
            reason = res_data.get("promptFeedback", {}).get("blockReason", "Unknown")
            return f"❌ الموديل رفض الرد بسبب: {reason}"

    except Exception as e:
        return "يا مساء الورد! أؤمرني أساعد حضرتك إزاي؟"
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















