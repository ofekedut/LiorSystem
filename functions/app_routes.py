import dataclasses

from typing import Callable
from request_payload import RequestPayload

routes: dict[str, dict[str, Callable[[RequestPayload], dict]]] = {
    "GET": {},
    "DELETE": {},
    "POST": {},
    "PUT": {},
}


@dataclasses.dataclass
class RouteMetadata:
    name: str
    desc: str
    queryParams: dict
    body: dict
    auth: int
    package: str
    returns: type


routes_metadata: dict[str, dict[str, RouteMetadata]] = {
    "GET": {},
    "DELETE": {},
    "POST": {},
    "PUT": {},
}
