FROM python:3.10-slim

# تثبيت مكتبات النظام الأساسية فقط
RUN apt-get update && apt-get install -y gcc g++ && apt-get clean

WORKDIR /app

# نسخ المكتبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# أمر التشغيل
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
