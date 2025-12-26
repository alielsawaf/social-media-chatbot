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
        return "⚠️ خطأ: المفتاح غير مضبوط"

    # ده الرابط المستقر لمناداة موديل Pro (النسخة المجانية)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": f"أنت مساعد ذكي لمصنع رنجة أبو السيد. رد بمصرية عامية. المعلومات: {DATA_INFO}\nالعميل: {user_text}"}]
        }]
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        res_data = response.json()
        
        if "candidates" in res_data:
            return res_data['candidates'][0]['content']['parts'][0]['text']
        else:
            # لو الموديل Pro لسه فيه مشكلة في المنطقة، هنجرب Flash بس بالرابط الصحيح
            return retry_with_flash(user_text)
            
    except Exception as e:
        return "أهلاً بك في رنجة أبو السيد! نورتنا."

# دالة احتياطية لو Pro رفض يشتغل
def retry_with_flash(user_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    full_prompt = f"أنت موظف استقبال في رنجة أبو السيد. رد بلهجة مصرية. {DATA_INFO}\nالعميل يسأل: {user_text}"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 300
        }
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        data = r.json()
        
        # استخراج النص بذكاء
        if "candidates" in data and "content" in data["candidates"][0]:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # لو جوجل رفض يرد لأي سبب، هنخليه يرد يدوي بس بذكاء
            if "بكام" in user_text or "سعر" in user_text:
                return "الرنجة عندنا بـ 200 ج والفسيخ بـ 460 ج يا فندم. نورتنا!"
            if "منيو" in user_text:
                return "اتفضل منيو رنجة أبو السيد من هنا: https://heyzine.com/flip-book/31946f16d5.html"
            return "يا مساء الفل! نورت رنجة أبو السيد، أؤمرني أساعدك إزاي؟"
    except:
        return "يا مساء الورد! نورتنا، تحت أمرك في أي استفسار."
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




