from flask import Flask, request
import requests
import os
import google.generativeai as genai

app = Flask(__name__)

# ================== CONFIG ==================
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# إعداد الجيمناي
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# الداتا اللي الـ AI هيعتمد عليها
DATA_INFO = """
رنجة أبو السيد:
- سعر الرنجة: 200 ج، عيار 24: 300 ج.
- الفسيخ بدون بكتيريا: 460 ج.
- الفرق بين الفريش والمجمد: الفريش (تبريد 0-4 وصلاحية شهر)، المجمد (تجميد -18 وصلاحية 3 شهور).
- الدود: طفيليات طبيعية تموت بالتجميد ولا تضر الإنسان.
- المنيو: https://heyzine.com/flip-book/31946f16d5.html
"""

# ================== LOGIC ==================
def get_ai_answer(user_text):
    # ده رابط الـ API المباشر من جوجل
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{
            "parts": [{"text": f"أنت خدمة عملاء رنجة أبو السيد. رد بلهجة مصرية من المعلومات دي: {DATA_INFO}\nالعميل: {user_text}"}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 200
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        
        # استخراج النص من الرد
        if "candidates" in res_data:
            return res_data['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"API Error: {res_data}")
            return "نورتنا يا غالي! أقدر أساعدك في الأسعار أو المنيو إزاي؟"
            
    except Exception as e:
        print(f"Request Error: {e}")
        return "منورنا يا أبو السيد! ابعت سؤالك تاني وهجاوبك حالاً."

def get_answer(text):
    q = normalize(text)
    
    # ردود سريعة يدوية عشان تضمن السرعة
    if "منيو" in q: return "اتفضل المنيو يا فندم: https://heyzine.com/flip-book/31946f16d5.html"
    if "دم" in q: return "السمكة جاهزة للأكل، والدم نتيجة التمليح الفريش والتجميد."
    
    # الباقي يروح للـ AI عن طريق الرابط المباشر
    return get_ai_answer(text)
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
                sender = ev["sender"]["id"]
                if "message" in ev and "text" in ev["message"]:
                    msg_text = ev["message"]["text"]
                    reply = get_answer(msg_text)
                    send_message(sender, reply)
    return "ok", 200

def send_message(user_id, text):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": user_id}, "message": {"text": text}}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


