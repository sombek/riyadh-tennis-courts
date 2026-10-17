# Live inspection and verification report

All observation timestamps below are Asia/Riyadh, UTC+3, on October 17, 2026.

## Findings

1. **Current furthest bookable calendar date:** Sunday, October 18, 2026, confirmed by public Chromium navigation and date-labelled live availability responses. Latest recorded check began at **17:54:46** and completed successfully after 15.012 seconds.
2. **Booking window:** the public serialized setting was `maxAdvanceBookingDays=1`. October 17 and 18 were enabled, and October 19 was disabled. The public window therefore currently extends one calendar day ahead, including today. This is evidence of a configured rolling window, not a measured multi-day release history.
3. **First observations of newly released dates:** none during this session. October 18 was already released when inspection began. The first persistent monitor baseline completed at **17:48:33**; that is a baseline time, not its release time.
4. **Probable daily release time:** not established. The browser UI computes the future boundary from its current calendar date plus the configured number of days, so midnight Riyadh is a hypothesis for when a fresh Riyadh-browser page would make another day selectable. Backend inventory could follow different timing. The site's separate 05:00 business-day start is not evidence that future dates release at 05:00. A midnight transition and repeated daily observations have not yet been observed. Hourly checks can bound a release between checks; they cannot identify an exact release second.
5. **End-to-end verified and deployed:** **No**. Local website extraction, persistent state, release-detection fixtures and duplicate suppression were verified. GitHub creation was denied and no repository destination has been selected. No scheduler has been deployed or observed firing. A real Telegram installation test was accepted at **18:01:39 Riyadh**, message ID **217**, with a durable `sent` acknowledgment.

## Live availability example

For October 18, the latest successful snapshot contained these available starts:

| Duration | Starts (Riyadh) |
|---|---|
| 55 minutes | 05:00, 06:00, 07:00, 15:00, 16:00, 23:00 |
| 110 minutes | 05:00, 06:00, 15:00 |

October 17 also exposed the venue-labelled post-midnight 00:00–00:55 slot, plus 23:00 starts for 55 and 110 minutes. Booking-date labels were preserved. Across both dates there were 12 date/duration slot combinations, not 12 distinct start times or courts. Availability can change after this report.

## Evidence and inspection method

- `verified-observations.json`: seven persisted successful live checks in separate processes, with real slots and no outbox alerts.
- `example-checks.jsonl`: actual execution logs. One early check needed three attempts before the date-link fix; later checks passed first attempt. Errors were recorded and were not converted into empty availability.
- `verified-calendar.png`: Chromium screenshot of the final public calendar selection.
- `october18-network.json`: sanitized real browser response fixture. Court identifiers/names/prices were removed, retaining actual booking dates, times, availability flags, HTTP status and response structure.
- Public availability is fetched through `POST /book?activity=tennis&type=court` using Next.js server actions, with `success/results/result/data` slot structures. It is not a demonstrated stable public JSON API. The implementation follows normal browser controls and supports the site's `date=YYYY-MM-DD` links, without replaying build-specific action IDs.
- Available returned slots have `is_available=true`; unavailable slots have `false`. Released calendar dates are independently identified by the public window and enabled calendar controls. A false flag alone cannot establish why a slot is unavailable; full occupancy, schedule omission and other restrictions may be indistinguishable.
- The site can refresh/reset click-selected dates. Supported date deep-links stabilized the inspected date. The extractor validates each response's date and actual duration to avoid misusing cached responses.

## Verification performed

- Python 3.12.14; Playwright 1.62.0; real system Chromium controlled by Playwright.
- Multiple successful real monitor invocations against the same atomic JSON state, latest bookable date consistently October 18, no newly released date, no duplicate release alerts.
- 20 automated tests passed: release fixture confirmation, baseline silence, restart persistence, cancellation suppression, fully booked releases, month rollover, corrupt/missing state, malformed/misdated/wrong-duration data, unlabeled empty responses, repeated failure health events and Telegram outbox edge cases.
- Real local Git bare-remote integration test confirmed the sending marker reaches the state branch before a controlled sender is called, and sent state prevents redelivery after restart. This verifies the Git persistence mechanism, not GitHub workflow execution or actual Telegram delivery.
- `systemd-analyze calendar '*-*-* *:00:00 Asia/Riyadh'` accepted the timer expression. Full service verification reported that `/opt/tennis-monitor/.venv/bin/python` does not exist in this environment; the documented VPS installation has not happened. GitHub workflow configuration passed actionlint v1.7.7 with no findings, but has not run on GitHub.
- Dockerfile supplied as an optional deployment artifact; image build and Docker runtime have not been verified.

## Precise remaining blockers

- `gh repo create sombek/netacademy-tennis-monitor --private` failed: `sombek does not have the correct permissions to execute CreateRepository`. No destination was created, no workflow was pushed and no scheduled checks are running.
- An existing repository destination or an owner-created private repository is required. The choice is pending; existing repositories were not modified.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are now configured privately for local execution and real delivery was accepted. They still need to be installed as Actions secrets in the selected repository; no secrets were committed or included in the source archive.
- GitHub Actions scheduling may be delayed/skipped. Permanent hosting and observed scheduled runs are required before calling this operational.

## Telegram verification update

The real monitor check beginning **18:01:24 Riyadh** parsed live availability, retained the existing baseline and delivered the explicitly labelled installation test through the Telegram Bot API. Telegram acknowledged message ID **217** at **18:01:39 Riyadh**. This verifies API acceptance, not whether the human has read the message. The durable outbox now records `test:installation.status=sent`. No booking-release alert was generated.

A second process beginning **18:01:48 Riyadh** completed successfully after one retry, retained the same sent message ID **217**, and attempted no further notification (`telegram_notification_succeeded=null`). The outbox contains exactly the one sent test event and no booking-release events.

## Hosted deployment attempt

Source and hourly workflow were deployed to the selected repository. Run [39047232614](https://github.com/sombek/riyadh-tennis-courts/actions/runs/39047232614) began the monitor at **18:56:49 Riyadh** on October 17. All 20 tests passed on the hosted runner, but the booking page returned **HTTP 429 on all three Chromium attempts**. No calendar data was accepted. The failure was persisted remotely without changing the baseline, losing seven earlier observations or creating booking alerts. The workflow was disabled after this failure, and no second hosted website check was attempted. Telegram secrets were also missing in that run. Monitoring is **not operational**. The owner confirmed receipt of the earlier locally sent Telegram test. See DEPLOYMENT_STATUS.md for the current blocker.

## Hosted Telegram verification

After the owner added the two repository secrets, isolated GitHub Actions run [39047482326](https://github.com/sombek/riyadh-tennis-courts/actions/runs/39047482326) sent test message **218** at **19:00:13 Riyadh** on October 17. A second run [39047522532](https://github.com/sombek/riyadh-tennis-courts/actions/runs/39047522532) succeeded using the same persisted sent event and did not resend. Both tests deliberately avoided the booking site. The October 18 baseline and seven successful availability observations were preserved. The availability workflow remains disabled because its HTTP 429 blocker is unresolved.

## Retry schedule update

At the user’s subsequent request, the availability workflow was re-enabled for checks every three hours (`0 */3 * * *` UTC, corresponding to 00:00/03:00/06:00/09:00/12:00/15:00/18:00/21:00 Asia/Riyadh). No immediate manual check was triggered by this change. This authorizes scheduled retries; it does not establish that the earlier HTTP 429 blocker has cleared.
