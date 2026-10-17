# Deployment status: three-hour retries enabled; hosted availability not yet verified

Repository: sombek/riyadh-tennis-courts.
Workflow: .github/workflows/tennis-monitor.yml.
Run evidence: https://github.com/sombek/riyadh-tennis-courts/actions/runs/39047232614

The source and hourly workflow are on the default branch. Existing website files were not edited. Code pushes, workflow dispatch and workflow status inspection now work.

The hosted run beginning October 17, 2026 at 18:56:49 Asia/Riyadh installed Python and Chromium, passed all 20 automated tests, and loaded the persistent state branch. However, every real browser navigation attempt returned HTTP 429 (Too Many Requests). Calendar parsing failed. This establishes the observed HTTP failure, not its exact server-side cause or a permanent block on every GitHub runner.

The failure was committed to monitor-state at 18:57:00 Riyadh. The baseline remained October 18; all seven previous successful observations and the sent installation-test record were preserved. No new booking date or release notification was recorded. This verifies hosted failure-state persistence, not successful hosted availability inspection.

The workflow was initially disabled after the hosted HTTP 429 failure. The user subsequently requested retries every three hours. It is now enabled with cron `0 */3 * * *`, corresponding to 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00 and 21:00 Asia/Riyadh. No immediate manual booking check was dispatched with this schedule change. GitHub may delay scheduled execution. Successful hosted availability inspection is still unverified, so the full monitor cannot be described as verified operational.

The owner has now added TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to repository Actions secrets. A separate manually dispatched workflow verified delivery directly from GitHub without accessing the booking site: Telegram message 218 was acknowledged at October 17, 2026, 19:00:13 Asia/Riyadh. Run: https://github.com/sombek/riyadh-tennis-courts/actions/runs/39047482326 . The credential blocker is resolved for workflow execution; website HTTP 429 remains unresolved.

Next verification is to inspect the authorized scheduled retries. If HTTP 429 persists, investigate the rate limit or choose a legitimate always-on host that can access the site. Two successful hosted booking checks against persisted state remain required. Hosted Telegram delivery is already verified. Do not bypass authentication, CAPTCHA or other access controls. No VPS was provisioned and this temporary workspace is not permanent hosting.

Telegram delivery and restart deduplication were verified locally (message 217), and the user confirmed receipt. Credentials remain private and are not included in source or state.

A second isolated hosted verification run also succeeded (https://github.com/sombek/riyadh-tennis-courts/actions/runs/39047522532). It reused sent event test:github-installation with message ID 218 and the original sent timestamp, issuing no duplicate Telegram request. The seven successful availability observations and October 18 baseline remain unchanged. The isolated test did not access the booking site or reset its failure streak.
