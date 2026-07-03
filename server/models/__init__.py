"""
חבילת המודלים - מכילה את כל מחלקות ה-ORM שמייצגות את טבלאות ה-DB
ייבוא של כל המודלים כדי שאפשר יהיה להשתמש בהם בקלות מנקודה אחת
"""

from models.customer import Customer                                # מודל לקוחות
from models.contractor import Contractor                            # מודל קבלנים
from models.admin import Admin                                      # מודל מנהלים
from models.concrete_request import ConcreteRequest                 # מודל בקשות לקוח
from models.contractor_concrete_request import ContractorConcreteRequest  # מודל הצעות קבלן
from models.strength import Strength                                # מודל חוזק
from models.reliant import Reliant                                  # מודל סומך
from models.stone_size import StoneSize                             # מודל גודל אבן
from models.purpose import Purpose                                  # מודל קטגוריית מטרה
from models.concrete_type import ConcreteType                       # מודל סוג בטון
from models.offer_match import OfferMatch                           # מודל התאמות (שלב 3)
from models.notification import Notification                        # מודל התראות (שלב 4)
