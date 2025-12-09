# 1. المرحلة الأساسية: استخدام صورة Python رسمية خفيفة (مبنية على Debian)
FROM python:3.10-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /usr/src/app

# --- 2. تثبيت حزم نظام التشغيل و درايفر ODBC 17 ---

# تثبيت الحزم الأساسية المطلوبة للدرايفر (unixodbc, curl, gpg)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        curl \
        gnupg \
        lsb-release \
    # تجميع جميع ملفات التثبيت في سطر واحد لتقليل حجم الصورة
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# إضافة مستودع Microsoft وتثبيت درايفر ODBC 17
# تم تحديث الطريقة لتجنب خطأ "Failed writing body"
RUN set -ex; \
    # جلب مفتاح GPG وحفظه بالطريقة الحديثة في keyrings
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /usr/share/keyrings/microsoft.gpg > /dev/null; \
    # إضافة المستودع باستخدام المفتاح الموقع
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod debian main" | tee /etc/apt/sources.list.d/mssql-tools.list; \
    # تحديث وتثبيت درايفر ODBC 17
    apt-get update; \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17

# --- 3. نسخ ملفات التطبيق وتثبيت المتطلبات ---
# نسخ كل الملفات من جذر المشروع إلى الحاوية
COPY . .

# تثبيت مكتبات Python (يجب أن يحتوي requirements.txt على flask, pyodbc, gunicorn)
RUN pip install --no-cache-dir -r requirements.txt

# --- 4. أمر التشغيل النهائي ---
ENV PORT 8080
EXPOSE 8080
# استخدم Gunicorn لتشغيل التطبيق بشكل مستقر
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
