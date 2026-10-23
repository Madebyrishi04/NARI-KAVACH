
import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def search_destination(place: str):
    params = {
        "q": place,
        "format": "jsonv2",
        "limit": 5,
        "addressdetails": 1,
    }

    headers = {
        "User-Agent": "PersonalSafetyApp/1.0"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        results = response.json()

    destinations = []

    for result in results:
        destinations.append({
            "name": result.get("name") or result.get("display_name"),
            "display_name": result.get("display_name"),
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
        })

    return destinations
