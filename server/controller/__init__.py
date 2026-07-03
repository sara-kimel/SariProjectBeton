"""
חבילת ה-Controller
מטרה: לחשוף את ה-API החוצה דרך FastAPI Routers
כל מודול מחזיק router אחד לישות
"""

from controller.customer_controller import router as customer_router
from controller.contractor_controller import router as contractor_router
from controller.concrete_request_controller import router as concrete_request_router
from controller.contractor_concrete_request_controller import router as contractor_concrete_request_router
from controller.strength_controller import router as strength_router
from controller.reliant_controller import router as reliant_router
from controller.stone_size_controller import router as stone_size_router
from controller.purpose_controller import router as purpose_router
from controller.concrete_type_controller import router as concrete_type_router
