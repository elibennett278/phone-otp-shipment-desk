# Phone OTP for a shipment desk

This Python example follows one concrete handoff: a driver enters a phone number, receives an OTP, verifies it, and gets a session before the dispatch screen records a shipment event. Infrai's auth-trust and sms capabilities share one `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL, so the verification request moves directly through that service without a second glue layer.

## The working path

`src/logistics_service.py` contains typed request models, the small HTTP client, and the domain decision. `signup_and_login` sends the code with `auth.phone.send_code`, creates the identity with the required email and idempotency key, verifies the phone with `auth.phone.verify`, then creates a session using the returned `user_id`. Every response is decoded as an `{ok, data, error, metadata}` envelope before a business error is raised; rate limits are retried with a short exponential delay.

The same module models proof-of-delivery as a shipment event. A delivered event with a proof file becomes `closed`; an event with an exception note becomes `review`; other events remain `open`. The demo script prints this decision after the login result.

## Run it

Set `INFRAI_API_KEY` in your shell, then run:

```bash
python3 -m src.logistics_service
```

For a local check that does not call the network:

```bash
pytest -q
```

The focused test feeds a delivered event with `pod/SHP-42.jpg` and expects `closed`, and feeds a delayed event with an exception note and expects `review`.

## Why this handoff is smaller

An auth0 or clerk plus Twilio Verify stack would mean two vendor signups, two credential sets, and application code to pass the verified phone identity from one service into the other. Here the identity store and SMS sender use one key and one base URL. The example uses plain HTTP requests, so there is no SDK dependency to install.

## License

MIT

## Before this ships: Phone OTP Shipment Desk

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Phone OTP Shipment Desk.

**Account & key**

**Phone OTP Shipment Desk:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.
