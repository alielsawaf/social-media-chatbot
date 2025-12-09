# 1. المرحلة الأساسية: استخدام صورة Python رسمية خفيفة
FROM python:3.10-slim

# 2. تحديد مجلد العمل داخل الحاوية
WORKDIR /usr/src/app

# 3. تثبيت درايفر ODBC 17 لـ SQL Server على نظام Linux
# هذه الأوامر ضرورية لتثبيت الدرايفر كـ System Package
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # الحزم الأساسية المطلوبة لعمل الدرايفر
        unixodbc \
        unixodbc-dev \
        curl \
        gnupg \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-tools.list \
    && apt-get update \
    # تثبيت درايفر ODBC 17
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. نسخ ملفات التطبيق
COPY . .

# 5. تثبيت مكتبات Python (بما فيها pyodbc)
# يجب أن يكون ملف requirements.txt يحتوي على pyodbc
RUN pip install --no-cache-dir -r requirements.txt

# 6. تحديد المنفذ (عادة ما يكون 5000 أو يتم تحديده عبر Railway)
ENV PORT 8080
EXPOSE 8080

# 7. أمر التشغيل النهائي للتطبيق
# تأكد من أن 'app' هو اسم ملفك و 'app' هو اسم متغير تطبيق Flask
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
