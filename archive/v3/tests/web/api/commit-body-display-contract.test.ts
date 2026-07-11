import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..')
const projectFilesSource = fs.readFileSync(path.join(repoRoot, 'web/src/pages/ProjectFiles.tsx'), 'utf-8')

assert.match(
  projectFilesSource,
  /<MarkdownPreview\s+content=\{selectedCommit\.body\.trim\(\)\}/,
  'ProjectFiles expanded commit body should render through MarkdownPreview so enforced "- " body lists show bullets',
)
assert.match(
  projectFilesSource,
  /className="ldvh-inline-markdown ldvh-commit-body-markdown max-w-none"/,
  'ProjectFiles commit body should use the commit body markdown class that renders list markers as LDVH dots',
)
assert.doesNotMatch(
  projectFilesSource,
  /<pre[^>]*>\s*\{selectedCommit\.body\.trim\(\)\}\s*<\/pre>/,
  'ProjectFiles must not render commit body through preformatted raw text',
)
