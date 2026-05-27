from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.models.schemas import CarCreate, RentRequest, CarResponse, RentalRecordResponse
from app.services.car_service import CarService
from app.dependencies import get_car_service
from app.exceptions import CarNotFoundError, CarNotAvailableError, CarNotRentedError
from app.limiter import limiter

router = APIRouter(prefix="/cars", tags=["cars"])


# /cars/rentals MUST be defined before /cars/{car_id} to avoid UUID parse conflict
@router.get("/rentals", response_model=list[RentalRecordResponse])
async def list_rentals(service: CarService = Depends(get_car_service)):
    return await service.list_rental_records()


@router.get("", response_model=list[CarResponse])
async def list_cars(
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    available: Optional[bool] = None,
    service: CarService = Depends(get_car_service),
):
    return await service.list_cars(make=make, model=model, year=year, available=available)


@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car_id: UUID, service: CarService = Depends(get_car_service)):
    try:
        return await service.get_car(car_id)
    except CarNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")


@router.post("", response_model=CarResponse)
async def add_car(data: CarCreate, service: CarService = Depends(get_car_service)):
    return await service.add_car(data)


@router.post("/{car_id}/rent", response_model=CarResponse)
@limiter.limit("5/minute")
async def rent_car(
    request: Request,
    car_id: UUID,
    data: RentRequest,
    service: CarService = Depends(get_car_service),
):
    try:
        return await service.rent_car(car_id, data)
    except CarNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    except CarNotAvailableError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Car is already rented")


@router.post("/{car_id}/return", response_model=CarResponse)
async def return_car(car_id: UUID, service: CarService = Depends(get_car_service)):
    try:
        return await service.return_car(car_id)
    except CarNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    except CarNotRentedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Car is not currently rented")
