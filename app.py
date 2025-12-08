from flask import Flask, request, jsonify
import os
import requests
from fuzzywuzzy import fuzz # تمت إضافة المكتبة الجديدة

app = Flask(__name__)

# --- 1. قراءة متغيرات البيئة من Railway ---
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')

# --- قائمة الكلمات التي سيتم إزالتها (Stop Words) لتنظيف النص ---
STOP_WORDS = [
    'ممكن', 'لو', 'سمحت', 'يا', 'فندم', 'عايز', 'من', 'فضلك', 'طيب', 'ايه', 'هو', 'هي', 
    'فين', 'ازاي', 'تكون', 'بتاعتكو', 'بتاعتنا', 'بتاعتكوا', 'بتاعتي', 'متاح', 'هل', 
    'بكام', 'الفرق', 'بين', 'و', 'دي', 'دا', 'ده', 'الي', 'اللي', 'ان', 'أن', 'ليه', 'عشان',
    'حضرتك', 'رقم', 'يرجى', 'الاستفسار', 'اريد'
]

def clean_text(text):
    """إزالة علامات الترقيم والكلمات التي لا تحدد النية (Stop Words)."""
    # 1. إزالة علامات الترقيم والرموز (للتأكد من إزالة أي علامات غريبة)
    cleaned_text = ''.join(c for c in text if c.isalnum() or c.isspace())
    
    # 2. تحويل النص إلى قائمة كلمات
    words = cleaned_text.lower().split()
    
    # 3. إزالة الكلمات التي لا تحدد النية (Stop Words)
    meaningful_words = [word for word in words if word not in STOP_WORDS]
    
    # 4. تجميع الكلمات المتبقية
    return " ".join(meaningful_words)


# --- الإجابات الطويلة لسهولة التعديل والتكرار ---
# الإجابة 1: التوصيل
ANSWER_DELIVERY = "خدمة التوصيل...\nالقاهره: خدمة توصيل أبو السيد متاحة الآن في مدينتي اربيسك والتجمع الأول والتجمع الخامس والتجمع الثالث وويست جيت أكتوبر فقط.\nللطلبات خارج هذه المناطق، نوفر لك سائقًا خاصًا لكن برسوم توصيل إضافية.\nخدمه التوصيل متوفره فى بورسعيد و القاهره و اسكندريه والغردقه فقط."

# الإجابة 2: التأكد من الرنجة (الأصلية)
ANSWER_AUTHENTICITY = "المصدر: حاول شراء رنجة أبو السيد من مصادر موثوقة لضمان حصولك على المنتج الأصلي.\nوالرنجه الخاصة بنا تكون في كراتين وليس صناديق خشب."

# الإجابة 3: الساندوتشات والسلطة
ANSWER_SANDWICHES = "منيو الساندويتشات و السلطة غير متاح حاليا ولا يوجد توصيل للساندوتشات و السلطة."

# الإجابة 4: المنيو (اللينك)
ANSWER_MENU = "مساء الخير دا لينك منيو المنتجات بتاعتنا:\nhttps://heyzine.com/flip-book/31946f16d5.html"

# الإجابة 5: سبب الغلاء/الجودة
ANSWER_HIGH_QUALITY = "لاننا بنضمنلك جودة منتج يا فندم حيث ان طريقة التمليح و التدخين مختلفة.\nاحنا بنملح سمك الرنجة بمحلول براين و بيتم تدخين السمك علي البارد بنشارة الماني عشان نضمن لحضرتك منتج صحي مدخن بشكل صحيح جاهز علي الاكل."

# الإجابة 6: التونة (الكانز)
ANSWER_TUNA_CAN = "الكانز التونة بيكون مستورد و مطبوع و دا الكان نفسه مش السمكة.\nلكن التونة الي عندنا مش مستوردة، هي تونة مصرية و بنصطادها من البحر الابيض المتوسط."

# الإجابة 7: الفرق بين السلمون (طبق/كيس)
ANSWER_SALMON_DIFF = "الفرق بيكون في لون اللحم، في الطبق بيكون افتح من الي في الكيس بسبب طريقة التدخين و طريقة التمليح و طريقة طهي المنتج و ده بيؤدي الي ان المنتجين بيكون في بينهم اختلاف في الطعم."

# الإجابة 8: مسؤول التوريد
ANSWER_SUPPLY_MANAGER = "دة رقم الاستاذ بلال يافندم مسؤل التوريد تقدر تتواصل معاه و هيساعد حضرتك: 01221093951"

# الإجابة 9: ضغط الفروع
ANSWER_BRANCH_PRESSURE = "ممكن حضرتك تتواصل تاني عشان للاسف في ضغط علي الفروع."

# الإجابة 10: مدير الحسابات
ANSWER_ACCOUNT_MANAGER = "01204464066 استاذ محمد الشماع مدير الحسابات ممكن يساعد حضرتك."

# الإجابة 11: الفرق بين الرنجة فيليه وعادية
ANSWER_FILLET_DIFF = "الرنجة الفيليه بتيجي مخلية و بيتم عليها عملية التصنيع بداية من التمليح للتدخين و بتاخد 3 طبقات تدخين لتعزيز طعم التدخين فيها. عشان كدا بتكون انشف من الرنجة العادية و الفص طعمه مختلف."

# الإجابة 12: سبب نشفان الفيليه
ANSWER_FILLET_DRY = "الرنجة الفيليه بتكون مخلية وواخده 3 طبقات سموك لتعزيز طعم التدخين فيها، عشان كده بتكون انشف شويه من الرنجة العاديه."

# الإجابة 13: دم الفسيخ
ANSWER_FESIKH_BLOOD = "يا فندم السمكه جاهزه علي الاكل و الدم ده بيكون بسبب ان السمكه بتتملح فريش و بيتم حفظها بعد عملية التمليح في التجميد. و عند الشراء بتخرج من مرحله التجميد ف السمكه بتفك عشان كده في السوائل (دم)."

# الإجابة 14: الفرق بين لحم التونة (أبيض/أحمر)
ANSWER_TUNA_COLOR = "اللحم الابيض افتح من اللحم الاحمر لان اللون الأحمر في لحم التونه بيجي من الميوغلوبين والهيموجلوبين. الميوغلوبين هو بروتين يحمل الأكسجين لذلك يكون اللحم الاحمر في التونة نسبة البروتين الموجودة فيه اعلي من التونة البيضاء. لحم التونة الاحمر بيكون طري اكثر من لحم التونة الابيض بسبب زيادة نسبة البروتين فيه."

# الإجابة 15: معلومات الفسيخ
ANSWER_FESIKH_INFO = "يتم عمل الفسيخ من سمك البوري. يتم تمليح الفسيخ فريش لايقاف النمو البكتيري. يتم تمليح الفسيخ تمليح جاف. يحفظ الفسيخ داخل ثلاجات بدرجات حرارة من 0 الي 4 لايقاف النمو البكتيري."

# الإجابة 16: حفظ الرنجة
ANSWER_STORAGE = "يفضل ان تحفظ في الفريزر بعد الشراء."

# الإجابة 17: الفرق بين عيار 24
ANSWER_24_KIND = "في عيار 24 عدد ساعات التدخين اطول من العادية، و حجم السمكة اصغر من حجم السمكة العادية، و طعم التدخين بيكون معزز اكثر لان عدد ساعات التدخين بتكون ازيد من عدد ساعات التدخين في السمكة العادية."

# الإجابة 18: الطلب اونلاين
ANSWER_ONLINE_ORDER = "غير متاح حاليا الطلب اونلاين يا فندم. لعمل اوردر بيكون عن طريق الإتصال على: 01212166660"

# الإجابة 19: وزن كرتونة
ANSWER_CARTON_WEIGHT = "وزن كرتونة الرنجة المجمده الكرتونه بتكون من 7.5 ل 8 كيلو يا فندم. ده مش جمله ده قطاعى عادى."

# الإجابة 20: الفرق بين المجمدة والفريش
ANSWER_FROZEN_FRESH = "الرنجه المجمده: تحفظ في درجه حراره -18، صلاحيه 3 شهور، وتحفظ في التجميد و ليس التبريد. الرنجه الفريش: تحفظ في درجه حراره 0 الي 4، صلاحيه شهر، وتحفظ في التبريد (درجه حراره الثلاجه)."

# --- 2. قائمة الأسئلة الشائعة والإجابات (FAQ) المحدثة بالمرادفات ---
FAQ = {
    # ------------------ 1. التوصيل ------------------
    "يوجد توصيل": ANSWER_DELIVERY,
    "توصيل": ANSWER_DELIVERY,
    "دليفري": ANSWER_DELIVERY,
    "شحن": ANSWER_DELIVERY,
    "مناطق التوصيل": ANSWER_DELIVERY,

    # ------------------ 2. التأكد من الأصالة ------------------
    "ازاي اتأكد رنجة رنجة ابو السيِد": ANSWER_AUTHENTICITY,
    "رنجة أبو السيد": ANSWER_AUTHENTICITY,
    "اصلي تقليد": ANSWER_AUTHENTICITY,
    "صناديق خشب": ANSWER_AUTHENTICITY, 

    # ------------------ 3. الساندوتشات والسلطة ------------------
    "ساندوتشات السلطة": ANSWER_SANDWICHES,
    "منيو ساندوتشات": ANSWER_SANDWICHES,
    "الفروع المتاح الساندوتشات السلطة": ANSWER_SANDWICHES,
    
    # ------------------ 4. المنيو ------------------
    "منيو المنتجات": ANSWER_MENU,
    "لينك المنيو": ANSWER_MENU,
    "كتالوج": ANSWER_MENU,

    # ------------------ 5. الغلاء والجودة ------------------
    "الرنجه بتاعتكو غاليه": ANSWER_HIGH_QUALITY,
    "غاليه": ANSWER_HIGH_QUALITY,
    "المنتجات بتاعتكوا غالية": ANSWER_HIGH_QUALITY,
    "السعر": ANSWER_HIGH_QUALITY,
    
    # ------------------ 6. التونة (الكانز) ------------------
    "الكانز بتاعة التونة مستورده مصري": ANSWER_TUNA_CAN,
    "تونة مستوردة": ANSWER_TUNA_CAN,
    "كانز التونة": ANSWER_TUNA_CAN,
    
    # ------------------ 7. فرق السلمون (طبق/كيس) ------------------
    "سلمون الشراح الفاكيوم": ANSWER_SALMON_DIFF,
    "سلمون طبق كيس": ANSWER_SALMON_DIFF,
    "سلمون فاكيوم": ANSWER_SALMON_DIFF,

    # ------------------ 8. مسؤول التوريد ------------------
    "مسؤل توريد للفنادق والمطاعم": ANSWER_SUPPLY_MANAGER,
    "مسؤول توريد": ANSWER_SUPPLY_MANAGER,
    "توريد فنادق": ANSWER_SUPPLY_MANAGER,

    # ------------------ 9. ضغط الفروع ------------------
    "عدم الرد تليفون الفروع": ANSWER_BRANCH_PRESSURE,
    "تليفون الفروع": ANSWER_BRANCH_PRESSURE,
    
    # ------------------ 10. مدير الحسابات ------------------
    "مدير الحسابات": ANSWER_ACCOUNT_MANAGER,
    "مدير الحسابات": ANSWER_ACCOUNT_MANAGER,

    # ------------------ 11. فرق الرنجة فيليه وعادية ------------------
    "الرنجة الفيليه الرنجة العادية": ANSWER_FILLET_DIFF,
    "رنجة فيليه عادية": ANSWER_FILLET_DIFF,
    "فيليه عادية": ANSWER_FILLET_DIFF,
    
    # ------------------ 12. نشفان الفيليه ------------------
    "الرنجة الفيليه بتكون ناشفة": ANSWER_FILLET_DRY,
    "ناشفة": ANSWER_FILLET_DRY,

    # ------------------ 13. دم الفسيخ ------------------
    "الفسيخ بيكون دم": ANSWER_FESIKH_BLOOD,
    "دم الفسيخ": ANSWER_FESIKH_BLOOD,
    
    # ------------------ 14. فرق التونة (أبيض/أحمر) ------------------
    "لحم التونة الابيض لحم التونة الاحمر": ANSWER_TUNA_COLOR,
    "تونة بيضاء حمراء": ANSWER_TUNA_COLOR,
    "لحم التونة الابيض": ANSWER_TUNA_COLOR,
    
    # ------------------ 15. معلومات الفسيخ ------------------
    "معلومات سمكة الفسيخ": ANSWER_FESIKH_INFO,
    "سمكة الفسيخ": ANSWER_FESIKH_INFO,
    "حفظ الفسيخ": ANSWER_FESIKH_INFO,
    
    # ------------------ 16. حفظ الرنجة ------------------
    "كيفية الاحتفاظ بالرنجة الشراء": ANSWER_STORAGE,
    "حفظ الرنجة": ANSWER_STORAGE,
    "تخزين الرنجة": ANSWER_STORAGE,

    # ------------------ 17. فرق عيار 24 ------------------
    "الرنجة العادية الرنجة عيار 24": ANSWER_24_KIND,
    "عيار 24": ANSWER_24_KIND,
    "رنجة 24": ANSWER_24_KIND,

    # ------------------ 18. طلب اونلاين ------------------
    "طلب اوردر اونلاين": ANSWER_ONLINE_ORDER,
    "طلب اوردر": ANSWER_ONLINE_ORDER,

    # ------------------ 19. وزن الكرتونة ------------------
    "وزن كرتونة الرنجه المجمده": ANSWER_CARTON_WEIGHT,
    "وزن الكرتونة": ANSWER_CARTON_WEIGHT,

    # ------------------ 20. فرق مجمدة/فريش ------------------
    "الرنجه المجمده الفريش": ANSWER_FROZEN_FRESH,
    "رنجة مجمدة وفريش": ANSWER_FROZEN_FRESH,
    "صلاحية الرنجة": ANSWER_FROZEN_FRESH
}


# --- 3. دالة البحث عن الإجابة (المحدثة باستخدام fuzzywuzzy) ---
def get_answer(user_message):
    """تبحث عن إجابة مطابقة للسؤال أو عن كلمة مفتاحية بدرجة تشابه عالية."""
    # user_message هنا هو بالفعل 'cleaned_message' من الويب هوك
    user_message_lower = user_message.lower()
    
    # حدد الحد الأدنى لنسبة التشابه المطلوبة (75% نسبة معقولة)
    THRESHOLD = 75
    
    best_match_answer = None
    highest_ratio = 0
    
    for question_key, answer in FAQ.items():
        # استخدام fuzz.token_set_ratio: يقارن الكلمات الرئيسية بغض النظر عن الترتيب والكلمات الزائدة
        ratio = fuzz.token_set_ratio(user_message_lower, question_key.lower())
        
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match_answer = answer
    
    # إذا تجاوز أعلى نسبة تشابه الحد الأدنى (THRESHOLD)، يتم إرسال الإجابة
    if highest_ratio >= THRESHOLD:
        # طباعة النسبة المئوية للاختبار والمتابعة
        print(f"Match found with ratio: {highest_ratio}%") 
        return best_match_answer
    
    return None # لم يتم العثور على إجابة


# --- 4. دالة إرسال الرد إلى فيسبوك ماسنجر (كما هي) ---
def send_message(recipient_id, message_text):
    """تستخدم Access Token لإرسال رسالة إلى المستخدم."""
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    }
    # إرسال طلب POST إلى API فيسبوك
    response = requests.post(
        "https://graph.facebook.com/v19.0/me/messages", 
        params=params,
        headers=headers,
        json=data
    )
    # هذا السطر مهم جداً لتشخيص فشل الرد!
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")
        print(f"Status Code: {response.status_code}") 

# --- 5. نقطة نهاية الويب (Webhook Endpoint) ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # --- كود التحقق الأولي لفيسبوك (GET Request) ---
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # التأكد من تطابق الرمز
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200 
        else:
            return "Verification token mismatch", 403

    # --- كود معالجة الرسائل العادي (POST Request) ---
    if request.method == 'POST':
        data = request.json
        
        # تصفح بيانات فيسبوك لاستخراج الرسالة
        try:
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message']['text']
                        
                        # الخطوة الجديدة: تنظيف الرسالة قبل إرسالها للبحث
                        cleaned_message = clean_text(message_text) 
                        
                        # 1. البحث في الأسئلة الشائعة باستخدام النص النظيف
                        response_text = get_answer(cleaned_message) 
                        
                        if response_text:
                            # 2. إجابة آلية جاهزة
                            send_message(sender_id, response_text)
                        else:
                            # 3. تحويل للمشرف البشري
                            handoff_message = "عذراً، لم أجد إجابة محددة. تم تحويل استفسارك إلى فريق الدعم لدينا، وسيرد عليك أحد الموظفين في أقرب وقت ممكن!"
                            send_message(sender_id, handoff_message)
                            print(f"*** تنبيه: تم تحويل السؤال التالي للمشرف: {message_text} (النص النظيف: {cleaned_message}) ***")
        except Exception as e:
            # طباعة الخطأ في السجلات لمزيد من التشخيص
            print(f"Error processing message: {e}")
            
        return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)
