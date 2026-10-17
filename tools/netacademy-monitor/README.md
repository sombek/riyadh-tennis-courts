# Net Academy tennis calendar monitor

Python 3.12 / Playwright Chromium monitor for https://netacademy.sa/book?activity=tennis&type=court. All dates and human-readable timestamps use **Asia/Riyadh (UTC+3)**. This monitors availability; it does not book or sign in.

**Current status:** real Chromium access and calendar/slot extraction verified locally. Baseline survives independent process executions, and unchanged availability produces no release alerts. A real Telegram test was accepted successfully on October 17 at 18:01:39 Riyadh (message ID 217). Credentials are configured privately for local execution; The selected deployment destination is `sombek/riyadh-tennis-courts`. Code pushes now work and the persistent state branch is initialized. Actions secret access is still denied to this connection; the owner must add the two secrets through GitHub settings. Hosted verification is pending. See DEPLOYMENT_STATUS.md. This is **not yet an operational deployed service**. See [inspection report](evidence/REPORT.md).

## How detection works

The normal calendar UI exposes a configurable booking window. Enabled dates inside that window are treated as released regardless of slot inventory. Public Next.js server-action responses provide per-slot `booking_date`, `start_time`, `end_time`, `is_available` and courts. No stable standalone public API was observed, so this uses Playwright and the site's supported date deep-links rather than hardcoded/replayed action IDs.

Both 55- and 110-minute options are inspected. Responses must match the expected booking date and duration and successful result schema. A failed/blocked request is an error, never an empty calendar. UI selection and configured boundary must agree; schema changes fail closed and produce screenshots and sanitized response summaries.

First success establishes a silent baseline. Later checks alert only for dates beyond the historical released-date boundary with slots available in **two fresh browser observations**. Dates already released, including fully booked dates, cannot generate release alerts if cancellations appear later. A day released with no slots is recorded without an availability alert. Boundary shrinkage does not reset the historical maximum.

`is_available=false` means no bookable inventory for that returned slot. It does not prove whether every court is reserved, a schedule is absent, or another venue restriction applies. The public response cannot always distinguish those causes. Disabled future dates beyond the configured window are unreleased. Membership-specific inventory is outside this public monitor's scope.

Venue booking-day labels are preserved: a `00:00` slot under October 17 is not silently reassigned to October 18. The site's business-day start includes yesterday before 05:00, while its configured future boundary is based on the current Riyadh calendar date. This is handled separately from the release time.

## Local run

Install [uv](https://docs.astral.sh/uv/), then:

```bash
uv sync --locked --python 3.12
uv run playwright install --with-deps chromium
cp .env.example .env
# Edit .env privately. Never commit or paste your bot token into logs.
set -a
. ./.env
set +a
uv run python -m scripts.initialize_state runtime/state.json
export REQUIRE_EXISTING_STATE=1
uv run python -m monitor
uv run python -m monitor
uv run python -m monitor --test-telegram
uv run python -m unittest discover -s tests -v
```

`--test-telegram` queues a single installation-test event, deduplicated by persisted state. The chat must have started the bot first. Get the token using Telegram's BotFather; obtain the chat ID from your own bot updates, then keep both in the environment or GitHub Secrets. No credentials are included here.

Exit status is nonzero for calendar failure, missing required Telegram configuration, pending/uncertain notifications, corrupted state or persistence failure. Without `REQUIRE_TELEGRAM=1`, local read-only checks may succeed with no credentials; this does not mean notification delivery has been verified.

## GitHub Actions deployment (no VPS)

Use a dedicated **private** repository because state and artifacts reveal your monitoring history. Source must be on the default branch for hourly schedules to run. This workspace's GitHub identity can read repositories, but repository creation was explicitly denied. Have the owner create a repository or select an existing destination before pushing.

1. Push this directory to the repository's default branch. Authenticate `git` using `gh auth setup-git` if needed.
2. From that source checkout, run `bash scripts/publish_state_branch.sh`. This creates the independent `monitor-state` branch **once**, containing `state.json`. It refuses to overwrite an existing branch. Do not protect that branch against the workflow's state updates; keep source protection separate. Initialize before enabling scheduled execution.
3. Add Actions secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` under repository Settings → Secrets and variables → Actions.
4. Ensure Actions is enabled and workflow permissions permit `contents: write`. Confirm branch rules allow state pushes.
5. Run **Tennis availability monitor** manually with `test_telegram=true`. Confirm the test message arrives and the run's state shows `test:installation.status=sent` with Telegram's message ID.
6. Run manually a second time; verify a second observation is persisted with no duplicate test or release notification.
7. Confirm at least one scheduled run, inspect logs/artifacts, and keep GitHub failure notifications enabled as a fallback if the monitor itself cannot reach Telegram.

Workflow: [../../.github/workflows/tennis-monitor.yml](../../.github/workflows/tennis-monitor.yml). It checks at `0 * * * *` UTC, which is also minute zero every Riyadh hour, supports manual dispatch, and serializes executions with one concurrency group. A long-running job cannot overlap another, though GitHub may coalesce pending runs. Runtime is bounded to 15 minutes; normal verified local checks took seconds.

**Timing limits:** GitHub scheduled workflows can be delayed or skipped, especially at minute zero. They cannot establish the exact release second. Scheduled-event logs label the current hour as an estimate because GitHub does not provide the intended firing timestamp. Manual runs record `scheduled_execution_time=null`. First observation bounds release between the previous successful check and discovery; observation history is needed before inferring a daily release time. GitHub plan minutes apply; no paid service was provisioned here.

### Durable state and notifications

GitHub state is stored on the non-expiring `monitor-state` branch, **not** Actions cache/artifacts. Every atomic state transition is committed and pushed before advancing. Workflow checkout fails if this branch disappears; `REQUIRE_EXISTING_STATE=1` prevents silent rebaselining. Local runs use atomic JSON replacement, file/directory fsync and an exclusive file lock. Back up the state branch; never reset state to solve a delivery error.

Alerts use a durable outbox. Three consecutive failed checks queue one separate `TENNIS MONITOR FAILURE` message per failure episode; successful parsing resets the streak. Health and booking messages have distinct text and IDs. Old sent outbox entries remain as deduplication records. An explicit Telegram rejection leaves an event pending for the next run.

Telegram `sendMessage` has no idempotency key. To prevent duplicates after a crash or ambiguous timeout, sending intent is persisted remotely **before** the request; interrupted/unknown outcomes become `uncertain` and are not automatically resent. A crash just before the request can therefore suppress an undelivered alert. Exactly-once guaranteed delivery is impossible with this API. Inspect the target chat and state before manually resolving an uncertain event. Only if confirmed absent, change its status to `pending` and push the state branch. A failed state push prevents sending.

## Optional always-on VPS

For better execution accuracy, provision a Linux VPS separately; no VPS is currently available. Install source at `/opt/tennis-monitor`, create an unprivileged `tennis-monitor` user, run `UV_PYTHON_INSTALL_DIR=/opt/tennis-monitor/python uv sync --locked --python 3.12` so managed Python remains accessible with `ProtectHome=true`, then install Chromium with:

```bash
PLAYWRIGHT_BROWSERS_PATH=/opt/tennis-monitor/browsers uv run playwright install --with-deps chromium
```

Put credentials in `/etc/tennis-monitor.env` with mode `0600` and initialize `/var/lib/tennis-monitor/state.json` once using `python -m scripts.initialize_state`. Ensure the service user owns `/var/lib/tennis-monitor` and `/var/log/tennis-monitor`, and can read the source, Python environment and browsers. Copy `deploy/tennis-monitor.service` and `.timer` into `/etc/systemd/system/`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tennis-monitor.timer
sudo systemctl start tennis-monitor.service
systemctl list-timers tennis-monitor.timer
journalctl -u tennis-monitor.service
systemd-analyze calendar '*-*-* *:00:00 Asia/Riyadh'
```

Timer uses `AccuracySec=1s`, zero randomized delay and persistent catch-up after restarts. The service manager prevents overlap. Source installation paths must exist before full unit verification. The optional Dockerfile supports a persistent `/data` mount; schedule container execution from the host. A continuously running scheduler is intentionally not embedded in the image.

## Logs and diagnostics

Every invocation emits JSON to stdout and `logs/checks.jsonl`: actual/scheduled time (or explicit unknown), scheduling-estimate flag, website-access result, parse result, latest bookable and released dates, date/slot counts, detected dates, notification status, duration, attempts and errors. `telegram_notification_succeeded=null` means no send was attempted. Missing credentials are reported separately. Example actual logs are in `evidence/example-checks.jsonl`.

Failures capture public-page screenshots, HTTP path/status/method and sanitized date/time/availability summaries, without cookies, authorization headers, bot tokens or account information. Actions retains diagnostic artifacts for 30 days. The durable observation history lives in state independently of artifact retention. Private authentication, CAPTCHA solving and bypasses are not implemented.

## Verification boundaries

Automated tests cover baseline/restarts, release confirmation, unchanged checks, cancellations, fully booked days, month rollover, state loss/corruption, malformed responses, cross-midnight slots, wrong date/duration, failure health episodes and Telegram outbox failure windows. Automated Telegram transport tests use a controlled sender. Separately, the real Telegram Bot API accepted the installation test (message ID 217); see the inspection report. Live evidence and remaining deployment blockers are reported explicitly in `evidence/REPORT.md`. Docker and VPS units have not been deployed here.

## Integration into riyadh-tennis-courts

Source lives under `tools/netacademy-monitor/`; the static court directory is unchanged. Run Python/uv commands from this directory. The workflow checks out the state branch inside this directory and keeps its own source/tests/logs separate from the website. Run the state-branch initialization helper from this directory; Git will find the repository origin in its parent checkout. Deployment verification is pending the two Actions secrets and successful hosted runs.
