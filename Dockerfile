FROM python:3.10-slim

# تثبيت مكتبات النظام لـ ODBC
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean

WORKDIR /app
COPY . .

# تحديث pip وتثبيت المكتبات
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# أمر التشغيل
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
