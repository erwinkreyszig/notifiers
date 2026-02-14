from itertools import chain

YOKOHAMA_BUS_URL_COMMON = "https://navi.hamabus.city.yokohama.lg.jp/koutuu/pc/location/BusOperationResult?courseId"
BUS_NUMBER_URL_MAP = {
    8: {
        "up": (
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600983",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600987",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600989",
        ),
        "down": (
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600980",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600990",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601028",
        ),
    },
    26: {
        "up": (
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600956",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600957",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600991",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601011",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601014",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601015",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601018",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601019",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601025",
        ),
        "down": (
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600961",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600975",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600982",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601008",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601012",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601027",
        ),
    },
    66: {
        "down": (
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601202",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601209",
        ),
    },
    58: {
        "up": (
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600736",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601047",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601180",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601243",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601403",
        ),
        "down": (
            f"{YOKOHAMA_BUS_URL_COMMON}=0001600730",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601000",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601043",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601241",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601404",
        ),
    },
    123: {
        "up": (
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601210",
            f"{YOKOHAMA_BUS_URL_COMMON}=0001601264",
        ),
        "down": (f"{YOKOHAMA_BUS_URL_COMMON}=0001601263",),
    },
    168: {
        "up": (f"{YOKOHAMA_BUS_URL_COMMON}=0001601182",),
        "down": (f"{YOKOHAMA_BUS_URL_COMMON}=0001601211",),
    },
}


def get_route_urls(route_number: int, direction: str | None = None) -> tuple:
    grouped_routes = BUS_NUMBER_URL_MAP[route_number]
    if not direction:
        return chain.from_iterable(grouped_routes.values())
    return grouped_routes[direction]
