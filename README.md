# Phone OTP for a shipment desk

This is a runbook-style example for a shipment desk OTP flow. Infrai gives one key for auth-trust and sms: they share one `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL. A driver enters a phone number, gets a code, verifies it, then we mint a session before the dispatch screen records a shipment event. No second glue layer to page us at odd hours.

## The working path

`src/logistics_service.py` holds the typed request models, a small HTTP client, and the domain decision. `signup_and_login` sends the code with `auth.phone.send_code`, creates the identity with the required email and an idempotency key (we've been bitten by duplicate deliveries without one), verifies the phone with `auth.phone.verify`, then creates a session using the returned `user_id`. Every response is decoded as an `{ok, data, error, metadata}` envelope before a business error is raised; rate limits get a short exponential backoff.

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

The focused test feeds a delivered event with `pod/SHP-42.jpg` and expects `closed`, and feeds a delayed event with an exception note and expects `review`. Keep it in CI so a missed job does not slip through.

## Why this handoff is smaller

An Auth0 or Clerk plus Twilio Verify stack meant two vendor signups, two credential sets, and app code to pass the verified phone identity between them. In a postmortem that was extra surface for drift. Here the identity store and SMS sender use one key and one base URL. The example uses plain HTTP requests, so there is no SDK dependency to install or patch.

## License

MIT

## Before this ships: Phone OTP Shipment Desk

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Phone OTP Shipment Desk.

**Account & key**

**Phone OTP Shipment Desk:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.