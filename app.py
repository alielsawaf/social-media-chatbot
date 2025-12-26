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

    # الخطوة 1: هنسأل جوجل "إيه الموديلات اللي عندك يا سيدي؟"
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    
    try:
        models_res = requests.get(list_url, timeout=10).json()
        available_models = [m['name'] for m in models_res.get('models', [])]
        
        # الخطوة 2: هنختار أول موديل متاح يدعم توليد المحتوى
        # هندور بالترتيب على (flash 1.5 ثم pro 1.5 ثم pro 1.0)
        selected_model = ""
        for target in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
            for am in available_models:
                if target in am:
                    selected_model = am
                    break
            if selected_model: break
        
        if not selected_model:
            return "❌ جوجل مش مفعّل أي موديلات على المفتاح ده حالياً."

        # الخطوة 3: نبعت السؤال للموديل اللي لقيناه شغال فعلاً
        url = f"https://generativelanguage.googleapis.com/v1beta/{selected_model}:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": f"أنت خدمة عملاء رنجة أبو السيد. المعلومات: {DATA_INFO}. رد بمصرية: {user_text}"}]}]
        }
        
        response = requests.post(url, json=payload, timeout=15)
        res_data = response.json()

        if "candidates" in res_data:
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"❌ الموديل {selected_model} موجود بس رفض يرد."

    except Exception as e:
        return f"⚠️ عذراً، حاول مرة أخرى (خطأ اتصال)."
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














