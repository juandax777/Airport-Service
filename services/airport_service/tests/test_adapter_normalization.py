from services.airport_service.app.main import adapt_airport, normalize_coordinates


def test_normalize_coordinates_swaps_api_colombia_values() -> None:
    latitude, longitude = normalize_coordinates(-75.42037792, 6.166336066)

    assert latitude == 6.166336066
    assert longitude == -75.42037792


def test_normalize_coordinates_keeps_valid_colombia_values() -> None:
    assert normalize_coordinates(4.70159, -74.1469) == (4.70159, -74.1469)


def test_normalize_coordinates_handles_missing_and_invalid_values() -> None:
    assert normalize_coordinates(None, -74.0) == (None, -74.0)
    assert normalize_coordinates("not-a-number", -74.0) == (None, None)


def test_adapt_airport_extracts_nested_city_and_normalizes_coordinates() -> None:
    airport = adapt_airport(
        {
            "id": 45,
            "name": "Base Aérea BG. Arturo Lema Posada",
            "city": {"id": 1, "name": "Rionegro"},
            "latitude": -75.42037792,
            "longitude": 6.166336066,
        }
    )

    assert airport.id == "45"
    assert airport.city == "Rionegro"
    assert airport.latitude == 6.166336066
    assert airport.longitude == -75.42037792


def test_adapt_airport_supports_fallback_fields() -> None:
    airport = adapt_airport(
        {
            "_id": "SKBO",
            "airportName": "El Dorado",
            "municipality": "Bogotá",
            "coordinates": {"latitude": 4.70159, "longitude": -74.1469},
        }
    )

    assert airport.id == "SKBO"
    assert airport.name == "El Dorado"
    assert airport.city == "Bogotá"
    assert airport.latitude == 4.70159
    assert airport.longitude == -74.1469
