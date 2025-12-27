from flask import Flask, request
import requests
import os
import google.generativeai as genai
app = Flask(__name__)

# ================== CONFIG ==================
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
# هنا ضفنا كل معلوماتك عشان الـ AI يذاكرها ويرد منها
DATA_INFO = """
اسم المصنع: رنجة أبو السيد.
المنتجات: رنجة سوبر، رنجة 24 قيراط، فسيخ ملح خفيف زبدة.
الأسعار: الرنجة بـ 200 جنيه، والفسيخ بـ 460 جنيه.
المكان: بورسعيد، وبنشحن لجميع المحافظات.
الفرق بين الفريش والمجمد: الفريش صلاحيته شهر في الثلاجة، المجمد صلاحيته 3 شهور في الفريزر.
رابط المنيو: https://heyzine.com/flip-book/31946f16d5.html
طريقة التواصل: من خلال رسائل الصفحة أو رقم الواتساب الخاص بالمصنع.
"""

# ================== AI LOGIC ==================


def get_ai_answer(user_text):
    if not GEMINI_API_KEY:
        return "⚠️ المفتاح ناقص"

    try:
        # ضبط الإعدادات
        genai.configure(api_key=GEMINI_API_KEY)
        
        # استخدام الموديل flash-8b (ده أخف وأسرع ومتاح دايماً مجاناً)
        model = genai.GenerativeModel('gemini-1.5-flash-8b')
        
        full_prompt = f"أنت خدمة عملاء رنجة أبو السيد. المعلومات: {DATA_INFO}. رد بمصرية: {user_text}"
        
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            return response.text

    except Exception as e:
        # لو الـ AI فشل، نستخدم ذكائنا اليدوي عشان الزبون ميهربش
        user_text = user_text.lower()
        if "توصيل" in user_text or "شحن" in user_text:
            return "أيوه يا فندم بنشحن لجميع المحافظات من بورسعيد، أؤمرني محتاج التوصيل لفين؟"
        if "سعر" in user_text or "بكام" in user_text:
            return "الرنجة بـ 200ج والفسيخ بـ 460ج، تحب تطلب كام كيلو؟"
        if "منيو" in user_text:
            return "اتفضل المنيو يا فندم: https://heyzine.com/flip-book/31946f16d5.html"
            
    return "يا مساء الورد! نورت رنجة أبو السيد، أؤمرني أساعدك إزاي؟"
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







