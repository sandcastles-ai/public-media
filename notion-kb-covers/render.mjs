import { chromium } from 'playwright'
import fs from 'fs'
import path from 'path'

const dir = path.join(path.dirname(new URL(import.meta.url).pathname), 'out')
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json')))
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 2000, height: 500 }, deviceScaleFactor: 2 })
let problems = 0
for (const item of manifest) {
  await page.goto('file://' + path.join(dir, item.slug + '.html'))
  await page.waitForFunction(() => document.body.dataset.ready === '1')
  await page.waitForTimeout(100)
  const issues = await page.evaluate(() => {
    const out = []
    const box = [...document.querySelectorAll('.core > * > *, .core > *')].reduce(
      (b, el) => {
        const r = el.getBoundingClientRect()
        return { l: Math.min(b.l, r.left), r: Math.max(b.r, r.right) }
      },
      { l: 1e9, r: -1e9 },
    )
    if (box.r - box.l > 660) out.push('core width ' + Math.round(box.r - box.l))
    if (box.l < 670 || box.r > 1330) out.push('core outside gallery-safe x ' + Math.round(box.l) + '-' + Math.round(box.r))
    for (const side of document.querySelectorAll('.side')) {
      const sr = side.getBoundingClientRect()
      if (sr.height > 250) out.push(side.className + ' height ' + Math.round(sr.height))
      if (sr.top < 90 || sr.bottom > 360) out.push(side.className + ' outside band ' + Math.round(sr.top) + '-' + Math.round(sr.bottom))
      for (const el of side.querySelectorAll('*')) {
        const r = el.getBoundingClientRect()
        if (r.right > sr.right - 10 || el.scrollWidth > el.clientWidth + 1) out.push(side.className + ' overflow: ' + (el.textContent || '').slice(0, 40))
      }
      for (const li of side.querySelectorAll('li')) {
        if (li.getBoundingClientRect().height > 36) out.push(side.className + ' wraps: ' + li.textContent.slice(0, 40))
      }
    }
    const chip = document.querySelector('.chip')
    if (chip && parseFloat(chip.style.fontSize) < 34) out.push('chip font ' + chip.style.fontSize)
    return [...new Set(out)]
  })
  if (issues.length) {
    problems++
    console.log('ISSUES', item.slug, JSON.stringify(issues))
  }
  await page.screenshot({ path: path.join(dir, item.slug + '.png') })
  console.log('rendered', item.slug)
}
await browser.close()
console.log(problems ? `${problems} cover(s) with layout issues` : 'all covers passed the layout audit')
