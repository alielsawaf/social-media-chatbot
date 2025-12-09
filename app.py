from flask import Flask, request, jsonify
import os
import requests
from fuzzywuzzy import fuzz
import pyodbc  # مكتبة الاتصال بقاعدة البيانات

app = Flask(__name__)

# --- 1. قراءة متغيرات البيئة الأساسية ---
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')

# !!! 🔴 [إجراء مؤقت للأمان]: يجب نقل هذا السطر إلى متغير بيئة اسمه SQL_DB_CONNECTION في بيئة الإنتاج !!!
# تم بناء سلسلة الاتصال باستخدام بياناتك:
# server=212.129.20.85, databasename=AbouElsayed_FAQ, user=pss, password=Aa#123456789#
SQL_DB_CONNECTION = "Driver={ODBC Driver 17 for SQL Server};Server=212.129.20.85;Database=AbouElsayed_FAQ;Uid=pss;Pwd=Aa#123456789#"
# ----------------------------------------------------------------------------------------------------------------------------------

# --- قائمة الكلمات التي سيتم إزالتها (Stop Words) لتنظيف النص ---
STOP_WORDS = [
    'ممكن', 'لو', 'سمحت', 'يا', 'فندم', 'عايز', 'من', 'فضلك', 'طيب', 'ايه', 'هو', 'هي', 
    'فين', 'ازاي', 'تكون', 'بتاعتكو', 'بتاعتنا', 'بتاعتكوا', 'بتاعتي', 'متاح', 'هل', 
    'بكام', 'الفرق', 'بين', 'و', 'دي', 'دا', 'ده', 'الي', 'اللي', 'ان', 'أن', 'ليه', 'عشان',
    'حضرتك', 'رقم', 'يرجى', 'الاستفسار', 'اريد', 'تواصل', 'عنوان', 'ابي', 'كام', 'عن', 
    'لوين', 'متوفر', 'شكرا', 'صباح', 'مساء', 'الخير', 'مساء الخير', 'صباح الخير', 'اهلا',
    'انا', 'احنا', 'كل', 'دلوقتي', 'علشان', 'مفيش', 'يوم', 'اخر', 'جديد', 'صورة', 'علي',
    'في', 'الى', 'اوقات', 'اذا', 'كنت', 'اسأل', 'بخصوص', 'مكان', 'المحلات' 
]

def clean_text(text):
    """إزالة علامات الترقيم والكلمات التي لا تحدد النية (Stop Words)."""
    cleaned_text = ''.join(c for c in text if c.isalnum() or c.isspace())
    words = cleaned_text.lower().split()
    meaningful_words = [word for word in words if word not in STOP_WORDS]
    return " ".join(meaningful_words)


# ---------------------------------------------------------------------
# ⭐️ دالة تحميل قاعدة المعرفة: لقراءة مفاتيح البحث من SQL Server ⭐️
# ---------------------------------------------------------------------
def load_faq_from_db():
    """تحميل جميع مفاتيح النوايا والـ AnswerID المرتبط بها من قاعدة البيانات."""
    
    # [ملاحظة]: يستخدم الكود الـ SQL_DB_CONNECTION المعرفة في الأعلى
    if not SQL_DB_CONNECTION:
        print("Error: SQL_DB_CONNECTION is not set.")
        return {}
    
    conn = None
    faq_map = {}
    try:
        # إنشاء الاتصال
        # [ملاحظة]: قد تحتاج بيئة التشغيل إلى تثبيت درايفر ODBC 17
        conn = pyodbc.connect(SQL_DB_CONNECTION)
        cursor = conn.cursor()
        
        # استعلام لجلب جميع مفاتيح الأسئلة والـ ID الخاص بالإجابة
        cursor.execute("SELECT QuestionKey, AnswerID FROM Intents")
        
        for row in cursor.fetchall():
            # تخزين المفتاح والـ ID في القاموس
            faq_map[row[0].lower()] = row[1] 
            
        print(f"Successfully loaded {len(faq_map)} intent keys from SQL Server.")
        return faq_map
            
    except Exception as e:
        print(f"Database loading error: {e}")
        # في حال فشل الاتصال، التطبيق سيعمل بقاعدة معرفة فارغة
        return {}
        
    finally:
        if conn:
            conn.close()

# ---------------------------------------------------------------------
# ⭐️ دالة جلب الإجابة النصية: لجلب الإجابة الكاملة باستخدام الـ ID ⭐️
# ---------------------------------------------------------------------
def fetch_answer_text(answer_id):
    """جلب نص الإجابة الكامل من جدول Answers باستخدام الـ AnswerID."""
    if not SQL_DB_CONNECTION:
        return "System Error: Database connection string is missing."

    conn = None
    try:
        conn = pyodbc.connect(SQL_DB_CONNECTION)
        cursor = conn.cursor()
        
        cursor.execute("SELECT AnswerText FROM Answers WHERE AnswerID = ?", answer_id)
        
        row = cursor.fetchone()
        
        if row:
            return row[0]
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching answer text for ID {answer_id}: {e}")
        return None
        
    finally:
        if conn:
            conn.close()

# تحميل قاعدة المعرفة (Intents Map) مرة واحدة عند تشغيل التطبيق
FAQ_INTENTS_MAP = load_faq_from_db()


# ---------------------------------------------------------------------
# ⭐️ دالة البحث عن الإجابة (تستخدم الذكاء المرجح على البيانات من SQL) ⭐️
# ---------------------------------------------------------------------
def get_answer(cleaned_message):
    """تستخدم تحليل النية المرجحة على المفاتيح المُحملة لتحديد الـ AnswerID الأنسب."""
    
    # إذا لم يتم تحميل المفاتيح من قاعدة البيانات، لا يمكننا الرد
    if not FAQ_INTENTS_MAP:
        return "عذراً، نظام قاعدة البيانات غير متاح حالياً. يرجى المحاولة لاحقاً."

    cleaned_message_lower = cleaned_message.lower()
    query_words = set(cleaned_message_lower.split())
    
    best_match_answer_id = None
    max_score = 0
    SCORE_THRESHOLD = 75 
    
    # 1. المرحلة الأولى: تحديد النية باستخدام FuzzyWuzzy على المفاتيح المحملة
    for question_key, answer_id in FAQ_INTENTS_MAP.items():

        ratio_score = fuzz.token_set_ratio(cleaned_message_lower, question_key)
        common_words_count = len(query_words.intersection(set(question_key.split())))
        
        # حساب النتيجة المرجحة (نقاط النية) - (الوزن المعزز 15 نقطة)
        total_score = ratio_score + (common_words_count * 15) 
        
        if total_score > max_score:
            max_score = total_score
            best_match_answer_id = answer_id
    
    # 2. المرحلة الثانية: جلب النص الكامل للإجابة من قاعدة البيانات
    if max_score >= SCORE_THRESHOLD and best_match_answer_id is not None:
        print(f"Intent found with Max Score: {max_score}, fetching AnswerID: {best_match_answer_id}")
        return fetch_answer_text(best_match_answer_id)
    
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
    response = requests.post(
        "https://graph.facebook.com/v19.0/me/messages", 
        params=params,
        headers=headers,
        json=data
    )
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

# --- 5. نقطة نهاية الويب (Webhook Endpoint) ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # كود التحقق (GET Request)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200 
        else:
            return "Verification token mismatch", 403

    # كود معالجة الرسائل العادي (POST Request)
    if request.method == 'POST':
        data = request.json
        
        try:
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message']['text']
                        
                        cleaned_message = clean_text(message_text) 
                        response_text = get_answer(cleaned_message) 
                        
                        if response_text:
                            send_message(sender_id, response_text)
                        else:
                            handoff_message = "عذراً، لم أجد إجابة محددة. تم تحويل استفسارك إلى فريق الدعم لدينا، وسيرد عليك أحد الموظفين في أقرب وقت ممكن!"
                            send_message(sender_id, handoff_message)
                            print(f"*** تنبيه: تم تحويل السؤال التالي للمشرف: {message_text} (النص النظيف: {cleaned_message}) ***")
        except Exception as e:
            print(f"Error processing message: {e}")
            
        return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # تأكد من تحميل المفاتيح قبل التشغيل
    if not FAQ_INTENTS_MAP:
        print("Initial database load failed. Application started with empty knowledge base.")
        
    app.run(debug=True)
