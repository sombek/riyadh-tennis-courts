# Deployment status

Repository: sombek/riyadh-tennis-courts.

The integration places source under tools/netacademy-monitor/ and the hourly workflow at .github/workflows/tennis-monitor.yml. Existing website files are unchanged.

Code pushes now work. The monitor-state branch has been initialized with the verified baseline and sent installation-test record (Telegram message 217), so deployment does not erase history or resend the test. No bot credentials are committed.

All 20 monitor tests pass. Existing verify-data.py passes for all 15 venues, node --check app.js passes, and the adapted workflow passes actionlint v1.7.7.

Remaining verification:
- GitHub still denies this connection access to the Actions secret public key (HTTP 403 Resource not accessible by integration). The repository owner must add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID through repository Settings > Secrets and variables > Actions.
- Run the deployed workflow twice, inspect real availability logs and persisted state, then verify notification delivery from the hosted runner. The hourly schedule is minute zero in Asia/Riyadh, subject to GitHub scheduling delays.
- Do not call the deployment operational until those checks pass.

Telegram delivery and restart deduplication have been verified locally, and the user confirmed receipt. The public repository contains only public booking availability and acknowledgment metadata. Tokens and environment files must remain private.
