/**
 * item-03 一致性回归测试：五类事实对象本地直读路径。
 *
 * 覆盖：
 * - spark/workcase/study 列表与详情直读
 * - study 的 frontmatter + 正文解析（report_body）
 * - adr/pitfall 目录缺失的如实呈现（item-02）
 * - create-spark 写入（Python 桥）→ 列表/详情直读回读的端到端一致性
 */

import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { test } from 'node:test'

import { listObjects, showObject } from '../../api/services/facts.ts'
import { listLocalFacts, readLocalFact, FACT_TYPE_DIRS, type LocalFactScope } from '../../api/services/localFactReader.ts'
import { invokeV4FactsMachine } from '../../api/internal/v4FactsTransport.ts'

function makeWorkspace(): { workspaceRoot: string; projectRoot: string; scope: LocalFactScope; cleanup: () => void } {
  const workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-local-facts-'))
  const projectRoot = path.join(workspaceRoot, 'project')
  fs.mkdirSync(path.join(projectRoot, 'ldvh-base', 'sparks'), { recursive: true })
  fs.mkdirSync(path.join(projectRoot, 'ldvh-base', 'workcases'), { recursive: true })
  fs.mkdirSync(path.join(projectRoot, 'ldvh-base', 'studies'), { recursive: true })
  // adr/pitfall 目录刻意缺失，模拟 v4 现状。
  execFileSync('git', ['init', '-q', projectRoot])
  const scope: LocalFactScope = { worktreeLocator: projectRoot, governedProjectId: 'sample' }
  return { workspaceRoot, projectRoot, scope, cleanup: () => fs.rmSync(workspaceRoot, { recursive: true, force: true }) }
}

function writeSpark(projectRoot: string, id: string, extra = ''): void {
  fs.writeFileSync(
    path.join(projectRoot, 'ldvh-base', 'sparks', `${id}.yaml`),
    [
      'title: 直读 Spark',
      'status: open',
      'priority: P2',
      'source_refs:',
      '- kind: repository-path',
      '  locator: specs/09.md',
      'summary: 直读路径验证。',
      `object_id: ${id}`,
      'fact_type_key: spark',
      "created_at: '2026-07-20T08:00:00+08:00'",
      "updated_at: '2026-07-20T08:00:00+08:00'",
      extra,
      '',
    ].join('\n'),
  )
}

function writeWorkcase(projectRoot: string, id: string): void {
  fs.writeFileSync(
    path.join(projectRoot, 'ldvh-base', 'workcases', `${id}.yaml`),
    [
      'title: 直读 WorkCase',
      'status: closed',
      'source_refs:',
      '- kind: git-revision',
      '  locator: specs/00.md',
      '  version: abc123',
      `object_id: ${id}`,
      'fact_type_key: workcase',
      "created_at: '2026-07-19T08:00:00+08:00'",
      "updated_at: '2026-07-20T08:00:00+08:00'",
      '',
    ].join('\n'),
  )
}

const STUDY_BODY = '## 研究问题\n\n直读路径是否保留 Markdown 正文？\n'

function writeStudy(projectRoot: string, id: string): void {
  fs.writeFileSync(
    path.join(projectRoot, 'ldvh-base', 'studies', `${id}.md`),
    [
      '---',
      'title: 直读 Study',
      'status: active',
      'source_refs:',
      '- kind: web-page',
      '  locator: https://example.com/',
      `object_id: ${id}`,
      'fact_type_key: study',
      "created_at: '2026-07-19T08:00:00+08:00'",
      "updated_at: '2026-07-19T08:00:00+08:00'",
      '---',
      '',
      STUDY_BODY,
    ].join('\n'),
  )
}

test('直读五类对象列表：有目录的类型返回对象，缺失目录的类型如实标注', async () => {
  const { projectRoot, scope, cleanup } = makeWorkspace()
  try {
    writeSpark(projectRoot, 'spark-0001')
    writeWorkcase(projectRoot, 'workcase-0001')
    writeStudy(projectRoot, 'study-0001')

    for (const [type, id] of [['spark', 'spark-0001'], ['workcase', 'workcase-0001'], ['study', 'study-0001']] as const) {
      const result = await listObjects(type, undefined, undefined, scope)
      assert.equal(result.ok, true)
      if (!result.ok) continue
      assert.equal(result.data.coverage_status, 'complete')
      const items = result.data.items as Array<Record<string, unknown>>
      assert.equal(items.length, 1)
      assert.equal(items[0].object_id, id)
      assert.equal(items[0].fact_type_key, type)
      assert.deepEqual(items[0].object_ref, {
        governed_project_id: 'sample',
        fact_type_key: type,
        object_id: id,
      })
      assert.equal(items[0].canonical_path, `ldvh-base/${FACT_TYPE_DIRS[type]}/${id}.${type === 'study' ? 'md' : 'yaml'}`)
      assert.equal(typeof items[0].absolute_path, 'string')
    }

    // item-02：adr/pitfall 目录缺失 → 独立 type_not_integrated，且诊断 items 非空。
    for (const type of ['adr', 'pitfall'] as const) {
      const result = await listObjects(type, undefined, undefined, scope)
      assert.equal(result.ok, true)
      if (!result.ok) continue
      assert.equal(result.data.coverage_status, 'type_not_integrated')
      const diagnosticItems = result.data.items as Array<Record<string, unknown>>
      assert.equal(diagnosticItems.length, 1)
      assert.equal(diagnosticItems[0].kind, 'type_not_integrated')
      assert.equal(diagnosticItems[0].status, 'type_not_integrated')
      assert.equal(result.issues.length, 1)
      assert.equal(result.issues[0].code, 'type_not_integrated')
      assert.match(String(result.issues[0].message), /尚未接入/)
    }
  } finally {
    cleanup()
  }
})

test('study 直读解析 frontmatter 元数据并保留 Markdown 正文', async () => {
  const { projectRoot, scope, cleanup } = makeWorkspace()
  try {
    writeStudy(projectRoot, 'study-0001')
    const listed = await listLocalFacts('study', scope)
    assert.equal(listed.status, 'complete')
    assert.equal(listed.items.length, 1)
    const item = listed.items[0]
    assert.equal(item.check_status, 'unverified')
    assert.equal(item.fact_object.title, '直读 Study')
    assert.equal(item.fact_object.object_id, 'study-0001')
    assert.equal(item.fact_object.report_body, STUDY_BODY)

    const detail = await showObject('study-0001', scope)
    assert.equal(detail.ok, true)
    if (detail.ok) {
      assert.equal(detail.data.report_body, STUDY_BODY)
      assert.equal(detail.summary.type, 'study')
      assert.equal(detail.summary.status, 'active')
    }
  } finally {
    cleanup()
  }
})

test('详情直读：五类 object_id 格式被接受，不存在对象如实 404，目录缺失如实上报', async () => {
  const { projectRoot, scope, cleanup } = makeWorkspace()
  try {
    writeSpark(projectRoot, 'spark-0001')

    const spark = await showObject('spark-0001', scope)
    assert.equal(spark.ok, true)
    if (spark.ok) {
      assert.equal(spark.data.object_id, 'spark-0001')
      assert.equal(spark.data.check_status, 'unverified')
      assert.equal(spark.summary.id, 'spark-0001')
      assert.equal(spark.summary.type, 'spark')
      assert.equal(spark.summary.status, 'open')
    }

    // 放宽到五类的 id 格式校验：workcase/adr/pitfall/study 不再被格式拒绝。
    const workcase = await showObject('workcase-0009', scope)
    assert.equal(workcase.ok, false)
    if (!workcase.ok) assert.match(workcase.error, /Object not found/)

    const adr = await showObject('adr-0001', scope)
    assert.equal(adr.ok, false)
    if (!adr.ok) assert.match(adr.error, /尚未接入/)

    // 非法 id 仍然拒绝。
    const invalid = await showObject('not-a-fact', scope)
    assert.equal(invalid.ok, false)

    const read = await readLocalFact('adr', 'adr-0001', scope)
    assert.equal(read.status, 'type_not_integrated')
  } finally {
    cleanup()
  }
})

test('已接入但暂无数据与类型未接入可区分', async () => {
  const { projectRoot, scope, cleanup } = makeWorkspace()
  try {
    fs.mkdirSync(path.join(projectRoot, 'ldvh-base', 'adrs'))
    const integratedEmpty = await listObjects('adr', undefined, undefined, scope)
    assert.equal(integratedEmpty.ok, true)
    if (!integratedEmpty.ok) return
    assert.equal(integratedEmpty.data.coverage_status, 'complete')
    assert.deepEqual(integratedEmpty.data.items, [])

    const notIntegrated = await listObjects('pitfall', undefined, undefined, scope)
    assert.equal(notIntegrated.ok, true)
    if (!notIntegrated.ok) return
    assert.equal(notIntegrated.data.coverage_status, 'type_not_integrated')
    assert.equal((notIntegrated.data.items as unknown[]).length, 1)
  } finally {
    cleanup()
  }
})

test('只读取各类型正式载体，错扩展名进入 issue 且详情 unavailable', async () => {
  const { projectRoot, scope, cleanup } = makeWorkspace()
  try {
    writeSpark(projectRoot, 'spark-0001')
    fs.writeFileSync(path.join(projectRoot, 'ldvh-base', 'sparks', 'spark-0002.md'), '# wrong carrier\n')
    fs.writeFileSync(path.join(projectRoot, 'ldvh-base', 'studies', 'study-0002.yaml'), 'object_id: study-0002\nfact_type_key: study\n')

    const sparks = await listLocalFacts('spark', scope)
    assert.deepEqual(sparks.items.map((item) => item.object_ref.object_id), ['spark-0001'])
    assert.equal(sparks.issues.length, 1)
    assert.equal(sparks.issues[0].code, 'unexpected_fact_carrier')

    const studies = await listLocalFacts('study', scope)
    assert.equal(studies.items.length, 0)
    assert.equal(studies.issues[0].code, 'unexpected_fact_carrier')

    const wrongDetail = await readLocalFact('spark', 'spark-0002', scope)
    assert.equal(wrongDetail.status, 'unavailable')
    const shown = await showObject('spark-0002', scope)
    assert.equal(shown.ok, false)
    if (!shown.ok) assert.equal(shown.exitCode, 'unexpected_fact_carrier')
  } finally {
    cleanup()
  }
})

test('解析失败与字段缺失如实记录在 issues，不拦截呈现', async () => {
  const { projectRoot, scope, cleanup } = makeWorkspace()
  try {
    fs.writeFileSync(
      path.join(projectRoot, 'ldvh-base', 'sparks', 'spark-0002.yaml'),
      'title: [unclosed\n  broken: yaml',
    )
    fs.writeFileSync(
      path.join(projectRoot, 'ldvh-base', 'sparks', 'spark-0003.yaml'),
      'title: 缺字段\nstatus: open\n',
    )
    const listed = await listLocalFacts('spark', scope)
    assert.equal(listed.status, 'complete')
    assert.equal(listed.items.length, 2)

    const broken = listed.items.find((item) => item.object_ref.object_id === 'spark-0002')
    assert.ok(broken)
    assert.equal(broken.check_status, 'parse_failed')
    assert.ok(broken.issues.some((issue) => issue.code === 'yaml_parse_failed'))

    const missingFields = listed.items.find((item) => item.object_ref.object_id === 'spark-0003')
    assert.ok(missingFields)
    assert.equal(missingFields.check_status, 'unverified')
    assert.ok(missingFields.issues.some((issue) => issue.code === 'field_missing'))

    const result = await listObjects('spark', undefined, undefined, scope)
    assert.equal(result.ok, true)
    if (result.ok) {
      assert.equal(result.issues.length > 0, true)
      const problems = result.data.projection_problems as Array<Record<string, unknown>>
      assert.equal(problems.length, 2)
    }
  } finally {
    cleanup()
  }
})

test('create-spark 写入（Python 桥）→ 列表/详情直读回读结构一致', async () => {
  const repositoryRoot = path.resolve(import.meta.dirname, '../../..')
  const pythonExecutable = process.platform === 'win32'
    ? path.join(repositoryRoot, '.venv', 'Scripts', 'python.exe')
    : path.join(repositoryRoot, '.venv', 'bin', 'python')
  assert.equal(fs.existsSync(pythonExecutable), true)

  const { workspaceRoot, projectRoot, scope, cleanup } = makeWorkspace()
  fs.writeFileSync(
    path.join(workspaceRoot, 'LDVH-GOVERNED-PROJECTS.yaml'),
    [
      'product_name: Local facts consistency',
      'product_description: Write via bridge, read via local reader.',
      'projects:',
      '  - id: sample',
      `    path: ${projectRoot}`,
      '    name: Sample',
      '    description: Consistency project.',
      '',
    ].join('\n'),
  )
  try {
    const machineScope = {
      workspace_root: workspaceRoot,
      worktree_locator: projectRoot,
      expected_governed_project_id: 'sample',
    }
    const captured = await invokeV4FactsMachine({
      protocol_version: 1,
      operation: 'create-spark',
      scope: machineScope,
      arguments: { title: '回读一致性', description: '写入走 Python 桥，读取走本地直读。', priority: 'P2' },
    }, { pythonExecutable })
    assert.equal(captured.status, 'created')
    const created = captured.result as Record<string, unknown>
    const createdRef = created.actual_ref as Record<string, unknown>
    const objectId = String(createdRef.object_id)

    // 写入产物真实落盘于 ldvh-base/sparks/。
    assert.equal(fs.existsSync(path.join(projectRoot, String(created.canonical_path))), true)

    // 列表直读回读：与 create 响应的 ref/canonical_path/fact_object 一致。
    const listed = await listObjects('spark', undefined, undefined, scope)
    assert.equal(listed.ok, true)
    if (!listed.ok) return
    const items = listed.data.items as Array<Record<string, unknown>>
    assert.equal(items.length, 1)
    const item = items[0]
    assert.equal(item.object_id, objectId)
    assert.deepEqual(item.object_ref, createdRef)
    assert.equal(item.canonical_path, created.canonical_path)
    const bridgeFact = created.fact_object as Record<string, unknown>
    for (const field of ['object_id', 'fact_type_key', 'title', 'summary', 'status', 'priority', 'created_at', 'updated_at', 'source_refs']) {
      assert.deepEqual(item[field], bridgeFact[field], `list item field ${field} matches bridge fact_object`)
    }

    // 详情直读回读：同一文件产出同一结构。
    const detail = await showObject(objectId, scope)
    assert.equal(detail.ok, true)
    if (!detail.ok) return
    assert.deepEqual(detail.data.object_ref, createdRef)
    assert.equal(detail.data.canonical_path, created.canonical_path)
    for (const field of ['object_id', 'fact_type_key', 'title', 'summary', 'status', 'created_at', 'updated_at']) {
      assert.deepEqual(detail.data[field], bridgeFact[field], `detail field ${field} matches bridge fact_object`)
    }
    assert.equal(detail.summary.id, objectId)
    assert.equal(detail.summary.type, 'spark')
  } finally {
    cleanup()
  }
})
