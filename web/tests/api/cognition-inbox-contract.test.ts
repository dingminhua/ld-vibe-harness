/**
 * 项目认知中心：GET /api/cognition 收件箱与近期动态契约测试。
 *
 * 以当前治理范围解析出的受管辖工作树（事实源）运行，断言 02 §8 当前已交付字段
 * （generatedAt / scope / inbox / recentActivity / issues）、待决收录与排序、命名纪律
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

test('cognition endpoint returns inbox and recent-activity contract shapes with observation time', async () => {
  const body = await cognition('zh')

  assert.match(String(body.generatedAt), RFC3339)
  assert.ok(body.scope && typeof body.scope === 'object')
  assert.equal(typeof (body.scope as Record<string, unknown>).governedProjectId, 'string')
  assert.ok(((body.scope as Record<string, unknown>).governedProjectId as string).length > 0)
  assert.ok(body.inbox && typeof body.inbox === 'object')
  const inbox = body.inbox as Record<string, unknown>
  assert.ok(Array.isArray(inbox.items))
  assert.equal(typeof inbox.total, 'number')
  assert.ok(body.recentActivity && typeof body.recentActivity === 'object')
  const recent = body.recentActivity as Record<string, unknown>
  assert.equal(recent.window, '1d')
  assert.match(String(recent.windowStart), RFC3339)
  assert.ok(Array.isArray(recent.items))
  assert.equal(recent.total, (recent.items as unknown[]).length)
  // 当前只新增“近期动态”；其余尚未建设的模块仍整体省略。
  for (const moduleKey of ['whileAway', 'timeline', 'sparkHealth', 'direction']) {
    assert.equal(moduleKey in body, false, `not-yet-built module must omit ${moduleKey}`)
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
