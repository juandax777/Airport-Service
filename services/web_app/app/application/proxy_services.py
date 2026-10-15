from .ports.service_gateway import ServiceGateway, ServiceResponse


class ProxyInternalService:
    """Application use case routing web API calls to internal services."""

    def __init__(
        self,
        gateway: ServiceGateway,
        airport_service_url: str,
        itinerary_service_url: str,
    ) -> None:
        self.gateway = gateway
        self.airport_service_url = airport_service_url
        self.itinerary_service_url = itinerary_service_url

    async def airports(
        self, method: str, path: str, body: bytes, content_type: str
    ) -> ServiceResponse:
        return await self.gateway.request(
            self.airport_service_url,
            method,
            f"/api/v1/airports{path}",
            body,
            content_type,
        )

    async def itineraries(
        self, method: str, path: str, body: bytes, content_type: str
    ) -> ServiceResponse:
        return await self.gateway.request(
            self.itinerary_service_url,
            method,
            f"/api/v1/itineraries{path}",
            body,
            content_type,
        )
