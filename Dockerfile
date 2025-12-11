# استخدم صورة Python 3.10 كنظام أساسي
FROM python:3.10-slim

# تعيين دليل العمل داخل الحاوية
WORKDIR /app

# نسخ ملف متطلبات المشروع وتثبيته
# هذا هو الإجراء القياسي، تأكد من وجود requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملف التطبيق app.py إلى الحاوية
COPY app.py .

# تحديد المنفذ (8080) كإجراء إعلامي
EXPOSE 8080

# أمر التشغيل النهائي:
# تشغيل Gunicorn لتطبيق Flask (app:app) وربطه بمنفذ Railway الداخلي ($PORT).
# تم حذف -w و --timeout لحل مشكلة "Worker failed to boot".
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
