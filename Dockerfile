# استخدم صورة Python كأساس
FROM python:3.10-slim

# تعيين دليل العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المتطلبات (إذا كنت تستخدم ملف requirements.txt)
# إذا لم يكن لديك هذا الملف، قم بتخطي السطرين التاليين مؤقتاً
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# تثبيت مكتباتك يدوياً إذا لم يكن لديك requirements.txt
RUN pip install Flask gunicorn fuzzywuzzy

# نسخ ملف التطبيق إلى الحاوية
COPY app.py .

# تعريف المنفذ
EXPOSE 8080

# أمر التشغيل (يجب أن يتطابق مع Start Command في Railway)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
