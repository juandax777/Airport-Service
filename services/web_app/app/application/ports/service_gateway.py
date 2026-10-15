from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ServiceResponse:
    content: bytes
    status_code: int
    media_type: str


class ServiceUnavailable(Exception):
    """Raised when an internal service cannot be reached."""


class ServiceGateway(Protocol):
    async def request(
        self,
        base_url: str,
        method: str,
        path: str,
        body: bytes,
        content_type: str,
    ) -> ServiceResponse: ...
