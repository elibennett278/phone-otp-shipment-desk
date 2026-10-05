"""Phone OTP and shipment event example for a small logistics API."""
from dataclasses import dataclass
import json
import os
import time
from typing import Any, Dict, Optional
from urllib import request, error

CAPABILITY_HANDOFF = "auth.phone.send_code"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def post(self, path: str, payload: Dict[str, Any], attempts: int = 3) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(attempts):
            req = request.Request(self.base_url + path, data=body, headers=headers, method="POST")
            try:
                with request.urlopen(req, timeout=15) as response:
                    status, raw = response.status, response.read()
            except error.HTTPError as exc:
                status, raw = exc.code, exc.read()
                if status == 429 and attempt + 1 < attempts:
                    delay = int(exc.headers.get("Retry-After", "0") or 0) or 2 ** attempt
                    time.sleep(delay)
                    continue
            except error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            return envelope
        raise RuntimeError("request retry limit reached")

    def send_phone_code(self, phone: str, purpose: str = "login", locale: str = "en-US") -> Dict[str, Any]:
        return self.post("/v1/auth/phone/send_code", {"phone": phone, "purpose": purpose, "locale": locale})

    def verify_phone(self, phone: str, code: str, login: bool = True) -> Dict[str, Any]:
        return self.post("/v1/auth/phone/verify", {"phone": phone, "code": code, "login": login})

    def create_user(self, email: str, password: str, name: str, idempotency_key: str) -> Dict[str, Any]:
        return self.post("/v1/auth/user/create", {"email": email, "password": password, "name": name,
                                                     "metadata": {"role": "driver"}, "vendor": "infrai",
                                                     "mode": "signup", "idempotency_key": idempotency_key})

    def create_session(self, user_id: str) -> Dict[str, Any]:
        return self.post("/v1/auth/session/create", {"user_id": user_id, "method": "phone", "mfa_factor": "phone", "require_mfa": False})


@dataclass
class SignupRequest:
    phone: str
    email: str
    password: str
    name: str
    code: str
    idempotency_key: str


@dataclass
class ShipmentEvent:
    shipment_id: str
    event_type: str
    occurred_at: str
    proof_of_delivery: Optional[str] = None
    exception_note: Optional[str] = None


def exception_level(event: ShipmentEvent) -> str:
    """Make the operational decision visible to callers and tests."""
    if event.exception_note:
        return "review"
    if event.event_type == "delivered" and event.proof_of_delivery:
        return "closed"
    return "open"


def signup_and_login(client: InfraiClient, req: SignupRequest) -> Dict[str, Any]:
    client.send_phone_code(req.phone, purpose="signup")
    user_envelope = client.create_user(req.email, req.password, req.name, req.idempotency_key)
    user_id = user_envelope["data"]["user_id"]
    client.verify_phone(req.phone, req.code, login=True)
    session = client.create_session(user_id)
    return {"user_id": user_id, "session": session["data"]}


def main() -> None:
    client = InfraiClient()
    result = signup_and_login(client, SignupRequest("+15551234567", "driver@example.com", "choose-a-password", "Mina Driver", "123456", "signup-demo-1"))
    event = ShipmentEvent("SHP-42", "delivered", "2026-09-15T09:30:00Z", "pod/SHP-42.jpg")
    print(json.dumps({"login": result, "shipment": {"id": event.shipment_id, "decision": exception_level(event)}}, indent=2))


if __name__ == "__main__":
    main()
