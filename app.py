from flask import Flask, request, jsonify

app = Flask(__name__)

# --- 1. قائمة الأسئلة الشائعة والإجابات (FAQ) ---
# يمكنك تعديل هذا القاموس ليناسب عملك
FAQ = {
    "مواعيد العمل": "مواعيد عملنا هي من الأحد إلى الخميس، من الساعة 9 صباحاً حتى 5 مساءً.",
    "الاسترجاع": "لدينا سياسة استرجاع خلال 14 يومًا من تاريخ الشراء. يرجى مراجعة شروط الاسترجاع الكاملة.",
    "عنوان المتجر": "يقع متجرنا الرئيسي في [اسم المدينة]، [عنوان تفصيلي].",
    "الشحن": "يستغرق الشحن عادةً من 3 إلى 5 أيام عمل داخل [البلد]."
}

# --- 2. دالة البحث عن الإجابة ---
def get_answer(user_message):
    """تبحث عن إجابة مطابقة للسؤال أو عن كلمة مفتاحية."""
    
    # تحويل الرسالة إلى حروف صغيرة للتطابق السهل
    user_message_lower = user_message.lower()
    
    for question_key, answer in FAQ.items():
        if question_key in user_message_lower or user_message_lower in question_key.lower():
            return answer  # إجابة جاهزة
    
    return None # لم يتم العثور على إجابة

# --- 3. نقطة نهاية الويب (Webhook Endpoint) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    # افترض أن منصة السوشيال ميديا ترسل البيانات كـ JSON
    data = request.json
    
    # **ملاحظة:** طريقة استخلاص الرسالة تختلف حسب منصة السوشيال ميديا (فيسبوك، تويتر، إلخ).
    # نحن هنا نفترض أن الرسالة موجودة في 'message'
    
    # مثال بسيط لاستخراج رسالة افتراضية
    try:
        incoming_message = data.get('message', '')
    except Exception:
        return jsonify({"status": "error", "message": "Invalid data format"}), 400

    if not incoming_message:
        return jsonify({"status": "ok", "response": "No message received"}), 200


    # البحث في الأسئلة الشائعة
    response_text = get_answer(incoming_message)
    
    if response_text:
        # إجابة آلية جاهزة
        final_response = {
            "type": "automatic",
            "text": response_text
        }
    else:
        # **تحويل للمشرف البشري**
        
        # في بيئة العمل الحقيقية، هنا يتم تسجيل الرسالة في قاعدة بيانات
        # أو إرسال إشعار (مثل بريد إلكتروني، رسالة Slack) لفريق الدعم.
        
        print(f"*** تنبيه: تم تحويل السؤال التالي للمشرف: {incoming_message} ***")
        
        final_response = {
            "type": "human_handoff",
            "text": "عذراً، لم أجد إجابة محددة. تم تحويل استفسارك إلى فريق الدعم لدينا، وسيرد عليك أحد الموظفين في أقرب وقت ممكن!"
        }
        
    # إرجاع الرد
    return jsonify({"response": final_response['text']}), 200

if __name__ == '__main__':
    # يجب استخدام Gunicorn للنشر على Render، لكن هذا للتشغيل المحلي
    app.run(debug=True)