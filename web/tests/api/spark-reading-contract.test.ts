import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { test } from 'node:test'

const webRoot = path.resolve(import.meta.dirname, '../..')

function source(relativePath: string): string {
  return fs.readFileSync(path.join(webRoot, relativePath), 'utf8')
}

test('Spark reading presents real intent before summary without inventing it from sources', () => {
  const layout = source('src/pages/object-detail/FactReadingLayouts.tsx')
  const projection = source('src/pages/object-detail/factReadingProjection.ts')
  const associations = source('src/pages/object-detail/FactAssociationsSection.tsx')

  for (const removed of ['intent-source', 'getSparkHumanIntentSources', 'formatSparkSummaryForReading']) {
    assert.equal(layout.includes(removed), false)
    assert.equal(projection.includes(removed), false)
  }
  assert.match(layout, /field: 'intent', zh: '意图'/)
  assert.ok(layout.indexOf("field: 'intent'") < layout.indexOf("field: 'summary'"))
  assert.match(layout, /value=\{obj\.intent\}/)
  assert.match(layout, /function SparkSummaryNode[\s\S]*value=\{value\}/)
  assert.match(associations, /\.\.\.associations\.projectMaterials/)
  assert.match(associations, /relationMaterials\.filter\(\(material\) => material\.category === 'project'\)/)
  assert.match(associations, /materials\.filter\(isSparkReadableProjectDocument\)/)
  assert.match(associations, /\(md\|mdx\|markdown\|rst\|adoc\|txt\)/)
  assert.equal(associations.includes('SparkSourceEvidenceSections'), false)
  assert.equal(associations.includes('sourceMaterials'), false)
  assert.equal(associations.includes('fieldKey="external_inputs"\n              materials={sparkProjection'), false)
  assert.equal(associations.includes('...associations.externalInputs,'), false)
})

test('Spark capture has a distinct creation reason and guided multiline summary', () => {
  const create = source('src/components/SparkCreate.tsx')
  const locales = source('src/i18n/locales.ts')

  assert.match(create, /JSON\.stringify\(\{ title, intent, description, priority \}\)/)
  assert.match(create, /spark\.intentHelp/)
  assert.match(create, /<textarea[\s\S]*rows=\{8\}[\s\S]*resize-y/)
  assert.match(create, /spark\.descriptionHelp/)
  assert.match(locales, /'spark\.descriptionHelp'/)
  assert.match(locales, /'spark\.intentHelp'/)
  assert.equal(create.includes('WorkCaseReadingLayout'), false)
})

test('Spark Markdown keeps list semantics and separates a following group', () => {
  const styles = source('src/index.css')

  assert.match(
    styles,
    /\.ldvh-study-node-content\.ldvh-spark-reading-prose \.ldvh-inline-markdown,\s*\.ldvh-study-node-content\.ldvh-spark-reading-prose \.ldvh-inline-markdown :where\(p, li\) \{\s*line-height: 26px;/,
  )
  assert.match(
    styles,
    /\.ldvh-study-node-content\.ldvh-spark-reading-prose \.ldvh-inline-markdown :where\(ul, ol\) \+ p \{\s*margin-top: 12px;/,
  )
  assert.match(
    styles,
    /\.ldvh-study-node-content\.ldvh-spark-reading-prose \.ldvh-inline-markdown :where\(ul > li\)::before \{\s*top: 10px;/,
  )
})

test('Spark open is presented as pending work, not as a generic unclosed state', () => {
  const locales = source('src/i18n/locales.ts')

  assert.match(
    locales,
    /spark:\s*\{\s*open: \{ zh: '待处理', en: 'Pending' \},\s*\},/,
  )
  assert.match(locales, /const objectEntry = OBJECT_STATUS_LOCALES\[type\]\?\.\[status\]/)
})

test('Object detail keeps its type label out of the title metadata and places status beside copy', () => {
  const detail = source('src/pages/ObjectDetail.tsx')

  assert.match(detail, /const isObjectDetail = !compact;/)
  assert.match(detail, /\{!isObjectDetail && \(/)
  assert.match(detail, /<span className="ldvh-meta-muted min-w-0 truncate">\{id\}<\/span>[\s\S]*\{isObjectDetail && showCopyAction && \(/)
  assert.match(detail, /\{showCopyAction && !isObjectDetail && \(/)
})

test('routed Spark presents one routing record instead of duplicate closure metadata', () => {
  const detail = source('src/pages/ObjectDetail.tsx')
  const panel = source('src/components/reading-panel/PanelContent.tsx')
  const layout = source('src/pages/object-detail/FactReadingLayouts.tsx')

  assert.match(detail, /closedAt=\{objType === 'spark' \|\| !obj\.closed_at \? undefined : formatDateTime/)
  assert.match(panel, /closedAt=\{objectType === 'spark' \|\| !obj\?\.closed_at \? undefined : formatDateTime/)
  assert.match(layout, /function SparkRoutingTime/)
  assert.equal(layout.includes("getFieldLabel('resolved_at', locale)"), false)
  assert.equal(layout.includes("getFieldLabel('closed_at', locale)"), false)
  assert.equal(layout.includes('statusLabel={statusLabel} objectType="spark"'), false)
})
