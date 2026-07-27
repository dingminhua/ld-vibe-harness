import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { test } from 'node:test'

function source(relativePath: string): string {
  return readFileSync(path.resolve(relativePath), 'utf8')
}

test('Dashboard reports a Git log failure without suppressing field-level facts', () => {
  const dashboard = source('api/routes/dashboard.ts')
  const page = source('src/pages/Dashboard.tsx')

  assert.match(dashboard, /git_log_unavailable/)
  assert.match(dashboard, /recentChangesIssue/)
  assert.doesNotMatch(dashboard, /getGitLog\(10, locale\)\.catch\(\(\) => \[\]\)/)
  assert.match(page, /data\.recentChangesIssue/)
})

test('Git status and historical file diffs do not turn command failures into successful emptiness', () => {
  const routes = source('api/routes/project-files.ts')

  assert.doesNotMatch(routes, /git', \['show',[\s\S]*?\.catch\(\(\) => ''\)/)
  assert.doesNotMatch(routes, /catch \{\s*\/\/ 非 Git 管辖项目不阻塞其它项目。[\s\S]*?\}/)
})
