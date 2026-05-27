from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Car(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    make: str
    model: str
    year: int
    is_available: bool = True
    rented_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class RentalRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    car_id: UUID
    renter_name: str
    rented_at: datetime = Field(default_factory=utcnow)
    returned_at: Optional[datetime] = None
