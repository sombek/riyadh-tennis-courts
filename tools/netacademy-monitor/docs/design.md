# Tennis availability monitor design

Goal: observe the first confirmed public release of tennis reservation calendar days at Net Academy, with Riyadh timestamps and Telegram notification. No booking, authentication bypass or access-control bypass.

Use Python 3.12 and Playwright Chromium. Inspection proved the public calendar has maxAdvanceBookingDays=1, and slot fetches use a Next.js server action on POST /book?activity=tennis&type=court. No stable public JSON API was observed. Follow the normal UI and parse validated availability results from its responses. Capture screenshot and only sanitized diagnostics on failures.

Extract all enabled calendar days through the configured boundary, including zero-slot dates; confirm the day beyond the boundary is disabled. Inspect 55 and 110 minute durations. A released day with zero available slots is not an unreleased day. Future disabled dates beyond the configured window are unreleased; an in-window zero-slot date has no public inventory (fully booked or no schedule; these causes cannot always be distinguished).

JSON persistent state records released-date high water mark, all observed dates, observation history, failure streak and an alert outbox. Initial successful check establishes baseline. New release candidates must be beyond the historical boundary and have available slots in two fresh browser observations. Already released dates never generate release alerts when cancellations appear. Failed checks never replace the availability baseline.

Write state atomically and serialize runs. GitHub Actions checks hourly at minute zero UTC (also minute zero Riyadh), with manual execution and global concurrency. A separate monitor-state branch stores state; each outbox transition is pushed before notification. No cache or expiring artifact is authoritative state. Logs/artifacts are diagnostics only.

Telegram Bot API has no idempotency key: exactly-once delivery cannot be guaranteed across an ambiguous timeout or crash. Persist sending before delivery; uncertain sends are not retried automatically to prevent duplicate alerts. Surface uncertain outcomes in state/logs and fail the run for operator review. Definite rejection can be retried. Repeated website failures generate separate health messages after three failures, one per failure episode.

GitHub scheduled execution may be delayed or skipped; report observed time, nominal scheduled hour, delay and observation interval. Never present first observation time as proven release time. A systemd timer is provided for a future always-on VPS. This environment is not permanent hosting.

Completion requires live inspection, real repeated monitor runs, fixture tests, persistent state tests, deployed workflow runs and successful Telegram delivery. Missing credentials block end-to-end completion, not development or live read-only verification.
