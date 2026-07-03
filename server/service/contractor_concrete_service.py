from repository.contractor_concrete_request_repository import ContractorConcreteRequestRepository
from dto.contractor_concrete_request_dto import ContractorConcreteRequestCreateDTO
from service.price_service import double_price_from_string
from sqlalchemy.orm import Session

class ContractorConcreteService:
    """Service layer עבור הצעות קבלנים"""

    def __init__(self, db: Session):
        self.repo = ContractorConcreteRequestRepository(db)

    def create_offer(self, dto: ContractorConcreteRequestCreateDTO):
        # מכפילה את המחיר לפני שמגיעה ל-DB
        dto.price = double_price_from_string(dto.price)
        return self.repo.create(dto)

    def update_offer(self, request_id: int, dto: ContractorConcreteRequestCreateDTO):
        # אם יש מחיר חדש, הכפל
        if dto.price is not None:
            dto.price = double_price_from_string(dto.price)
        return self.repo.update(request_id, dto)