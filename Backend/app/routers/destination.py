
from fastapi import APIRouter, HTTPException, Query
import httpx

from app.services.geocoding_service import search_destination

router = APIRouter(
    prefix="/destinations",
    tags=["Destinations"],
)


@router.get("/search")
async def search_places(
    q: str = Query(..., min_length=2, max_length=150),
):
    try:
        results = await search_destination(q.strip())
        return results

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Destination search timed out. Please try again.",
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="The destination search service is temporarily unavailable.",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the destination search service.",
        )
