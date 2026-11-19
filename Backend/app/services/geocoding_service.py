import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Verified local landmark database for immediate fallback & offline reliability
LOCAL_LANDMARKS = [
    {
        "name": "Bhubaneswar Railway Station",
        "display_name": "Bhubaneswar Railway Station, Master Canteen, Khordha, Odisha",
        "latitude": 20.2667774,
        "longitude": 85.8435592,
    },
    {
        "name": "KIIT University (Campus 6)",
        "display_name": "KIIT University Campus 6, Patia, Bhubaneswar, Odisha, 751024",
        "latitude": 20.354563,
        "longitude": 85.816109,
    },
    {
        "name": "Patia Chowk",
        "display_name": "Patia Square, Nandankanan Road, Patia, Bhubaneswar, Odisha",
        "latitude": 20.360120,
        "longitude": 85.823450,
    },
    {
        "name": "Infocity / DLF Cybercity",
        "display_name": "Infocity Road, Chandrasekharpur, Bhubaneswar, Odisha, 751024",
        "latitude": 20.345800,
        "longitude": 85.808900,
    },
    {
        "name": "Jayadev Vihar Overbridge",
        "display_name": "Jayadev Vihar Overbridge, National Highway 16, Bhubaneswar, Odisha",
        "latitude": 20.298000,
        "longitude": 85.823000,
    },
    {
        "name": "Esplanade One Mall",
        "display_name": "Esplanade One Mall, Rasulgarh Industrial Estate, Bhubaneswar, Odisha",
        "latitude": 20.296500,
        "longitude": 85.864000,
    },
    {
        "name": "Master Canteen Square",
        "display_name": "Master Canteen Square, Janpath, Kharvela Nagar, Bhubaneswar, Odisha",
        "latitude": 20.270000,
        "longitude": 85.844000,
    },
    {
        "name": "AIIMS Bhubaneswar",
        "display_name": "All India Institute of Medical Sciences (AIIMS), Sijua, Patrapada, Bhubaneswar, Odisha",
        "latitude": 20.228500,
        "longitude": 85.776500,
    },
    {
        "name": "Biju Patnaik International Airport",
        "display_name": "Biju Patnaik International Airport (BBI), Airport Road, Bhubaneswar, Odisha",
        "latitude": 20.244400,
        "longitude": 85.817800,
    },
    {
        "name": "KIMS Super Speciality Hospital",
        "display_name": "KIMS Hospital, KIIT Campus 5, Patia, Bhubaneswar, Odisha",
        "latitude": 20.352000,
        "longitude": 85.817500,
    },
    {
        "name": "Nayapalli / IRC Village",
        "display_name": "Nayapalli, IRC Village, Bhubaneswar, Odisha, 751015",
        "latitude": 20.297000,
        "longitude": 85.817000,
    },
    {
        "name": "Saheed Nagar",
        "display_name": "Saheed Nagar, Maharshi College Road, Bhubaneswar, Odisha, 751007",
        "latitude": 20.288000,
        "longitude": 85.845000,
    },
    {
        "name": "Khandagiri Caves",
        "display_name": "Udayagiri and Khandagiri Caves, Khandagiri, Bhubaneswar, Odisha",
        "latitude": 20.260000,
        "longitude": 85.786500,
    },
    {
        "name": "Apollo Hospital Bhubaneswar",
        "display_name": "Apollo Hospitals, Samantpuri, Sainik School Road, Bhubaneswar, Odisha",
        "latitude": 20.306000,
        "longitude": 85.835000,
    },
    {
        "name": "Baramunda ISBT Bus Stand",
        "display_name": "Baramunda Inter State Bus Terminal (ISBT), Baramunda, Bhubaneswar, Odisha",
        "latitude": 20.275000,
        "longitude": 85.795000,
    },
    {
        "name": "Utkal University (Vani Vihar)",
        "display_name": "Utkal University, Vani Vihar, Rasulgarh, Bhubaneswar, Odisha",
        "latitude": 20.302000,
        "longitude": 85.850000,
    },
]


def match_local_landmarks(place: str):
    tokens = [t.strip().lower() for t in place.replace(",", " ").split() if len(t.strip()) >= 2]
    matched = []
    for lm in LOCAL_LANDMARKS:
        haystack = f"{lm['name']} {lm['display_name']}".lower()
        if any(t in haystack for t in tokens):
            matched.append(lm)
    return matched


async def search_destination(place: str):
    params = {
        "q": place,
        "format": "jsonv2",
        "limit": 5,
        "addressdetails": 1,
    }

    headers = {
        "User-Agent": "NariKavach-SafetyApp/1.0 (safety-routing@narikavach.internal)"
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
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

        if destinations:
            return destinations
    except Exception as e:
        print(f"[Geocoding Warning] External Nominatim query failed ({e}), using local landmarks directory.")

    # Fallback to local landmark directory
    local_matches = match_local_landmarks(place)
    if local_matches:
        return local_matches

    # If no token matched, return top 4 prominent hubs
    return LOCAL_LANDMARKS[:4]
