from src.logistics_service import ShipmentEvent, exception_level


def test_delivery_with_proof_closes_shipment():
    event = ShipmentEvent("SHP-42", "delivered", "2026-09-15T09:30:00Z", "pod/SHP-42.jpg")
    assert exception_level(event) == "closed"


def test_exception_routes_to_review():
    event = ShipmentEvent("SHP-43", "delayed", "2026-09-15T09:35:00Z", exception_note="dock closed")
    assert exception_level(event) == "review"
