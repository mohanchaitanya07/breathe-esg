from math import asin, cos, radians, sin, sqrt

AIRPORTS = {
    "BLR": (13.1986, 77.7066),
    "DEL": (28.5562, 77.1000),
    "BOM": (19.0896, 72.8656),
    "MAA": (12.9941, 80.1709),
    "HYD": (17.2403, 78.4294),
    "CCU": (22.6547, 88.4467),
    "SIN": (1.3644, 103.9915),
    "DXB": (25.2532, 55.3657),
    "LHR": (51.4700, -0.4543),
    "JFK": (40.6413, -73.7781),
    "FRA": (50.0379, 8.5622),
    "PNQ": (18.5821, 73.9197),
    "AGR": (27.1558, 77.9609),
    "MAS": (13.0827, 80.2707),
}


EARTH_R_KM = 6371.0

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_R_KM * asin(sqrt(a))


def route_distance_km(origin: str, destination: str) -> float | None:
    o = AIRPORTS.get((origin or "").strip().upper())
    d = AIRPORTS.get((destination or "").strip().upper())
    if not o or not d:
        return None
    return haversine_km(o[0], o[1], d[0], d[1])
