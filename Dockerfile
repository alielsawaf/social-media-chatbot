# ابدأ بصورة Python رسمية (مبنية على Debian)
FROM python:3.10-slim

# تعيين مجلد العمل
WORKDIR /usr/src/app

# --- 1. تثبيت حزم نظام التشغيل الأساسية ---
# تثبيت الأدوات المساعدة و unixODBC، وهي متطلبات مسبقة للدرايفر
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        curl \
        gnupg \
        lsb-release \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- 2. إعداد مستودع Microsoft وتثبيت الدرايفر ODBC 17 ---
# هذا الجزء هو الأكثر عرضة للفشل، وقد تم تبسيطه ليكون أكثر موثوقية
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-tools.list \
    && apt-get update \
    # تثبيت درايفر ODBC 17 (الاسم المستخدم في سلسلة الاتصال)
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- 3. نسخ ملفات التطبيق ---
COPY . .

# --- 4. تثبيت مكتبات Python (بما فيها pyodbc) ---
RUN pip install --no-cache-dir -r requirements.txt

# --- 5. أمر التشغيل (Gunicorn) ---
ENV PORT 8080
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
