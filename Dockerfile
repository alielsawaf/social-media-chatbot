# استخدام نسخة بايثون رسمية
FROM python:3.9-slim

# تثبيت الحزم الأساسية ودرايفر ميكروسوفت
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    gcc \
    g++ \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean

# ضبط مجلد العمل
WORKDIR /app
COPY . .

# تثبيت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت باستخدام gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
