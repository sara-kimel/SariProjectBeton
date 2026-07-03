"""
שירות אזורים גיאוגרפיים (Region Service) - שלד בלבד!
פונקציות לדוגמא לחישוב אזור גיאוגרפי מקואורדינטות
"""


class RegionService:
    """
    שירות לטיפול באזורים גיאוגרפיים
    שלד בלבד - דורש חיבור לשירות מפות חיצוני (כמו Google Maps) בעתיד
    """

    def get_region_from_coordinates(self, lat: float, lng: float) -> str:
        """
        קבלת שם האזור מקואורדינטות (lat, lng)
        TODO: לחבר לשירות Reverse Geocoding כמו Google Maps API
        השלבים הצפויים:
        1. שליחת בקשה ל-Google Maps API
        2. חילוץ שם העיר / אזור
        3. החזרת השם
        """
        raise NotImplementedError("יש לחבר לשירות מפות חיצוני")

    def get_nearby_regions(self, region: str, radius_km: float) -> list:
        """
        קבלת רשימת אזורים סמוכים ברדיוס נתון
        TODO: לממש מבנה נתונים של אזורים ומרחקים
        """
        raise NotImplementedError("יש לממש מיפוי אזורים")
