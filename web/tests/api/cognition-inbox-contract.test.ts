/**
 * 项目认知中心：GET /api/cognition 收件箱与近期动态契约测试。
 *
 * 以当前治理范围解析出的受管辖工作树（事实源）运行，断言 02 §8 当前已交付字段
 * （generatedAt / scope / inbox / activeWorkCases / recentActivity / sparkHealth / commitHotspots / issues）、待决与推进中收录及排序、命名纪律
 * （WorkCase 的两个 Human Gate progress_group，加上 Pitfall 的 draft 待确认）、
 * 内联对象卡片依据、条件 canonical_path，以及近期动态的窗口与时间标记。
 *
 * 断言以“不依赖具体对象身份的不变式”为主：无论事实源是本仓库还是预览工作树，
 * 收录 / 排序 / 命名 / 投影规则都必须确定性成立。
 */

import assert from 'node:assert/strict'
import type { Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import { after, before, test } from 'node:test'
import type { CommitHotspotBuildItem } from '../../api/routes/cognition.ts'
import type { GitLogEntryWithFiles } from '../../api/services/git.ts'

let server: Server
let baseUrl = ''

before(async () => {
  const { default: app } = await import('../../api/app.ts')
  server = app.listen(0)
  const address = server.address() as AddressInfo
  baseUrl = `http://127.0.0.1:${address.port}`
})

after(async () => {
  await new Promise<void>((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()))
  })
})

async function cognition(locale = 'zh', window = '1d') {
  const response = await fetch(`${baseUrl}/api/cognition?locale=${locale}&window=${window}`)
  assert.equal(response.status, 200)
  assert.match(response.headers.get('cache-control') ?? '', /no-store/)
  return (await response.json()) as Record<string, unknown>
}

const RFC3339 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)$/

function priorityRank(priority: unknown): number {
  if (typeof priority !== 'string') return 4
  const match = /^P([0-3])$/.exec(priority)
  return match ? Number(match[1]) : 4
}

/** 复制路由排序规则，用于校验收件箱顺序的确定性。 */
function compareSort(a: Record<string, unknown>, b: Record<string, unknown>): number {
  const ra = priorityRank(a.priority)
  const rb = priorityRank(b.priority)
  if (ra !== rb) return ra - rb
  const ua = typeof a.updatedAt === 'string' ? a.updatedAt : ''
  const ub = typeof b.updatedAt === 'string' ? b.updatedAt : ''
  const ha = ua !== ''
  const hb = ub !== ''
  if (ha && hb) {
    if (ua !== ub) return ua < ub ? -1 : 1
    return String(a.id).localeCompare(String(b.id))
  }
  if (ha && !hb) return -1
  if (!ha && hb) return 1
  return String(a.id).localeCompare(String(b.id))
}

/** WorkCase 条目仅由两个 Human Gate progress_group 推导期望的 inboxKind。 */
function expectedInboxKind(item: Record<string, unknown>): string | null {
  const pg = item.progress_group
  if (pg === 'plan_confirmation') return 'plan_confirmation'
  if (pg === 'closure_confirmation') return 'closure_confirmation'
  return null
}

test('cognition endpoint returns inbox, recent activity, Spark health, and commit hotspot contract shapes with observation time', async () => {
  const body = await cognition('zh')

  assert.match(String(body.generatedAt), RFC3339)
  assert.ok(body.scope && typeof body.scope === 'object')
  assert.equal(typeof (body.scope as Record<string, unknown>).governedProjectId, 'string')
  assert.ok(((body.scope as Record<string, unknown>).governedProjectId as string).length > 0)
  assert.ok(body.inbox && typeof body.inbox === 'object')
  const inbox = body.inbox as Record<string, unknown>
  assert.ok(Array.isArray(inbox.items))
  assert.equal(typeof inbox.total, 'number')
  assert.ok(body.activeWorkCases && typeof body.activeWorkCases === 'object')
  const activeWorkCases = body.activeWorkCases as Record<string, unknown>
  assert.ok(Array.isArray(activeWorkCases.items))
  assert.equal(activeWorkCases.total, (activeWorkCases.items as unknown[]).length)
  assert.ok(body.recentActivity && typeof body.recentActivity === 'object')
  const recent = body.recentActivity as Record<string, unknown>
  assert.equal(recent.window, '1d')
  assert.match(String(recent.windowStart), RFC3339)
  assert.ok(Array.isArray(recent.items))
  assert.equal(recent.total, (recent.items as unknown[]).length)
  assert.ok(body.sparkHealth && typeof body.sparkHealth === 'object')
  const sparkHealth = body.sparkHealth as Record<string, unknown>
  for (const key of ['total', 'openTotal', 'terminalTotal', 'silentThresholdDays', 'silentCount']) {
    assert.equal(typeof sparkHealth[key], 'number')
  }
  assert.ok(sparkHealth.terminalByStatus && typeof sparkHealth.terminalByStatus === 'object')
  assert.ok(sparkHealth.openByPriority && typeof sparkHealth.openByPriority === 'object')
  assert.ok(Array.isArray(sparkHealth.silentItems))
  assert.ok(body.commitHotspots && typeof body.commitHotspots === 'object')
  const hotspots = body.commitHotspots as Record<string, unknown>
  assert.equal(hotspots.window, '1d')
  for (const key of ['totalCommits', 'hotspotTotal', 'relationTotal']) {
    assert.equal(typeof hotspots[key], 'number')
  }
  assert.ok(Array.isArray(hotspots.clusters))
  assert.equal('independentHotspots' in hotspots, false)
  // 其余尚未建设的模块仍整体省略。
  for (const moduleKey of ['whileAway', 'timeline', 'direction']) {
    assert.equal(moduleKey in body, false, `not-yet-built module must omit ${moduleKey}`)
  }
})

test('commit hotspots preserve only deterministic commit mappings and one-hop formal relation shape', async () => {
  const body = await cognition('zh', '1d')
  const hotspots = body.commitHotspots as Record<string, unknown>
  assert.equal(hotspots.window, '1d')
  const clusters = hotspots.clusters as Array<Record<string, unknown>>
  const primaryKeys = new Set<string>()
  const scope = body.scope as Record<string, unknown>
  const projectId = String(scope.governedProjectId)
  const commitEvidence = new Map<string, Promise<{ message: string; files: Set<string> }>>()
  const getCommitEvidence = (hash: string) => {
    const cached = commitEvidence.get(hash)
    if (cached) return cached
    const pending = fetch(`${baseUrl}/api/project-files/git/commit/${hash}?projectId=${encodeURIComponent(projectId)}`)
      .then(async (response) => {
        assert.equal(response.status, 200)
        const payload = (await response.json()) as { commit: { message: string; body: string; files: Array<{ path: string }> } }
        return {
          message: `${payload.commit.message}\n${payload.commit.body}`,
          files: new Set(payload.commit.files.map((file) => file.path)),
        }
      })
    commitEvidence.set(hash, pending)
    return pending
  }
  const assertNode = async (node: Record<string, unknown>) => {
    assert.ok(['workcase', 'adr', 'pitfall', 'spark', 'study'].includes(String(node.type)))
    assert.match(String(node.id), /^(workcase|adr|pitfall|spark|study)-\d{4,}$/)
    assert.equal(typeof node.title, 'string')
    assert.equal(typeof node.typeColor, 'string')
    assert.ok(Array.isArray(node.commitRefs))
    const refs = node.commitRefs as Array<Record<string, unknown>>
    for (const ref of refs) {
      assert.match(String(ref.hash), /^[0-9a-f]{40}$/)
      assert.match(String(ref.shortHash), /^[0-9a-f]{7,}$/)
      assert.match(String(ref.date), RFC3339)
      assert.equal(typeof ref.relativeTime, 'string')
      assert.ok(['canonical_path', 'explicit_id', 'both'].includes(String(ref.mapping)))
      const evidence = await getCommitEvidence(String(ref.hash))
      const canonicalPath = `ldvh-base/${node.type === 'workcase' ? 'workcases' : `${node.type}s`}/${node.id}${node.type === 'study' ? '.md' : '.yaml'}`
      const mappedByPath = evidence.files.has(canonicalPath)
      const mappedById = new RegExp(`\\b${String(node.id).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`).test(evidence.message)
      if (ref.mapping === 'canonical_path') assert.equal(mappedByPath, true)
      if (ref.mapping === 'explicit_id') assert.equal(mappedById, true)
      if (ref.mapping === 'both') {
        assert.equal(mappedByPath, true)
        assert.equal(mappedById, true)
      }
    }
  }

  const uniqueRelations = new Set<string>()
  let previousPrimaryCommitTotal = Number.POSITIVE_INFINITY
  for (const cluster of clusters) {
    assert.ok(cluster.primary && typeof cluster.primary === 'object')
    const primary = cluster.primary as Record<string, unknown>
    await assertNode(primary)
    const primaryKey = `${primary.type}:${primary.id}`
    assert.equal(primaryKeys.has(primaryKey), false, `duplicate primary hotspot: ${primaryKey}`)
    primaryKeys.add(primaryKey)
    const primaryCommitTotal = (primary.commitRefs as unknown[]).length
    assert.ok(primaryCommitTotal > 0, 'each cluster must have exactly one traceable primary hotspot')
    assert.ok(primaryCommitTotal <= previousPrimaryCommitTotal, 'clusters must be ordered by primary traceable commit activity')
    previousPrimaryCommitTotal = primaryCommitTotal
    assert.ok(Array.isArray(cluster.relations))
    assert.ok((cluster.relations as unknown[]).length > 0)
    for (const relation of cluster.relations as Array<Record<string, unknown>>) {
      assert.ok(relation.direction === 'outgoing' || relation.direction === 'incoming')
      assert.equal(typeof relation.relationKey, 'string')
      assert.ok(String(relation.relationKey).length > 0)
      assert.ok(relation.node && typeof relation.node === 'object')
      const node = relation.node as Record<string, unknown>
      await assertNode(node)
      const nodeKey = `${node.type}:${node.id}`
      assert.notEqual(primaryKey, nodeKey)
      const source = relation.direction === 'outgoing' ? primaryKey : nodeKey
      const target = relation.direction === 'outgoing' ? nodeKey : primaryKey
      uniqueRelations.add(`${source}\u0000${target}\u0000${relation.relationKey}`)
    }
  }
  assert.equal(primaryKeys.size, hotspots.hotspotTotal)
  assert.equal(uniqueRelations.size, hotspots.relationTotal)
})

test('commit hotspot builder does not absorb transitive peers and rejects invalid relation semantics', async () => {
  const { buildCommitHotspots } = await import('../../api/routes/cognition.ts')
  const target = (fact_type_key: string, object_id: string) => ({ governed_project_id: 'demo', fact_type_key, object_id })
  const fact = (
    type: CommitHotspotBuildItem['type'],
    object_id: string,
    status: string,
    relations: unknown = undefined,
  ): CommitHotspotBuildItem => ({
    type,
    object_id,
    title: object_id,
    status,
    ...(type === 'workcase' ? { progress_group: status === 'closed' ? 'closed' : 'progressing' } : {}),
    read_status: 'readable',
    canonical_path: `ldvh-base/${type === 'study' ? 'studies' : `${type}s`}/${object_id}${type === 'study' ? '.md' : '.yaml'}`,
    relations,
  })
  const facts: CommitHotspotBuildItem[] = [
    fact('spark', 'spark-0001', 'open', [
      { relation_key: 'related-to', target: target('spark', 'spark-0002') },
    ]),
    fact('spark', 'spark-0002', 'open', [
      { relation_key: 'related-to', target: target('spark', 'spark-0003') },
    ]),
    fact('spark', 'spark-0003', 'open'),
    fact('study', 'study-0001', 'active', [
      { relation_key: 'informs', target: target('spark', 'spark-0001') },
    ]),
    fact('workcase', 'workcase-0001', 'open', [
      { relation_key: 'contributed-to', target: target('workcase', 'workcase-0002') },
    ]),
    fact('workcase', 'workcase-0002', 'open'),
  ]
  const commits: GitLogEntryWithFiles[] = [{
    hash: 'a'.repeat(40),
    shortHash: 'a'.repeat(7),
    author: 'Tester',
    date: '2026-08-01T00:00:00Z',
    message: 'feat: update spark hotspot',
    body: '',
    category: 'feat',
    scope: '',
    description: 'update spark hotspot',
    isBreaking: false,
    relativeTime: '1小时前',
    files: ['ldvh-base/sparks/spark-0001.yaml'],
  }]

  const result = buildCommitHotspots(commits, facts, 'demo')
  assert.equal(result.hotspotTotal, 1)
  assert.equal(result.relationTotal, 2)
  assert.equal(result.clusters.length, 1)
  assert.equal(result.clusters[0].primary.id, 'spark-0001')
  assert.deepEqual(
    result.clusters[0].relations.map((relation) => `${relation.direction}:${relation.relationKey}:${relation.node.id}`),
    ['outgoing:related-to:spark-0002', 'incoming:informs:study-0001'],
  )
  assert.equal(result.clusters[0].relations.some((relation) => relation.node.id === 'spark-0003'), false)
  assert.equal(result.clusters[0].relations.some((relation) => relation.node.id === 'workcase-0002'), false)
})

test('Spark health splits the current pool into terminal and open items, then lists only silent open Sparks', async () => {
  const body = await cognition('zh')
  const health = body.sparkHealth as Record<string, unknown>
  const terminalByStatus = health.terminalByStatus as Record<string, unknown>
  const terminalTotal = Number(terminalByStatus.routed) + Number(terminalByStatus.implemented) + Number(terminalByStatus.discarded)

  assert.equal(Number(health.total), Number(health.openTotal) + terminalTotal)
  assert.equal(Number(health.terminalTotal), terminalTotal)
  assert.ok(Number(health.silentThresholdDays) > 0)
  const silentItems = health.silentItems as Array<Record<string, unknown>>
  assert.equal(Number(health.silentCount), silentItems.length)
  for (let index = 0; index < silentItems.length; index += 1) {
    const item = silentItems[index]
    assert.equal(item.type, 'spark')
    assert.equal(typeof item.id, 'string')
    assert.ok(Number(item.silentDays) >= Number(health.silentThresholdDays))
    assert.equal(typeof item.updatedAt, 'string')
    if (index > 0) assert.ok(Number(silentItems[index - 1].silentDays) >= Number(item.silentDays))
  }
})

test('recent activity accepts only explicit windows and marks current fact objects by created_at or updated_at', async () => {
  for (const window of ['1d', '3d', '7d', '14d']) {
    const body = await cognition('zh', window)
    const recent = body.recentActivity as Record<string, unknown>
    assert.equal(recent.window, window)
    const items = recent.items as Array<Record<string, unknown>>
    const expected = items.slice().sort((a, b) => {
      const at = String(a.occurredAt)
      const bt = String(b.occurredAt)
      if (at !== bt) return at > bt ? -1 : 1
      if (a.activity !== b.activity) return a.activity === 'updated' ? -1 : 1
      return `${a.type}:${a.id}`.localeCompare(`${b.type}:${b.id}`)
    })
    assert.deepEqual(items.map((item) => `${item.activity}:${item.type}:${item.id}:${item.occurredAt}`), expected.map((item) => `${item.activity}:${item.type}:${item.id}:${item.occurredAt}`))
    for (const item of items) {
      assert.ok(['workcase', 'adr', 'pitfall', 'spark', 'study'].includes(String(item.type)))
      assert.ok(['created', 'updated'].includes(String(item.activity)))
      assert.match(String(item.occurredAt), RFC3339)
      assert.equal(typeof item.relativeTime, 'string')
      assert.equal(typeof item.typeColor, 'string')
      if (item.type === 'workcase') {
        assert.equal('status' in item, false)
      } else {
        assert.equal(typeof item.status, 'string')
        assert.equal('progress_group' in item, false)
      }
    }
  }

  const response = await fetch(`${baseUrl}/api/cognition?locale=zh&window=30d`)
  assert.equal(response.status, 400)
})

test('inbox collects only decision-baseline items with a deterministic sort order', async () => {
  const body = await cognition('zh')
  const inbox = body.inbox as Record<string, unknown>
  const items = inbox.items as Array<Record<string, unknown>>

  assert.equal(inbox.total, items.length)
  assert.ok(items.length >= 1, '收件箱至少含一个待决定事项')

  // 排序确定性：实际顺序必须等于按路由规则重排的顺序。
  const expected = items.slice().sort(compareSort)
  const actualIds = items.map((i) => String(i.id))
  const expectedIds = expected.map((i) => String(i.id))
  assert.deepEqual(actualIds, expectedIds)

  // 优先级最小者排在最前（P0 > P1 > …）；缺失/非法优先级排最后。
  const ranks = items.map((i) => priorityRank(i.priority))
  const minRank = Math.min(...ranks)
  assert.equal(priorityRank(items[0].priority), minRank)
  // 缺失优先级项必须排在所有合法 P0-P3 之后（Q8）；非法优先级同为 rank 4 也归入末尾。
  const validIndices = items
    .map((i, idx) => ({ i, idx }))
    .filter(({ i }) => typeof i.priority === 'string' && /^P[0-3]$/.test(String(i.priority)))
    .map(({ idx }) => idx)
  const lastValidIndex = validIndices.length > 0 ? Math.max(...validIndices) : -1
  items.forEach((i, idx) => {
    if (!('priority' in i)) {
      assert.ok(idx > lastValidIndex, 'missing-priority item must come after all valid P0-P3 items')
    }
  })
})

test('active WorkCases contain only the progressing group and reuse the list Card projection', async () => {
  const body = await cognition('zh')
  const active = body.activeWorkCases as Record<string, unknown>
  const items = active.items as Array<Record<string, unknown>>
  const inboxIds = new Set(
    ((body.inbox as Record<string, unknown>).items as Array<Record<string, unknown>>)
      .map((item) => String(item.id)),
  )

  assert.equal(active.total, items.length)
  assert.deepEqual(items.map((item) => String(item.id)), items.slice().sort(compareSort).map((item) => String(item.id)))
  for (const item of items) {
    assert.equal(item.type, 'workcase')
    assert.equal(item.progress_group, 'progressing')
    assert.equal(typeof item.phase, 'string')
    assert.equal(typeof item.isBlocked, 'boolean')
    assert.equal('status' in item, false)
    assert.equal('inboxKind' in item, false)
    assert.equal(inboxIds.has(String(item.id)), false, 'progressing item must not duplicate a Human Gate item')
    assert.ok(item.card && typeof item.card === 'object')
    const card = item.card as Record<string, unknown>
    assert.equal(typeof card.goal, 'string')
    assert.equal('object_id' in card, false)
    assert.equal('status' in card, false)
    assert.equal('phase' in card, false)
    if ('progress_step' in item) {
      assert.ok(['item_execution', 'controller_self_check', 'independent_review', 'controller_synthesis'].includes(String(item.progress_step)))
    }
  }
})

test('inbox keeps WorkCase Human Gates separate from Pitfall draft confirmation', async () => {
  const body = await cognition('zh')
  const items = (body.inbox as Record<string, unknown>).items as Array<Record<string, unknown>>

  const kinds = new Set<string>()
  let workCaseCount = 0
  let pitfallCount = 0
  for (const item of items) {
    if (item.type === 'workcase') {
      workCaseCount += 1
      assert.ok(['plan_confirmation', 'closure_confirmation'].includes(String(item.progress_group)))
      assert.ok(['plan_confirmation', 'closure_confirmation'].includes(String(item.inboxKind)))
      // WorkCase 条目只携带 progress_group；不得把来源 status 放在名为 status 的字段（02 §7.3）。
      assert.equal('status' in item, false)
      assert.equal(item.inboxKind, expectedInboxKind(item))
    } else if (item.type === 'pitfall') {
      pitfallCount += 1
      assert.equal(item.status, 'draft')
      assert.equal(item.inboxKind, 'pitfall_confirmation')
      assert.equal('progress_group' in item, false)
    } else {
      assert.fail(`unexpected inbox object type: ${String(item.type)}`)
    }
    assert.equal(typeof item.relativeTime, 'string')
    assert.equal(typeof item.typeColor, 'string')
    assert.equal('source_status' in item, false)
    kinds.add(String(item.inboxKind))
  }
  assert.ok(workCaseCount > 0)
  assert.ok(pitfallCount > 0)
  assert.ok(kinds.has('plan_confirmation'))
  assert.ok(kinds.has('closure_confirmation'))
  assert.ok(kinds.has('pitfall_confirmation'))
})

test('priority signal is shown only for valid P0-P3 and omitted for missing/invalid', async () => {
  const body = await cognition('zh')
  const items = (body.inbox as Record<string, unknown>).items as Array<Record<string, unknown>>

  for (const item of items) {
    if ('priority' in item) {
      assert.match(String(item.priority), /^P[0-3]$/)
    }
  }
  // 若存在缺失/非法优先级的条目，它们必须排在所有合法 P0-P3 之后（Q8）。
  const missing = items.filter((i) => !('priority' in i))
  if (missing.length > 0) {
    const lastLegalIndex = items.length - missing.length - 1
    for (let i = 0; i < items.length; i++) {
      if (!('priority' in items[i])) assert.ok(i > lastLegalIndex)
    }
  }
})

test('decision basis is inlined via each source object card projection (Q3)', async () => {
  const body = await cognition('zh')
  const items = (body.inbox as Record<string, unknown>).items as Array<Record<string, unknown>>

  for (const item of items) {
    assert.ok('card' in item)
    const card = item.card as Record<string, unknown>
    if (item.type === 'workcase') {
      assert.equal(typeof card.goal, 'string')
      if (item.inboxKind === 'plan_confirmation') {
        assert.ok(Array.isArray(card.successCriteria), 'plan item carries successCriteria array')
        for (const field of ['scope', 'success_criterion_definitions', 'work_items', 'creation_reviews', 'execution_authorization']) {
          if (field in card) assert.notEqual(card[field], undefined, `${field} preserves its source value`)
        }
      }
    } else {
      assert.equal(item.type, 'pitfall')
      for (const field of ['symptoms', 'trigger_conditions', 'applicability', 'root_cause', 'resolution', 'avoidance', 'validation_summary']) {
        if (field in card) assert.notEqual(card[field], undefined, `${field} preserves its source value`)
      }
    }
    // 身份字段不重复收入 card。
    assert.equal('object_id' in card, false)
    assert.equal('status' in card, false)
    assert.equal('progress_group' in card, false)
  }
})

test('readable items carry canonical_path for conditional copy (Q4); time omission when missing', async () => {
  const body = await cognition('zh')
  const items = (body.inbox as Record<string, unknown>).items as Array<Record<string, unknown>>

  assert.ok(items.length > 0)
  for (const item of items) {
    // 字段级直读 readable 时携带 canonical_path，供条件显示“复制对象路径”。
    const collection = item.type === 'workcase' ? 'workcases' : 'pitfalls'
    assert.equal(item.canonical_path, `ldvh-base/${collection}/${String(item.id)}.yaml`)
    // updated_at 缺失排最后并省略时间显示（Q8）：有则带 updatedAt 字符串。
    if (item.read_status === 'readable' && typeof item.updatedAt !== 'string') {
      // 缺失时该条目应处于排序末尾（上方排序测试已覆盖），此处仅记录形状。
      assert.equal(typeof item.updatedAt, 'undefined')
    }
  }
})

test('observation time and inbox survive locale switch without leaking raw status/enum', async () => {
  const zh = await cognition('zh')
  const en = await cognition('en')

  assert.match(String(zh.generatedAt), RFC3339)
  assert.match(String(en.generatedAt), RFC3339)
  // 同一观察窗口下，收件箱对象集合与排序与语言无关（locale 仅影响 relativeTime 文案）。
  const zhIds = ((zh.inbox as Record<string, unknown>).items as Array<Record<string, unknown>> | undefined)?.map((i) => String(i.id))
  const enIds = ((en.inbox as Record<string, unknown>).items as Array<Record<string, unknown>> | undefined)?.map((i) => String(i.id))
  assert.deepEqual(zhIds, enIds)
})

test('module-level degradation is surfaced via issues without breaking the contract', async () => {
  const body = await cognition('zh')
  // 当前事实源无模块级降级：issues 省略（仅在存在时返回数组）。
  if ('issues' in body) {
    assert.ok(Array.isArray(body.issues))
  }
})
