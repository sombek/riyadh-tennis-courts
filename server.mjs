#!/usr/bin/env node
// Serves the site plus /api/slots (the academy's API has no CORS, so the page can't call it directly).
// Usage: node server.mjs  ->  http://localhost:8080
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { getSlots } from './check-slots.mjs';

const ROOT = fileURLToPath(new URL('.', import.meta.url));
const PORT = Number(process.env.PORT) || 8080;
const SPORTS = new Set(['tennis', 'pickleball', 'squash']);
const CACHE_MS = 5 * 60 * 1000;
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
};
const cache = new Map();

function send(res, status, body, type) {
  res.writeHead(status, { 'Content-Type': type, 'X-Content-Type-Options': 'nosniff' });
  res.end(body);
}

async function slots(res, params) {
  const sport = params.get('sport') || 'tennis';
  if (!SPORTS.has(sport)) return send(res, 400, JSON.stringify({ error: 'Unknown sport' }), TYPES['.json']);
  const hit = cache.get(sport);
  if (!hit || Date.now() - hit.at > CACHE_MS) {
    cache.set(sport, { at: Date.now(), data: getSlots({ sport }) });
  }
  try {
    const { at, data } = cache.get(sport);
    send(res, 200, JSON.stringify({ fetchedAt: new Date(at).toISOString(), slots: await data }), TYPES['.json']);
  } catch (err) {
    cache.delete(sport);
    console.error(err);
    send(res, 502, JSON.stringify({ error: 'Could not reach Tennis Home Academy' }), TYPES['.json']);
  }
}

createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/api/slots') return slots(res, url.searchParams);

  let path;
  try {
    path = normalize(join(ROOT, decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname)));
  } catch {
    return send(res, 400, 'Bad request', 'text/plain');
  }
  if (!path.startsWith(ROOT) || path.split(sep).some((p) => p.startsWith('.'))) return send(res, 403, 'Forbidden', 'text/plain');
  try {
    send(res, 200, await readFile(path), TYPES[extname(path)] || 'application/octet-stream');
  } catch {
    send(res, 404, 'Not found', 'text/plain');
  }
}).listen(PORT, '127.0.0.1', () => console.log(`http://localhost:${PORT}`));
