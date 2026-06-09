from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from math import ceil


class CarCreate(BaseModel):
    make: str = Field(max_length=100)
    model: str = Field(max_length=100)
    year: int


class RentRequest(BaseModel):
    renter_name: str = Field(max_length=100)


class CarResponse(BaseModel):
    id: UUID
    make: str
    model: str
    year: int
    is_available: bool
    rented_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class PaginatedCarsResponse(BaseModel):
    items: list[CarResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RentalRecordResponse(BaseModel):
    id: UUID
    car_id: UUID
    renter_name: str
    rented_at: datetime
    returned_at: Optional[datetime]
