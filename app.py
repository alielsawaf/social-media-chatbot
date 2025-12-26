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
def get_answer(user_text):
    try:
        # تغيير الموديل لنسخة أحدث وأكثر استقراراً
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        
        prompt = f"أنت خدمة عملاء رنجة أبو السيد، رد بلهجة مصرية ودودة من المعلومات دي فقط: {DATA_INFO}\nالعميل بيقول: {user_text}"
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        else:
            return "نورتنا يا فندم! أقدر أساعدك إزاي؟"

    except Exception as e:
        error_details = str(e)
        # لو لسه في مشكلة 404، جرب نغير الموديل لـ gemini-pro
        if "404" in error_details:
             try:
                 alt_model = genai.GenerativeModel('gemini-pro')
                 res = alt_model.generate_content(user_text)
                 return res.text
             except:
                 return "⚠️ عذراً، الموديل غير متاح حالياً على هذا السيرفر."
        
        return f"⚠️ الـ AI واجه خطأ: {error_details[:50]}"
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

