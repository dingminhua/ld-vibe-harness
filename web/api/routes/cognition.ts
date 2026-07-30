/**
 * Cognition API 路由：聚合项目认知中心第一期的待决定事项收件箱。
 *
 * 第一期只交付模块一（待决定事项）+ §5 全局信任标记所需的派生字段：
 * generatedAt（观察时间）、scope、inbox（两类 Human Gate 派生收录与排序）、issues（模块级降级）。
 * 数据经 Web 字段级直读（localFactReader / facts.ts 的 listObjects），不复用 /api/dashboard 聚合逻辑。
 *
 * 命名纪律（02 §7 第 3 条）：WorkCase 条目只携带 progress_group；待决类型 inboxKind
 * 仅表示 Human 的计划批准或关闭确认。blocked 仍由对象列表/详情如实呈现，不进入待决定收件箱。
 */

import { Router, type Request, type Response } from 'express'
import { listObjects } from '../services/facts.js'
import { deriveWorkCaseProgressProjection, type WorkCaseProgressGroup } from '../../shared/workcaseStatus.js'
import { ProjectScopeError, requestProject } from '../services/requestScope.js'
import { getRelativeTime } from '../services/time.js'
import { getTypeColor } from '../services/typeColors.js'

const router = Router()

type InboxKind = 'plan_confirmation' | 'closure_confirmation'

type CognitionIssue = { section: string; code: string; message: string; object_ref?: string }

/** 决定依据投影中属于对象身份的字段，不重复收入 card。 */
const IDENTITY_PROJECTION_KEYS = new Set([
  'object_id',
  'fact_type_key',
  'title',
  'title_en',
  'title_zh',
  'status',
  'phase',
  'updated_at',
  'priority',
  'read_status',
  'read_issues',
  'field_issues',
  'unparsed_structures',
])

interface InboxBuildItem {
  object_id: string
  title: string
  title_en?: string
  title_zh?: string
  status: string
  phase: string | undefined
  priority?: string
  updated_at?: string
  read_status: string
  projection: Record<string, unknown>
  field_issues: Array<Record<string, unknown>>
  unparsed_structures: Array<Record<string, unknown>>
  read_issues: Array<Record<string, unknown>>
}

/** P0=0 … P3=3；缺失或非法落 4（排最后，并省略优先级信号）。 */
function priorityRank(priority: unknown): number {
  if (typeof priority !== 'string') return 4
  const match = /^P([0-3])$/.exec(priority)
  if (!match) return 4
  return Number(match[1])
}

/** 与 localFactReader.metadataFor 的 workcase 公式一致：ldvh-base/workcases/{object_id}.yaml */
function workcaseCanonicalPath(objectId: string): string {
  return `ldvh-base/workcases/${objectId}.yaml`
}

function deriveInboxKind(_status: string, _phase: string | undefined, progressGroup: WorkCaseProgressGroup | null): InboxKind | null {
  if (progressGroup === 'plan_confirmation') return 'plan_confirmation'
  if (progressGroup === 'closure_confirmation') return 'closure_confirmation'
  return null
}

function compareInbox(a: InboxBuildItem, b: InboxBuildItem): number {
  const ra = priorityRank(a.priority)
  const rb = priorityRank(b.priority)
  if (ra !== rb) return ra - rb
  const ua = a.updated_at
  const ub = b.updated_at
  // updated_at 正序（等待最久在前）；相同按 object_id 升序 tiebreak；缺失排最后。
  if (ua && ub) {
    if (ua !== ub) return ua < ub ? -1 : 1
    return a.object_id.localeCompare(b.object_id)
  }
  if (ua && !ub) return -1
  if (!ua && ub) return 1
  return a.object_id.localeCompare(b.object_id)
}

function toIssue(record: Record<string, unknown>): CognitionIssue {
  return {
    section: String(record.section ?? 'inbox'),
    code: String(record.code ?? 'unknown'),
    message: String(record.message ?? ''),
    ...(record.object_ref !== undefined ? { object_ref: String(record.object_ref) } : {}),
  }
}

router.get('/', async (req: Request, res: Response): Promise<void> => {
  const generatedAt = new Date().toISOString()
  try {
    const locale = String(req.query.locale || 'zh')
    const project = await requestProject(req)
    const factScope = { worktreeLocator: project.path, governedProjectId: project.id }

    const result = await listObjects('workcase', undefined, undefined, factScope)
    const issues: CognitionIssue[] = []

    if (!result.ok || !('data' in result)) {
      const message = result.ok ? 'WorkCase 列表读取失败' : (result as { error: string }).error
      issues.push({ section: 'inbox', code: 'workcase_list_unavailable', message })
      res.json({
        generatedAt,
        scope: { governedProjectId: project.id },
        inbox: { items: [], total: 0 },
        issues,
      })
      return
    }

    const data = result.data as {
      items: Array<Record<string, unknown>>
      collection_issues?: Array<Record<string, unknown>>
    }
    const collectionIssues = Array.isArray(data.collection_issues) ? data.collection_issues : []
    for (const issue of collectionIssues) issues.push(toIssue(issue))

    const builds: InboxBuildItem[] = []
    for (const raw of data.items) {
      const object_id = String(raw.object_id ?? '')
      const status = String(raw.status ?? 'unknown')
      const phase = typeof raw.phase === 'string' ? raw.phase : undefined
      const progressGroup = deriveWorkCaseProgressProjection(status, phase)?.progressGroup ?? null
      // progress_group 不可派生不收入收件箱，经 issues 与未解析结构呈现（Q8）。
      if (progressGroup === null) {
        issues.push({
          section: 'inbox',
          code: 'progress_group_unresolved',
          message: `WorkCase ${object_id} 的进展分组无法由当前 status=${status} 派生，未收入收件箱`,
          object_ref: object_id,
        })
        continue
      }
      const inboxKind = deriveInboxKind(status, phase, progressGroup)
      if (inboxKind === null) continue

      builds.push({
        object_id,
        title: String(raw.title ?? object_id),
        ...(typeof raw.title_en === 'string' ? { title_en: raw.title_en } : {}),
        ...(typeof raw.title_zh === 'string' ? { title_zh: raw.title_zh } : {}),
        status,
        phase,
        priority: typeof raw.priority === 'string' ? raw.priority : undefined,
        updated_at: typeof raw.updated_at === 'string' ? raw.updated_at : undefined,
        read_status: String(raw.read_status ?? 'unknown'),
        projection: raw,
        field_issues: Array.isArray(raw.field_issues) ? (raw.field_issues as Array<Record<string, unknown>>) : [],
        unparsed_structures: Array.isArray(raw.unparsed_structures) ? (raw.unparsed_structures as Array<Record<string, unknown>>) : [],
        read_issues: Array.isArray(raw.read_issues) ? (raw.read_issues as Array<Record<string, unknown>>) : [],
      })
    }

    builds.sort(compareInbox)

    const items = builds.map((build) => {
      const progressGroup = deriveWorkCaseProgressProjection(build.status, build.phase)?.progressGroup ?? null
      const inboxKind = deriveInboxKind(build.status, build.phase, progressGroup) as InboxKind
      const card = Object.fromEntries(
        Object.entries(build.projection).filter(([key]) => !IDENTITY_PROJECTION_KEYS.has(key)),
      )
      const entry: Record<string, unknown> = {
        type: 'workcase',
        id: build.object_id,
        title: build.title,
        ...(build.title_en !== undefined ? { title_en: build.title_en } : {}),
        ...(build.title_zh !== undefined ? { title_zh: build.title_zh } : {}),
        relativeTime: getRelativeTime(build.updated_at ?? '', locale),
        typeColor: getTypeColor('workcase'),
        progress_group: progressGroup,
        inboxKind,
        read_status: build.read_status,
        card,
      }
      // priority 缺失/非法落 P3 之后并省略优先级信号（Q8）。
      if (priorityRank(build.priority) < 4 && typeof build.priority === 'string') entry.priority = build.priority
      // updated_at 缺失排最后并省略时间显示（Q8）。
      if (build.updated_at) entry.updatedAt = build.updated_at
      // 字段级直读 readable 时携带 canonical_path，供条件显示"复制对象路径"（Q4）。
      if (build.read_status === 'readable') entry.canonical_path = workcaseCanonicalPath(build.object_id)
      if (build.field_issues.length > 0) entry.field_issues = build.field_issues
      if (build.unparsed_structures.length > 0) entry.unparsed_structures = build.unparsed_structures
      if (build.read_issues.length > 0) entry.read_issues = build.read_issues
      return entry
    })

    res.json({
      generatedAt,
      scope: { governedProjectId: project.id },
      inbox: { items, total: items.length },
      ...(issues.length > 0 ? { issues } : {}),
    })
  } catch (err) {
    if (err instanceof ProjectScopeError) {
      res.status(400).json({ ok: false, error: err.message })
      return
    }
    res.status(500).json({ ok: false, error: 'Cognition aggregation failed' })
  }
})

export default router
