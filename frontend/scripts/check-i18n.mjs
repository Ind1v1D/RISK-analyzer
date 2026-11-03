// Fails (exit 1) if any language is missing a key, has an extra key, uses
// different {placeholders} than English, or lacks a plural form its language needs.
//   npm run check:i18n
import { translations } from '../src/i18n/translations.js'

const en = translations.en
const placeholders = (v) =>
  [...new Set(JSON.stringify(v).match(/\{\w+\}/g) ?? [])].sort().join(',')

let problems = 0
const fail = (msg) => {
  problems += 1
  console.error('✗', msg)
}

for (const [lang, dict] of Object.entries(translations)) {
  const needed = new Intl.PluralRules(lang).resolvedOptions().pluralCategories.filter((c) => c !== 'other')
  for (const key of Object.keys(en)) {
    if (!(key in dict)) {
      fail(`[${lang}] missing key: ${key}`)
      continue
    }
    if (placeholders(dict[key]) !== placeholders(en[key])) {
      fail(`[${lang}] placeholders differ from English in: ${key}`)
    }
    if (typeof dict[key] === 'object') {
      for (const cat of [...needed, 'other']) {
        if (!(cat in dict[key])) fail(`[${lang}] ${key} lacks plural form "${cat}"`)
      }
    }
  }
  for (const key of Object.keys(dict)) if (!(key in en)) fail(`[${lang}] unknown extra key: ${key}`)
}

if (problems) process.exit(1)
console.log(`✓ i18n OK — ${Object.keys(translations).join(', ')} × ${Object.keys(en).length} keys`)
