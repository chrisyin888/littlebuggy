#!/usr/bin/env node
/**
 * Generate the crawler-readable static versions of /swim-lessons and
 * /registration from the same data files the Vue app uses, so the two
 * can never drift. Run: node scripts/generate_course_static.mjs
 */
import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const swim = await import(join(root, 'src/data/swimLessons.js'))
const reg = await import(join(root, 'src/data/registration.js'))

const esc = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

const SWIM_STATUS = {
  dated: 'Date set',
  open: 'Open now',
  rolling: 'Rolling',
  tba: 'Not posted yet',
  none: 'No winter lessons',
}
const REG_STATUS = {
  open: 'Open now',
  dated: 'Date set',
  rolling: 'Rolling',
  tba: 'Not posted yet',
  none: 'Not offered',
  club: 'Club-run',
}

const STYLE = `
  body { font-family: system-ui, -apple-system, sans-serif; margin: 0; color: #1f2430; background: #faf9fc; }
  main { max-width: 980px; margin: 0 auto; padding: 24px 16px 48px; }
  h1 { font-size: 1.6rem; line-height: 1.25; }
  h2 { font-size: 1.2rem; margin-top: 2.2rem; }
  .updated { color: #555; font-size: 0.92rem; }
  table { width: 100%; border-collapse: collapse; background: #fff; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #e7e4ee; font-size: 0.92rem; vertical-align: top; line-height: 1.45; }
  th { background: #eef4ff; }
  td.when, td.city { font-weight: 700; }
  td.city { white-space: nowrap; }
  .wrap { overflow-x: auto; }
  .note { background: #eef4ff; border: 1px solid #c7d7f5; border-radius: 8px; padding: 10px 14px; }
  .sub { display: block; color: #555; font-size: 0.85rem; margin-top: 3px; }
  ul.tips { margin: 0; padding-left: 1.05rem; }
  ul.tips li { margin-bottom: 0.25rem; }
  a { color: #6d28d9; }
  li, p { line-height: 1.55; }
`

// ————————————————— Swim lessons —————————————————
const { SWIM_CITIES, SWIM_UPCOMING, SWIM_TABLE, SWIM_CHECKED_DATE } = swim

const upcomingRows = SWIM_UPCOMING.map(
  (i) =>
    `      <tr><td class="when">${esc(i.when)}</td><td>${esc(i.label)}</td><td><a href="${esc(i.url)}">Register</a></td></tr>`,
).join('\n')

const cityRows = SWIM_CITIES.map((c) => {
  const t = SWIM_TABLE[c.id]
  const dates = t.dates.map((d) => esc(d)).join('<br>')
  const note = t.note ? `<span class="sub">${esc(t.note)}</span>` : ''
  const pools = (c.pools.length ? esc(c.pools.join(' · ')) : '—') +
    (c.poolsNote ? `<span class="sub">${esc(c.poolsNote)}</span>` : '')
  const tips = `<ul class="tips">${t.tips.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`
  return `      <tr><td class="city">${esc(c.name)}</td><td>${dates}${note}</td><td>${pools}</td><td>${SWIM_STATUS[c.status]}</td><td>${tips}</td><td><a href="${esc(c.registerUrl)}">Register</a></td></tr>`
}).join('\n')

const sourceItems = SWIM_CITIES.map(
  (c) => `    <li>${esc(c.name)} — <a href="${esc(c.sourceUrl)}">${esc(c.sourceName)}</a></li>`,
).join('\n')

const swimHtml = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Swim Lessons Registration in Metro Vancouver — Dates, Pools &amp; Sign-Up Links — LittleBuggy</title>
<meta name="description" content="When does swim lessons registration open in Vancouver, Burnaby, Surrey, Richmond, Delta, Coquitlam and the rest of Metro Vancouver? Verified city dates, pools, and official registration links — plus the account and waitlist steps to do before the day.">
<style>${STYLE}</style>
</head>
<body>
<main>
  <p><a href="https://littlebuggy.ca/">← LittleBuggy home</a></p>
  <h1>Swim Lessons Registration in Metro Vancouver</h1>
  <p class="updated">City-run swim lesson sign-up dates, pools and official registration links for 15 Metro Vancouver cities — one table, one row per city. Checked against city websites ${esc(SWIM_CHECKED_DATE)}. Interactive version: <a href="https://littlebuggy.ca/swim-lessons">littlebuggy.ca/swim-lessons</a></p>

  <div class="note">
    <h2 style="margin-top:0">Next registrations — in date order</h2>
    <div class="wrap">
    <table>
      <tr><th>When</th><th>What opens</th><th></th></tr>
${upcomingRows}
    </table>
    </div>
    <p>Port Coquitlam registration is already open, and Burnaby swim lessons use rolling registration (30 days before each class starts for residents).</p>
  </div>

  <h2>All 15 cities — one table</h2>
  <div class="wrap">
  <table>
    <tr><th>City</th><th>Next registration</th><th>Pools</th><th>Status</th><th>Good to know</th><th></th></tr>
${cityRows}
  </table>
  </div>

  <h2>Before registration day</h2>
  <ul>
    <li><strong>Create the account days early.</strong> Some cities take days to approve new accounts or verify resident status.</li>
    <li><strong>Add every child to the account, with birthdays</strong> — age and level checks happen at checkout.</li>
    <li><strong>Know your child's level</strong> — most cities require the previous level on file; other cities' report cards can usually be submitted ahead of time.</li>
    <li><strong>Use wish lists / favourites</strong> where the system offers them.</li>
    <li><strong>Residents usually register first</strong> — check your city's gap in the table.</li>
    <li><strong>Join the waitlist immediately if your class is full</strong> — emailed offers can expire in 24–36 hours.</li>
  </ul>

  <h2>About this page &amp; sources</h2>
  <p>LittleBuggy shares information for families; we do not run lessons and cannot register your child or guarantee a spot. Dates come from the official city pages listed below, checked ${esc(SWIM_CHECKED_DATE)} — confirm on the official site before registration day. For skating lessons, holiday camps, gymnastics, preschool and lifeguard courses, see the <a href="https://littlebuggy.ca/registration">recreation registration calendar</a>.</p>
  <ul>
${sourceItems}
  </ul>
</main>
</body>
</html>
`
writeFileSync(join(root, 'public/swim-lessons/index.html'), swimHtml)

// ————————————————— Registration calendar —————————————————
const { REG_CALENDAR, REG_OPEN_NOW, REG_SECTIONS, REG_SYSTEMS, REG_TABLE, REG_CHECKED_DATE } = reg

const calRows = REG_CALENDAR.map((r) => {
  const s = REG_SYSTEMS[r.sys]
  return `      <tr><td class="when">${esc(r.when)}</td><td>${esc(r.what)}</td><td><a href="${esc(s.url)}">${esc(s.label)}</a></td></tr>`
}).join('\n')

const openItems = REG_OPEN_NOW.map((i) => `    <li>${esc(i)}</li>`).join('\n')

const sectionHtml = REG_SECTIONS.map((sec) => {
  const rows = sec.entries
    .map((e) => {
      const t = REG_TABLE[`${sec.id}|${e.city}`] || { when: e.text, status: 'dated', note: '' }
      const s = REG_SYSTEMS[e.sys]
      return `      <tr><td class="city">${esc(e.city)}</td><td>${esc(t.when)}</td><td>${REG_STATUS[t.status]}</td><td>${esc(e.venue)}</td><td>${esc(t.note)}</td><td><a href="${esc(s.url)}">Register</a></td></tr>`
    })
    .join('\n')
  return `
  <h2>${esc(sec.title)}</h2>
  <p>${esc(sec.blurb)}</p>
  <div class="wrap">
  <table>
    <tr><th>City</th><th>Registration</th><th>Status</th><th>Where</th><th>Good to know</th><th></th></tr>
${rows}
  </table>
  </div>`
}).join('\n')

const regHtml = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recreation Registration Calendar — Skating, Camps, Gymnastics &amp; Swim Lessons in Metro Vancouver — LittleBuggy</title>
<meta name="description" content="Every Metro Vancouver city recreation registration date in one calendar: skating lessons, winter break &amp; summer camps, gymnastics, preschool and Bronze lifeguard courses — verified against official city websites, with direct registration links.">
<style>${STYLE}</style>
</head>
<body>
<main>
  <p><a href="https://littlebuggy.ca/">← LittleBuggy home</a></p>
  <h1>Recreation Registration Calendar: Metro Vancouver</h1>
  <p class="updated">Skating lessons, holiday camps, gymnastics, preschool and lifeguard courses — every city's next registration date in one place, one row per city. Checked against city websites ${esc(REG_CHECKED_DATE)}. Interactive version: <a href="https://littlebuggy.ca/registration">littlebuggy.ca/registration</a>. Swim lessons have a dedicated page: <a href="https://littlebuggy.ca/swim-lessons">littlebuggy.ca/swim-lessons</a></p>

  <div class="note">
    <h2 style="margin-top:0">The calendar — every confirmed date, in order</h2>
    <div class="wrap">
    <table>
      <tr><th>When</th><th>What opens</th><th>Register</th></tr>
${calRows}
    </table>
    </div>
    <h3>Already open now</h3>
    <ul>
${openItems}
    </ul>
  </div>

  <h2>Swim lessons</h2>
  <p>Swim lessons are the most competitive registration of all, so they get a dedicated page with every city's date, pools and rules in one table: <a href="https://littlebuggy.ca/swim-lessons">littlebuggy.ca/swim-lessons</a></p>
${sectionHtml}

  <h2>About this page</h2>
  <p>LittleBuggy is an information page for families — we do not run programs and cannot register your child or guarantee a spot. Dates and rules come from the official city websites, checked ${esc(REG_CHECKED_DATE)}; cities do change dates (Richmond's winter registration night was postponed this season), so confirm in the official system before your registration day. The universal rules still apply: create the account and add your children days early, know the level or category you need, and join the waitlist the moment a class shows full.</p>
</main>
</body>
</html>
`
writeFileSync(join(root, 'public/registration/index.html'), regHtml)

console.log('static pages written')
