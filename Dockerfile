FROM python:3.10-slim

# تحديث النظام وتثبيت تعريفات ODBC (السطور دي لازم تتنفذ)
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

# سطر إضافي لكسر الكاش - هنغير التاريخ ده لو منفعش
ENV CACHE_BYPASS=2025-12-19-v1

WORKDIR /app

# نسخ الملفات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# أمر التشغيل
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
