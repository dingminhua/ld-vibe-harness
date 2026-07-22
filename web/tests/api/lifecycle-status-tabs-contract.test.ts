import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { test } from 'node:test'

const webRoot = path.resolve(import.meta.dirname, '../..')

function source(relativePath: string): string {
  return fs.readFileSync(path.join(webRoot, relativePath), 'utf8')
}

test('V4 fact lists keep lifecycle status tabs even when a terminal state has zero objects', () => {
  const filter = source('src/components/ObjectStatusFilter.tsx')

  assert.match(filter, /adr: \['active', 'superseded', 'retired'\]/)
  assert.match(filter, /pitfall: \['active', 'superseded', 'retired'\]/)
  assert.match(filter, /study: \['active', 'superseded', 'retired'\]/)
  assert.match(filter, /if \(!\(type in FALLBACK_STATUSES_BY_TYPE\)\) return sortedOptions;/)
  assert.match(filter, /if \(displayOptions\.length <= 1 && !\(type in FALLBACK_STATUSES_BY_TYPE\)\) return null;/)
})

test('retired has an explicit lifecycle status label', () => {
  const locales = source('src/i18n/locales.ts')

  assert.match(locales, /retired: \{ zh: '已退出', en: 'Retired' \}/)
})
