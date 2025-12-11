# استخدم صورة Python 3.10 كنظام أساسي
FROM python:3.10-slim

# تعيين دليل العمل داخل الحاوية
WORKDIR /app

# نسخ ملف متطلبات المشروع وتثبيته
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملف التطبيق app.py إلى الحاوية
COPY app.py .

# تحديد المنفذ (8080) كإجراء إعلامي
EXPOSE 8080

# أمر التشغيل النهائي (الصيغة الصحيحة التي تعالج $PORT):
# نستخدم الصيغة السطرية بدلاً من مصفوفة JSON لضمان قراءة المتغير.
CMD gunicorn app:app --bind 0.0.0.0:$PORT
