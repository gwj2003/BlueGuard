from fastapi import APIRouter

from services.geocoding import geocoding_service


router = APIRouter(prefix="/api", tags=["geo"])


@router.get("/geocode")
def geocode(address: str):
    return geocoding_service.geocode(address)


@router.get("/reverse-geocode")
def reverse_geocode(lat: float, lon: float):
    return geocoding_service.reverse_geocode(lat, lon)
