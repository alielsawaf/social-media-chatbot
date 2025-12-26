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

    # الرابط الرسمي v1 مع الاسم الكامل للموديل gemini-1.5-flash
    # ده الرابط اللي جوجل بتنصح بيه حالياً لتجنب خطأ الـ 404
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"أنت خدمة عملاء رنجة أبو السيد. رد بلهجة مصرية ودودة جداً. المعلومات: {DATA_INFO}. العميل يسأل: {user_text}"
            }]
        }],
        "generationConfig": {
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_data = response.json()

        if "candidates" in res_data:
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        
        elif "error" in res_data:
            # لو لسه مطلع 404، هنغير الرابط لآخر محاولة يدوية
            error_msg = res_data["error"].get("message", "")
            return f"❌ خطأ تقني (جوجل): {error_msg[:50]}"
        
        return "منورنا يا أبو السيد! أؤمرني أساعدك إزاي؟"

    except Exception as e:
        return "يا مساء الورد! نورتنا في رنجة أبو السيد."
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









