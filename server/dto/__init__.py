"""
חבילת ה-DTO (Data Transfer Objects)
מטרה: להגדיר את המבנה של הנתונים שעוברים בין הלקוח לשרת
DTOs הם מחלקות Pydantic שמבצעות ולידציה אוטומטית של הנתונים
"""

# ייבוא כל ה-DTO לנוחות שימוש
from dto.customer_dto import CustomerCreateDTO, CustomerResponseDTO
from dto.contractor_dto import ContractorCreateDTO, ContractorResponseDTO
from dto.concrete_request_dto import ConcreteRequestCreateDTO, ConcreteRequestResponseDTO
from dto.contractor_concrete_request_dto import (
    ContractorConcreteRequestCreateDTO,
    ContractorConcreteRequestResponseDTO,
)
from dto.strength_dto import StrengthCreateDTO, StrengthResponseDTO
from dto.reliant_dto import ReliantCreateDTO, ReliantResponseDTO
from dto.stone_size_dto import StoneSizeCreateDTO, StoneSizeResponseDTO
from dto.purpose_dto import PurposeCreateDTO, PurposeResponseDTO
from dto.concrete_type_dto import ConcreteTypeCreateDTO, ConcreteTypeResponseDTO
