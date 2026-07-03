"""
קובץ ראשי של האפליקציה (FastAPI Entry Point)
זה הקובץ שמרים את השרת ומחבר את כל ה-Controllers
להרצה: uvicorn app:app --reload
"""

from fastapi import FastAPI                          # פריימוורק לשרת
from fastapi.middleware.cors import CORSMiddleware   # מאפשר חיבור מ-Frontend

from config import settings                           # הגדרות (כולל CORS)

# ייבוא כל ה-routers מהשכבת controller
from controller.auth_controller import router as auth_router
from controller.customer_controller import router as customer_router
from controller.contractor_controller import router as contractor_router
from controller.concrete_request_controller import router as concrete_request_router
from controller.contractor_concrete_request_controller import router as contractor_offer_router
from controller.match_controller import router as match_router
from controller.notification_controller import router as notification_router
from controller.admin_controller import router as admin_router
from controller.strength_controller import router as strength_router
from controller.reliant_controller import router as reliant_router
from controller.stone_size_controller import router as stone_size_router
from controller.purpose_controller import router as purpose_router
from controller.concrete_type_controller import router as concrete_type_router


# יצירת אפליקציית FastAPI עם תיאור ושם
app = FastAPI(
    title="Beton API - תיווך שאריות בטון",
    description="""
    שרת לתיווך בין קבלנים עם שאריות בטון לבין לקוחות שצריכים כמות מועטה של בטון.

    תיעוד אינטראקטיבי זמין ב:
    - Swagger UI: /docs
    - ReDoc: /redoc
    """,
    version="1.0.0"
)


# הוספת CORS — מוגבל ל-origins של הלקוח (config/CORS_ORIGINS). שלב 6:
# בעבר היה "*"; כעת רשימת origins מפורשת (ברירת מחדל = Vite בפיתוח).
# ניתן לעקוף ל-"*" בפיתוח בלבד ע"י CORS_ORIGINS=* ב-.env.
_origins = settings.cors_origin_list
_allow_all = _origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _origins,
    # עם "*" אי אפשר גם credentials (מדיניות CORS); בפיתוח מוותרים על credentials
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


# חיבור כל ה-routers לאפליקציה
app.include_router(auth_router)                # /auth, /admin/users/.../reset-password
app.include_router(customer_router)            # /customers
app.include_router(contractor_router)          # /contractors
app.include_router(concrete_request_router)    # /concrete-requests
app.include_router(contractor_offer_router)    # /contractor-offers
app.include_router(match_router)               # /matches
app.include_router(notification_router)        # /notifications
app.include_router(admin_router)               # /admin/users, /admin/stats
app.include_router(strength_router)            # /strengths
app.include_router(reliant_router)             # /reliants
app.include_router(stone_size_router)          # /stone-sizes
app.include_router(purpose_router)             # /purposes
app.include_router(concrete_type_router)       # /concrete-types


# נקודת קצה בסיסית לבדיקה שהשרת חי
@app.get("/", tags=["Health Check"])
def root():
    """
    בדיקה שהשרת רץ
    GET / מחזיר הודעת ברוכים הבאים
    """
    return {
        "message": "ברוכים הבאים ל-Beton API",
        "docs": "/docs",
        "status": "ok"
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    """בדיקת בריאות פשוטה לשרת"""
    return {"status": "healthy"}


# הרצה ישירה - אם מריצים python app.py
if __name__ == "__main__":
    import uvicorn
    # הרצת השרת על host 0.0.0.0 ופורט 8000 - אפשר לגשת מכל מקום
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)

