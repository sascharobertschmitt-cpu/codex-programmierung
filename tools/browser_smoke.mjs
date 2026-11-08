// Headless-Browsertest einer Babylon.js-Testseite.
// Erwartet, dass die Seite window.TEST_RESULT = {ok, checks, stats} setzt.
// Aufruf: node tools/browser_smoke.mjs <url> <screenshot.png> [timeoutMs]
// Rendering laeuft per Software (SwiftShader), FPS-Werte sind daher nicht aussagekraeftig.
import { chromium } from 'playwright';

const [url, shot, timeoutArg] = process.argv.slice(2);
const timeout = Number(timeoutArg || 90000);
if (!url || !shot) {
  console.error('Aufruf: node tools/browser_smoke.mjs <url> <screenshot.png> [timeoutMs]');
  process.exit(2);
}

const launch = {
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
};
if (process.env.PW_CHANNEL) launch.channel = process.env.PW_CHANNEL;
if (process.env.PW_EXECUTABLE) launch.executablePath = process.env.PW_EXECUTABLE;

const browser = await chromium.launch(launch);
const page = await browser.newPage({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
page.on('console', (m) => console.log(`[console.${m.type()}] ${m.text()}`));
page.on('pageerror', (e) => console.log(`[pageerror] ${e.message}`));
page.on('requestfailed', (r) => console.log(`[requestfailed] ${r.url()} ${r.failure()?.errorText}`));

let result = null;
try {
  await page.goto(url, { waitUntil: 'load', timeout });
  await page.waitForFunction(() => window.TEST_RESULT !== undefined, null, { timeout });
  result = await page.evaluate(() => window.TEST_RESULT);
  await page.waitForTimeout(1500);
} catch (e) {
  console.log('Timeout/Fehler: ' + e.message);
}
await page.screenshot({ path: shot, fullPage: true });
await browser.close();

if (!result) {
  console.log('Kein TEST_RESULT erhalten.');
  process.exit(1);
}
for (const c of result.checks) {
  const s = c.ok === true ? 'PASS' : c.ok === 'warn' ? 'WARN' : 'FAIL';
  console.log(`[${s}] ${c.name}  ${c.detail || ''}`);
}
console.log(JSON.stringify(result.stats, null, 2));
process.exit(result.ok ? 0 : 1);
