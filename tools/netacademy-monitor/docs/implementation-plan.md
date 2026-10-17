# Tennis Monitor Implementation Plan

Goal: implement docs/design.md using Python 3.12, Playwright, JSON state, GitHub Actions and Telegram.

1. Write tests for baseline, persistent restart, release confirmation, cancellation suppression, failures, malformed response parsing and outbox deduplication. Run to demonstrate missing implementation.
2. Implement state transitions in monitor/state.py and response validation in monitor/browser.py. Run tests.
3. Implement UI inspection, 55/110-minute slots, configured date boundary verification, screenshot-on-error and structured logs. Run live twice against the same state; confirm no outbox events.
4. Implement Telegram delivery with durable sending marker and conservative ambiguous-outcome handling, plus repeated-failure notification. Exercise tests for definite rejection and uncertain delivery.
5. Add hourly/manual GitHub Actions workflow with serialized execution, a durable state branch and credentials from GitHub Secrets. Add systemd alternative, environment template and README.
6. Run complete test suite, inspect repository for secrets, deploy to a dedicated private repository, run workflow twice, inspect persisted state and logs. Send test Telegram message if credentials are available. Report all unverified requirements precisely.

Review focus: midnight/month rollover, empty inventory vs network failure, past midnight slots retaining booking-date semantics, crash between send and acknowledgment, missing/corrupt persisted state. Tests and validation must fail closed for schema drift.
