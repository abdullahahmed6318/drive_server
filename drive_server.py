import os
import time
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cloudinary
import cloudinary.uploader
import cloudinary.api
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn

app = FastAPI()

# تفعيل CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 المفاتيح الخاصة بك من Cloudinary
CLOUDINARY_CLOUD_NAME = "nwakgxiv"
CLOUDINARY_API_KEY = "576472358429142"
CLOUDINARY_API_SECRET = "7DRxjE7n4Xi3Dsu0J05VsafgsLs"

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

# 📤 1. رفع الملف إلى Cloudinary
@app.post("/upload-to-drive")
async def upload_to_drive(image: UploadFile = File(...)):
    try:
        print(f"📥 جاري استقبال الملف: {image.filename}")
        contents = await image.read()

        # resource_type="auto" يتعامل مع الصور والفيديوهات بجميع الصيغ تلقائياً
        upload_result = cloudinary.uploader.upload(
            contents,
            folder="temp_pixelum_files",
            resource_type="auto"
        )

        public_id = upload_result.get("public_id")
        secure_url = upload_result.get("secure_url")
        resource_type = upload_result.get("resource_type", "image")

        print(f"✅ تم الرفع بنجاح إلى Cloudinary! Public ID: {public_id}")

        return {
            "status": "success",
            "file_id": f"{resource_type}:{public_id}",
            "file_url": secure_url
        }

    except Exception as e:
        print(f"❌ خطأ أثناء الرفع إلى Cloudinary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 🗑️ 2. حذف الملف من Cloudinary
@app.post("/delete-from-drive")
async def delete_from_drive(file_id: str = Form(...)):
    try:
        if ":" in file_id:
            res_type, pub_id = file_id.split(":", 1)
        else:
            res_type, pub_id = "image", file_id

        result = cloudinary.uploader.destroy(pub_id, resource_type=res_type)
        print(f"✅ تم حذف الملف بنجاح: {pub_id} ({result})")
        return {"status": "success", "deleted_id": file_id}
    except Exception as e:
        print(f"❌ خطأ في حذف الملف {file_id}: {str(e)}")
        return {"status": "error", "message": str(e)}

# 🧹 3. التنظيف الدوري (كل 30 دقيقة للملفات الأقدم من نصف ساعة)
def auto_cleanup_old_files():
    try:
        print("🧹 جاري فحص وتنظيف الملفات القديمة من Cloudinary...")
        for r_type in ["image", "video", "raw"]:
            resources = cloudinary.api.resources(
                type="upload",
                prefix="temp_pixelum_files/",
                resource_type=r_type,
                max_results=50
            ).get("resources", [])

            now = datetime.now(timezone.utc)
            for item in resources:
                created_at = datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if now - created_at > timedelta(minutes=30):
                    cloudinary.uploader.destroy(item["public_id"], resource_type=r_type)
                    print(f"🗑️ تم مسح الملف القديم: {item['public_id']}")
    except Exception as e:
        print(f"❌ خطأ في التنظيف الدوري: {e}")

@app.on_event("startup")
def start_cleanup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_cleanup_old_files, 'interval', minutes=15)
    scheduler.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
