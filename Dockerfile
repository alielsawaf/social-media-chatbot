# هذا هو الجزء الذي يجب التركيز عليه في Dockerfile

# 1. تثبيت الحزم الأساسية و unixODBC
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        curl \
        gnupg \
        lsb-release \
    # إزالة الملفات المؤقتة لتصغير حجم الصورة
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 2. إضافة مستودع Microsoft وتثبيت الدرايفر
# نستخدم الأمر الرسمي لتثبيت المستودع والدرايفر
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-tools.list \
    && apt-get update \
    # تثبيت درايفر ODBC 17
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17
