#!/usr/bin/env node
// Lists free slots at Tennis Home Academy (all locations, all visible services)
// via the same public Amelia endpoints the booking widget uses.
// Usage: node check-slots.mjs [--sport tennis|pickleball|squash] [--date YYYY-MM-DD] [--json]

import { fileURLToPath } from 'node:url';

const API = 'https://tennishomeacademy.com/wp-admin/admin-ajax.php?action=wpamelia_api&call=';

async function get(call, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${API}${call}${qs ? `&${qs}` : ''}`, { headers: { 'User-Agent': 'Mozilla/5.0' } });
  if (!res.ok) throw new Error(`${call} -> HTTP ${res.status}`);
  return (await res.json()).data;
}

export async function getSlots({ sport = null, date: dateFilter = null } = {}) {
sport = sport?.toLowerCase() || null;
const entities = await get('/entities&types[]=locations&types[]=categories&types[]=employees');
const locations = new Map(entities.locations.map((l) => [l.id, l.name.replace(/\s+/g, ' ').trim()]));
const employees = entities.employees.filter((e) => e.status === 'visible');
const courtName = new Map(employees.map((e) => [e.id, `${e.firstName} ${e.lastName}`.trim()]));
const services = entities.categories
  .filter((c) => !sport || c.name.toLowerCase().includes(sport))
  .flatMap((c) => c.serviceList)
  .filter((s) => s.status === 'visible');

const results = [];

await Promise.all(services.map(async (service) => {
  const providerIds = employees
    .filter((e) => e.serviceList.some((s) => s.id === service.id))
    .map((e) => e.id);
  if (!providerIds.length) return;

  const data = await get('/slots', {
    serviceId: service.id,
    providerIds: providerIds.join(','),
    group: 1,
    page: 'booking',
    persons: 1,
  });

  for (const [date, times] of Object.entries(data.slots || {})) {
    if (dateFilter && date !== dateFilter) continue;
    for (const [time, entries] of Object.entries(times)) {
      for (const [providerId, locationId] of entries) {
        results.push({
          location: locations.get(locationId) ?? `Location ${locationId}`,
          service: service.name.replace(/\s+/g, ' ').trim(),
          price: service.price,
          date,
          time,
          court: courtName.get(providerId) ?? `Court ${providerId}`,
        });
      }
    }
  }
}));

// Some services share a name and court (e.g. two "JW Squash Court" entries).
const seen = new Set();
const unique = results.filter((r) => {
  const key = [r.location, r.service, r.date, r.time, r.court].join('|');
  return !seen.has(key) && seen.add(key);
});
results.length = 0;
results.push(...unique);

results.sort((a, b) =>
  a.location.localeCompare(b.location) ||
  a.service.localeCompare(b.service) ||
  a.date.localeCompare(b.date) ||
  a.time.localeCompare(b.time));

return results;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
const args = process.argv.slice(2);
const opt = (name) => (args.includes(name) ? args[args.indexOf(name) + 1] : null);
const asJson = args.includes('--json');
const results = await getSlots({ sport: opt('--sport'), date: opt('--date') });

if (asJson) {
  console.log(JSON.stringify(results, null, 2));
} else if (!results.length) {
  console.log('No free slots found.');
} else {
  let loc, svc, day;
  for (const r of results) {
    if (r.location !== loc) { loc = r.location; svc = day = null; console.log(`\n=== ${loc} ===`); }
    if (r.service !== svc) { svc = r.service; day = null; console.log(`\n  ${svc} (${r.price} SAR/hr)`); }
    if (r.date !== day) {
      day = r.date;
      const weekday = new Date(`${day}T12:00:00`).toLocaleDateString('en-GB', { weekday: 'short' });
      console.log(`    ${weekday} ${day}`);
    }
    console.log(`      ${r.time}  ${r.court}`);
  }
}
}
