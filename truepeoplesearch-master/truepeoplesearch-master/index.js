// index.js — stealth + human pacing, no page.waitForTimeout (uses sleep())
// Requires: puppeteer-extra, puppeteer-extra-plugin-stealth, random-useragent
// CSV headers must be EXACT: 1st Owner's First Name, 1st Owner's Last Name, Site Zip Code

const fs = require('fs');
const parse = require('csv-parse/lib/sync');

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const randomUA = require('random-useragent');
puppeteer.use(StealthPlugin());

const NOTFOUND_SELECTOR = 'body > div:nth-child(2) > div > div.content-center > div.row.pl-1.record-count > div';
const EMAIL_DESC_STRING = 'Email Addresses';

// === knobs you can tweak ===
const MAX_ROWS = 5;             // test safely; set to null for all rows
const MIN_COOLDOWN_MS = 12000;  // per-row delay min
const MAX_COOLDOWN_MS = 30000;  // per-row delay max
// ============================

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const jitter = (a, b) => a + Math.floor(Math.random() * (b - a + 1));

async function wiggle(page) {
  const x = 300 + Math.random() * 200;
  const y = 300 + Math.random() * 200;
  await page.mouse.move(x, y, { steps: 15 + Math.floor(Math.random() * 10) });
}

async function getTruePeople(page, firstName, lastName, zip) {
  const name = (firstName + ' ' + lastName).trim();
  const targetUrl = `https://www.truepeoplesearch.com/results?name=${encodeURI(name)}&citystatezip=${zip}&rid=0x0`;

  await wiggle(page);
  await sleep(jitter(1000, 2200));   // was page.waitForTimeout

  await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });

  // Block detection
  const blocked = await page.evaluate(() => {
    return /Access blocked|unusual activity/i.test(document.body.innerText || '');
  });
  if (blocked) return { blocked: true, emails: '' };

  // Not-found text detector (same behavior as the original)
  const notFound = await page.evaluate((sel) => {
    const NOTFOUND_TEXT = 'We could not find any records for that search criteria.';
    try {
      const el = document.querySelector(sel);
      if (!el) return false;
      return (el.textContent || '').trim() === NOTFOUND_TEXT;
    } catch { return false; }
  }, NOTFOUND_SELECTOR);
  if (notFound) return { blocked: false, emails: '' };

  // Scrape email block
  const emails = await page.evaluate((DESC_STRING) => {
    const elems = document.querySelectorAll('*');
    const emailDomElement = Array.from(elems).find(v => (v.textContent || '').trim() === DESC_STRING);
    if (!emailDomElement) return '';
    const p = emailDomElement.parentNode;
    const out = [];
    for (let i = 1; i < p.childElementCount; i++) {
      out.push((p.children[i].textContent || '').trim());
    }
    return out.join('\t');
  }, EMAIL_DESC_STRING);

  return { blocked: false, emails };
}

(async () => {
  // read CSV (must be in this folder)
  const input = fs.readFileSync('./data.csv', 'utf8');
  let records = parse(input, { columns: true, skip_empty_lines: true });

  if (MAX_ROWS && records.length > MAX_ROWS) records = records.slice(0, MAX_ROWS);

  // Launch with stealth-y args
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled'
    ]
  });
  const [page] = await browser.pages();

  // Random, modern-ish Chrome UA + headers
  const ua = randomUA.getRandom(ua => ua.browserName === 'Chrome' && parseFloat(ua.browserVersion) >= 115)
            || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36';
  await page.setUserAgent(ua);
  await page.setExtraHTTPHeaders({ 'Accept-Language': 'en-US,en;q=0.9' });

  // Kill obvious automation fingerprints
  await page.evaluateOnNewDocument(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
    Object.defineProperty(navigator, 'plugins',   { get: () => [1,2,3,4,5] });
  });

  for (const record of records) {
    const firstName = record["1st Owner's First Name"];
    const lastName  = record["1st Owner's Last Name"];
    const zip       = record["Site Zip Code"];

    if (!firstName || !lastName || !zip) {
      console.log('Skipping row with missing fields');
      continue;
    }

    const { blocked, emails } = await getTruePeople(page, firstName, lastName, zip);

    if (blocked) {
      console.log('Blocked — change IP (phone hotspot) or wait ~10 min, then rerun.');
      break; // bail early so you can change IP
    }

    if (emails) {
      console.log(`${firstName}\t${lastName}\t${emails}`);
    } else {
      console.log(`${firstName}\t${lastName}\t(no emails found)`);
    }

    // cooldown per row (randomized) — was page.waitForTimeout
    await sleep(jitter(MIN_COOLDOWN_MS, MAX_COOLDOWN_MS));
  }

  await browser.close();
})();
