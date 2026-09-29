# Data review — 29 September 2026

Reviewed all 15 original records. This is a structural and editorial audit of the supplied directory, not a fresh verification of venue availability, prices, phone ownership, or linked websites.

## What was normalized

- Preserved all 15 names, original location text, map URLs, contact values, booking/site/app URLs, base amounts and existing price tiers.
- Extracted duration options from notes into consistent numeric price records. Durations are minutes; currency is SAR with a separate assumption flag for Al Yamamah.
- Assigned stable venue IDs; used consistent nested fields and `null` for missing values.
- Separated shared map links, map searches and coordinates. None claim a verified court entrance.
- Separated booking pages from general websites and app-store downloads. An email awaiting a reply is now a pending booking status, with the original note retained.
- Preserved the questionable Al Yamamah number verbatim, flagged its Saudi number format, and removed its active WhatsApp action without guessing a replacement.
- Retained the non-Saudi Salwa contact unchanged. Its format is plausible; ownership and WhatsApp availability remain unverified.
- Retained a complete original snapshot in `source-records.json`. `courts.json` is the canonical cleaned dataset; the offline browser bundle is generated from it.

## Record-by-record audit

| Venue | Recorded price(s), SAR | Outstanding detail / treatment |
|---|---|---|
| القيروان | 110; 155 / 90 min; 210 / 120 min | Base duration absent from the explicit record; display 110 with a duration warning. Shared map link retained. |
| العارض | 110; 155 / 90 min; 210 / 120 min | Same duration ambiguity; distinct venue and map retained despite shared contact and prices. |
| شوايات | 110 / 60 min; 140 / 90 min; 190 / 120 min | Area missing. Both app stores available in the main actions. Removed contradictory hourly labeling from longer-duration tiers. |
| جامعة اليمامة | 150; 200 / 90 min; 250 / 120 min | Base duration unspecified; currency assumed in source. Raw +9665599888307 has an unexpected Saudi format and is inactive. Entrance unconfirmed. |
| جامعة الأمير سلطان | Not recorded | Booking link retained. Campus search is not a confirmed court entrance. |
| المدينة الرقمية | 180 / 60 min; 360 / 120 min | Parsed the second duration from notes. Hotel map search and entrance uncertainty retained. |
| نت تنس | 200 / 60 min | General website, not claimed to be a direct booking page. Map is a search. |
| راكت | 199 / 60 min | Duration explicitly stated in original note. Sinjab app link is absent; no link invented. |
| بيت التنس | 286 / 120 min | Show the full two-hour price and a clearly derived 143/hour equivalent. Excluded from one-hour offer sorting. Branch/three-court versus three-branch ambiguity retained. |
| كمباوند سلوى | 110 | Base duration and area unspecified. Candidate location and access conditions require confirmation. International contact preserved. |
| كمباوند نجد | 150 / 60 min peak; 99 / 60 min off-peak | Preserve recorded time windows. 22:00–23:00 has no recorded rate. Access for non-residents needs confirmation. “From 99” explicitly varies by time. |
| وادي حنيفة — Spin | 200 | Base duration unspecified. Booking URL, WhatsApp and shared map link retained. |
| الإنتركونتيننتال | 230 / 60 min | Same-day phone booking opens at 10:00 according to notes. Phone action retained. Area missing. |
| فال كمباوند | Not recorded | Pending email response in source; site link is not a confirmed booking flow. Coordinates identify the facility, not the entrance. |
| ملعب جامعة الملك سعود | 150 / 60 min | Booking form, evening hours, confirmation requirement and cancellation notice retained. Cancellation WhatsApp and area missing. |

The old interface implicitly called prices hourly when `priceHours` was absent. This review deliberately does not turn that fallback into an independently supported duration. Five base prices remain unspecified until confirmed. Existing explicit durations and durations written in notes are retained.

## Verification completed

- Data preservation checks pass for all 15 records, including every original contact and URL.
- 13 venues have at least one recorded price; 6 have shared map links; 6 have structurally usable contact channels.
- Browser checks: Arabic search (including hamza variants), price and location filters, contact filtering, ascending hourly sorting, empty results/reset, saving/removing favorites and persistence after reload.
- Expanded Al Yamamah details show the original questionable number and currency caveat without a contact link.
- Responsive checks at 320 px, 390 px and 768 px: no horizontal page overflow. Desktop and phone layouts visually inspected.
- Browser error/warning log was empty during checks; JavaScript syntax validation passed.

## Limits

Source websites and current prices were not revalidated. Structural phone validation is not proof of ownership. Shared location links are not independently verified locations. No messages, calls, bookings, or publication were performed.
