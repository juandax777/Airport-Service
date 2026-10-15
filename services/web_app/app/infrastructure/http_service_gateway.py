import httpx

from ..application.ports.service_gateway import ServiceResponse, ServiceUnavailable


class HttpxServiceGateway:
    """HTTP adapter for the internal Airport and Itinerary services."""

    async def request(
        self,
        base_url: str,
        method: str,
        path: str,
        body: bytes,
        content_type: str,
    ) -> ServiceResponse:
        headers = {"content-type": content_type}
        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=15) as client:
                upstream = await client.request(
                    method, path, content=body or None, headers=headers
                )
        except httpx.HTTPError as exc:
            raise ServiceUnavailable from exc
        return ServiceResponse(
            content=upstream.content,
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type", "application/json"),
        )
