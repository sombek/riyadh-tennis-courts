# Deployment status: installed, paused after live hosted access failure

Repository: sombek/riyadh-tennis-courts.
Workflow: .github/workflows/tennis-monitor.yml.
Run evidence: https://github.com/sombek/riyadh-tennis-courts/actions/runs/39047232614

The source and hourly workflow are on the default branch. Existing website files were not edited. Code pushes, workflow dispatch and workflow status inspection now work.

The hosted run beginning October 17, 2026 at 18:56:49 Asia/Riyadh installed Python and Chromium, passed all 20 automated tests, and loaded the persistent state branch. However, every real browser navigation attempt returned HTTP 429 (Too Many Requests). Calendar parsing failed. This establishes the observed HTTP failure, not its exact server-side cause or a permanent block on every GitHub runner.

The failure was committed to monitor-state at 18:57:00 Riyadh. The baseline remained October 18; all seven previous successful observations and the sent installation-test record were preserved. No new booking date or release notification was recorded. This verifies hosted failure-state persistence, not successful hosted availability inspection.

The workflow is explicitly disabled (disabled_manually) to avoid repeated failed hourly requests. No further live target inspection was attempted after identifying this hosted-access blocker. Monitoring is NOT operational.

The hosted run also had no Telegram secrets. GitHub still denies this connection access to the repository Actions secret public key (HTTP 403). The owner can add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID through repository Settings > Secrets and variables > Actions. Adding secrets alone does not resolve the live website HTTP 429.

Next deployment work requires a legitimate always-on execution host that can inspect this public booking site successfully. Reverify live access before enabling the schedule, then run two real checks against persisted state and confirm a hosted Telegram test. Do not bypass authentication, CAPTCHA or other access controls. No VPS was provisioned and this temporary workspace is not permanent hosting.

Telegram delivery and restart deduplication were verified locally (message 217), and the user confirmed receipt. Credentials remain private and are not included in source or state.
