#פה אני עושה פילטור פה אזמן כל פעם פונקציה אחרת
#אך מתוך הcontroller  אזמן את הפונקציה הראשית
#from service.contractor_concrete_request_service import get_nearby_candidates

from fastapi.params import Depends
#def find_candidates(
  #  db,
   # lat: float,
   # lng: float,
   # radius_meters: int = 10000
#):
  #  service = get_nearby_candidates(db)

   # return service.get_nearby_candidates(
    #    lat=lat,
     #   lng=lng,
     #   radius_meters=radius_meters
    #)
from starlette.middleware.sessions import Session

from controller.concrete_type_controller import router
from database import get_db
from repository import ContractorConcreteRequestRepository
from sqlalchemy import text

#פונקציה שעושה
# פונקציה שמבצעת קריאה ל-Stored Procedure בשם GetCandidateRequests.
# הפונקציה מקבלת מיקום גיאוגרפי (קו רוחב וקו אורך), מזהה סוג בטון,
# כמות נדרשת ורדיוס חיפוש במטרים.
# הנתונים נשלחים למסד הנתונים באמצעות SQLAlchemy.
# תוצאות ה-Stored Procedure מומרות לרשימת מילונים (List[Dict]),
# כאשר כל מילון מייצג רשומה אחת שהוחזרה מהשאילתה.
# בסיום הפונקציה מדפיסה את התוצאות לקונסול ומחזירה אותן למשתמש.
class CandidateSelector:
    def __init__(self, db):
        self.db = db


    def get_candidate_requests(
        self,
        lat: float,
        lng: float,
        concrete_id: int,
        required_quantity: float,
        radius_meters: float
    ):
        result = self.db.execute(
            text("""
                EXEC GetCandidateRequests
                    @Lat = :lat,
                    @Lng = :lng,
                    @ConcreteId = :concrete_id,
                    @RequiredQuantity = :required_quantity,
                    @RadiusMeters = :radius_meters
            """),
            {
                "lat": lat,
                "lng": lng,
                "concrete_id": concrete_id,
                "required_quantity": required_quantity,
                "radius_meters": radius_meters
            }
        )

        candidates = [dict(row._mapping) for row in result]

        print(candidates)

        return candidates


