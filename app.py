from flask import Flask, request
from fuzzywuzzy import fuzz
import requests
import re
import os

app = Flask(__name__)

# ================== CONFIG ==================
PAGE_ACCESS_TOKEN = "EAARosZC3fHjUBQNm1eADUNlWqXKJZAtNB4w9upKF3sLLcZCdz14diiyFFeSipgiEi4Vx1PZAvu9b46xPcHv2wjIekD8LZAhDuAqgSOcrAiqzZBXr3Unk5k269G26dSMZB1wsiCvazanjVWcgdoh8M6AzkPn4xzQUUUQ8o3XLJ0V5s7MfnZAyZAzWF3VBDvP4IWFX5050XCmWWGQZDZD"
VERIFY_TOKEN = "my_secret_token"

# ================== DATA ==================
# البحث عن الكلمة المفتاحية (Keyword) والرد المقابل لها فوراً
DATA_MAP = {
    "فسيخ": "💰 سعر الفسيخ المبطرخ:\nالوزن: 1 KG\nالسعر: 560 EGP ✨",
    "24": "💰 سعر رنجة مدخنة 24 قيراط:\nالوزن: 1 KG\nالسعر: 300 EGP ✨",
    "بطارخ": "💰 سعر بطارخ بوري مملحة:\nالوزن: 1 KG\nالسعر: 2850 EGP ✨",
    "تونه": "💰 سعر تونة قطع:\nالوزن: 125 G\nالسعر: 70 EGP ✨",
    "رنجه": "💰 سعر رنجة مدخنة مبطرخة:\nالوزن: 1 KG\nالسعر: 250 EGP ✨",
    "منيو": "دا لينك منيو المنتجات والأسعار بالتفصيل: https://heyzine.com/flip-book/31946f16d5.html",
    "اسعار": "دا لينك منيو المنتجات والأسعار بالتفصيل: https://heyzine.com/flip-book/31946f16d5.html",
    "دود": "فندم ده مش دود ده بيكون طفيليات.. توجد في التجويف البطني للرنجة وهي لا تصيب الإنسان.",
    "مستورد": "التونة اللي عندنا مصرية وبنصطادها من البحر الأبيض المتوسط."
}

# ================== LOGIC ==================
def get_answer(text):
    q = text.lower().replace("ة", "ه").replace("أ", "ا").replace("إ", "ا").strip()
    
    # 1. البحث المباشر في الخريطة
    for key in DATA_MAP:
        if key in q:
            return DATA_MAP[key]
    
    # 2. رد الترحيب لو الكلام عام
    if any(w in q for w in ["اهلا", "سلام", "ازيك", "صباح", "مساء"]):
        return "أهلاً بك في رنجة أبو السيد 👋 نورتنا.. حابب تعرف أسعارنا النهاردة؟ (رنجة، فسيخ، بطارخ، تونة)"
    
    # 3. الرد الافتراضي
    return "نورتنا في رنجة أبو السيد 👋.. اؤمرنا محتاج تسأل عن إيه؟ (رنجة، فسيخ، بطارخ، تونة)"

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
