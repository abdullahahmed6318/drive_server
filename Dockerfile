# تحديد الصورة الأساسية لبايثون
FROM python:3.10-slim

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# فتح البورت المطلوب
EXPOSE 8080

# أمر تشغيل السيرفر (تأكد من وجود كلمة CMD في البداية هكذا)
CMD ["uvicorn", "drive_server:app", "--host", "0.0.0.0", "--port", "8080"]
