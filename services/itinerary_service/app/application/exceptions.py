class AirportsMustDiffer(Exception):
    """Raised when an itinerary has the same departure and arrival airport."""


class AirportDoesNotExist(Exception):
    def __init__(self, airport_id: str):
        self.airport_id = airport_id
        super().__init__(f"Airport {airport_id} does not exist")


class AirportServiceUnavailable(Exception):
    """Raised when Airport Service cannot validate an airport."""


class ItineraryNotFound(Exception):
    """Raised when a requested itinerary is absent."""


class EventPublicationFailed(Exception):
    """Raised after persistence succeeds but publishing the creation event fails."""
