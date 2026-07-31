/**
 * Cognition API 路由：聚合项目认知中心的待决定事项与近期动态。
 *
 * 已交付模块一（待决定事项）、模块二（近期动态）与模块四（Spark 池健康）
 * + §5 全局信任标记所需的派生字段：
 * generatedAt（观察时间）、scope、inbox（WorkCase Human Gate 与 Pitfall draft 审核的派生收录与排序）、
 * recentActivity（指定窗口内事实对象的创建 / 更新标记）与 issues（模块级降级）。
 * 数据经 Web 字段级直读（localFactReader / facts.ts 的 listObjects），不复用 /api/dashboard 聚合逻辑。
 *
 * 命名纪律（02 §7 第 3 条）：WorkCase 条目只携带 progress_group；待决类型 inboxKind
 * 表示 Human 的计划批准、关闭确认或 Pitfall draft 审核。blocked 仍由对象列表/详情如实呈现，不进入待决定收件箱。
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, type ObjectType } from '../services/facts.js'
import { FACT_TYPE_CARRIERS, FACT_TYPE_DIRS, listLocalFacts, type LocalFactItem } from '../services/localFactReader.js'
import { getGitLogWithFiles, type GitLogEntryWithFiles } from '../services/git.js'
import { deriveWorkCaseProgressProjection, type WorkCaseProgressGroup } from '../../shared/workcaseStatus.js'
import { ProjectScopeError, requestProject } from '../services/requestScope.js'
import { getRelativeTime } from '../services/time.js'
import { getTypeColor } from '../services/typeColors.js'

const router = Router()

type InboxKind = 'plan_confirmation' | 'closure_confirmation' | 'pitfall_confirmation'
type InboxObjectType = 'workcase' | 'pitfall'
type RecentActivityKind = 'created' | 'updated'
type RecentActivityWindow = '1d' | '3d' | '7d' | '14d'
type CommitMappingKind = 'canonical_path' | 'explicit_id' | 'both'

const RECENT_ACTIVITY_WINDOWS: Record<RecentActivityWindow, number> = {
  '1d': 1,
  '3d': 3,
  '7d': 7,
  '14d': 14,
}
const SPARK_SILENT_THRESHOLD_DAYS = 5
const SPARK_TERMINAL_STATUSES = new Set(['routed', 'implemented', 'discarded'])
const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000

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
  type: InboxObjectType
  inboxKind: InboxKind
  object_id: string
  title: string
  title_en?: string
  title_zh?: string
  status: string
  phase: string | undefined
  progress_group?: WorkCaseProgressGroup
  priority?: string
  updated_at?: string
  read_status: string
  projection: Record<string, unknown>
  field_issues: Array<Record<string, unknown>>
  unparsed_structures: Array<Record<string, unknown>>
  read_issues: Array<Record<string, unknown>>
}

interface RecentActivityBuildItem {
  type: ObjectType
  object_id: string
  title: string
  title_en?: string
  title_zh?: string
  activity: RecentActivityKind
  occurred_at: string
  status?: string
  progress_group?: WorkCaseProgressGroup
  priority?: string
  read_status: string
  field_issues: Array<Record<string, unknown>>
  unparsed_structures: Array<Record<string, unknown>>
}

interface SparkHealthBuildItem {
  object_id: string
  title: string
  title_en?: string
  title_zh?: string
  priority?: string
  updated_at: string
  silent_days: number
  read_status: string
  field_issues: Array<Record<string, unknown>>
  unparsed_structures: Array<Record<string, unknown>>
}

interface CommitHotspotBuildItem {
  type: ObjectType
  object_id: string
  title: string
  title_en?: string
  title_zh?: string
  status?: string
  progress_group?: WorkCaseProgressGroup
  priority?: string
  read_status: string
  canonical_path: string
  relations: unknown
}

interface CommitHotspotRef {
  hash: string
  shortHash: string
  date: string
  relativeTime: string
  mapping: CommitMappingKind
}

interface CommitHotspotNode extends Omit<CommitHotspotBuildItem, 'object_id' | 'canonical_path' | 'relations'> {
  id: string
  typeColor: string
  commitRefs: CommitHotspotRef[]
}

interface CommitHotspotEdge {
  source: string
  target: string
  relationKey: string
}

/** P0=0 … P3=3；缺失或非法落 4（排最后，并省略优先级信号）。 */
function priorityRank(priority: unknown): number {
  if (typeof priority !== 'string') return 4
  const match = /^P([0-3])$/.exec(priority)
  if (!match) return 4
  return Number(match[1])
}

/** 与 localFactReader.metadataFor 一致：按事实类型返回当前 canonical path。 */
function canonicalPath(type: InboxObjectType, objectId: string): string {
  return `ldvh-base/${type === 'workcase' ? 'workcases' : 'pitfalls'}/${objectId}.yaml`
}

function factCanonicalPath(type: ObjectType, objectId: string): string {
  return `ldvh-base/${FACT_TYPE_DIRS[type]}/${objectId}${FACT_TYPE_CARRIERS[type]}`
}

function factKey(type: string, objectId: string): string {
  return `${type}:${objectId}`
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

function parseRecentActivityWindow(value: unknown): RecentActivityWindow | null {
  if (value === undefined || value === '') return '1d'
  return typeof value === 'string' && value in RECENT_ACTIVITY_WINDOWS
    ? value as RecentActivityWindow
    : null
}

function timestampInWindow(value: unknown, start: number, end: number): value is string {
  if (typeof value !== 'string') return false
  const timestamp = Date.parse(value)
  return Number.isFinite(timestamp) && timestamp >= start && timestamp <= end
}

function compareRecentActivity(a: RecentActivityBuildItem, b: RecentActivityBuildItem): number {
  if (a.occurred_at !== b.occurred_at) return a.occurred_at > b.occurred_at ? -1 : 1
  if (a.activity !== b.activity) return a.activity === 'updated' ? -1 : 1
  if (a.type !== b.type) return a.type.localeCompare(b.type)
  return a.object_id.localeCompare(b.object_id)
}

function buildRecentActivityItem(
  raw: Record<string, unknown>,
  type: ObjectType,
  activity: RecentActivityKind,
  occurredAt: string,
): RecentActivityBuildItem {
  const object_id = String(raw.object_id ?? '')
  const status = String(raw.status ?? 'unknown')
  const phase = typeof raw.phase === 'string' ? raw.phase : undefined
  const progressGroup = type === 'workcase'
    ? deriveWorkCaseProgressProjection(status, phase)?.progressGroup ?? undefined
    : undefined
  return {
    type,
    object_id,
    title: String(raw.title ?? object_id),
    ...(typeof raw.title_en === 'string' ? { title_en: raw.title_en } : {}),
    ...(typeof raw.title_zh === 'string' ? { title_zh: raw.title_zh } : {}),
    activity,
    occurred_at: occurredAt,
    ...(type === 'workcase' ? { progress_group: progressGroup } : { status }),
    ...(priorityRank(raw.priority) < 4 && typeof raw.priority === 'string' ? { priority: raw.priority } : {}),
    read_status: String(raw.read_status ?? 'unknown'),
    field_issues: Array.isArray(raw.field_issues) ? raw.field_issues as Array<Record<string, unknown>> : [],
    unparsed_structures: Array.isArray(raw.unparsed_structures) ? raw.unparsed_structures as Array<Record<string, unknown>> : [],
  }
}

function silentDays(updatedAt: unknown, observedAt: number): number | null {
  if (typeof updatedAt !== 'string') return null
  const updatedAtMs = Date.parse(updatedAt)
  if (!Number.isFinite(updatedAtMs) || updatedAtMs > observedAt) return null
  return Math.floor((observedAt - updatedAtMs) / MILLISECONDS_PER_DAY)
}

function compareSilentSpark(a: SparkHealthBuildItem, b: SparkHealthBuildItem): number {
  if (a.silent_days !== b.silent_days) return b.silent_days - a.silent_days
  const priorityDifference = priorityRank(a.priority) - priorityRank(b.priority)
  if (priorityDifference !== 0) return priorityDifference
  if (a.updated_at !== b.updated_at) return a.updated_at < b.updated_at ? -1 : 1
  return a.object_id.localeCompare(b.object_id)
}

/** Spark 健康度只聚合当前状态与更新时间；不从更新时间推断实际分流发生时刻。 */
function buildSparkHealth(rawItems: Array<Record<string, unknown>>, observedAt: number) {
  const terminalByStatus = { routed: 0, implemented: 0, discarded: 0 }
  const openByPriority: Record<string, number> = {}
  const silentItems: SparkHealthBuildItem[] = []
  let total = 0
  let openTotal = 0

  for (const raw of rawItems) {
    const status = typeof raw.status === 'string' ? raw.status : ''
    if (status !== 'open' && !SPARK_TERMINAL_STATUSES.has(status)) continue
    total += 1
    if (status !== 'open') {
      terminalByStatus[status as keyof typeof terminalByStatus] += 1
      continue
    }

    openTotal += 1
    const priority = priorityRank(raw.priority) < 4 && typeof raw.priority === 'string' ? raw.priority : undefined
    if (priority) openByPriority[priority] = (openByPriority[priority] ?? 0) + 1
    const updatedAt = typeof raw.updated_at === 'string' ? raw.updated_at : ''
    const days = silentDays(updatedAt, observedAt)
    if (days === null || days < SPARK_SILENT_THRESHOLD_DAYS) continue
    silentItems.push({
      object_id: String(raw.object_id ?? ''),
      title: String(raw.title ?? raw.object_id ?? ''),
      ...(typeof raw.title_en === 'string' ? { title_en: raw.title_en } : {}),
      ...(typeof raw.title_zh === 'string' ? { title_zh: raw.title_zh } : {}),
      ...(priority ? { priority } : {}),
      updated_at: updatedAt,
      silent_days: days,
      read_status: String(raw.read_status ?? 'unknown'),
      field_issues: Array.isArray(raw.field_issues) ? raw.field_issues as Array<Record<string, unknown>> : [],
      unparsed_structures: Array.isArray(raw.unparsed_structures) ? raw.unparsed_structures as Array<Record<string, unknown>> : [],
    })
  }

  silentItems.sort(compareSilentSpark)
  const terminalTotal = terminalByStatus.routed + terminalByStatus.implemented + terminalByStatus.discarded
  return {
    total,
    openTotal,
    terminalTotal,
    terminalByStatus,
    openByPriority,
    silentThresholdDays: SPARK_SILENT_THRESHOLD_DAYS,
    silentCount: silentItems.length,
    silentItems,
  }
}

function buildCommitHotspotFact(
  raw: Record<string, unknown>,
  type: ObjectType,
  relations: unknown = raw.relations,
): CommitHotspotBuildItem | null {
  const objectId = typeof raw.object_id === 'string' ? raw.object_id : ''
  const factType = typeof raw.fact_type_key === 'string' ? raw.fact_type_key : ''
  if (!objectId || factType !== type) return null
  const status = typeof raw.status === 'string' ? raw.status : undefined
  const phase = typeof raw.phase === 'string' ? raw.phase : undefined
  const progressGroup = type === 'workcase' && status
    ? deriveWorkCaseProgressProjection(status, phase)?.progressGroup
    : undefined
  const priority = priorityRank(raw.priority) < 4 && typeof raw.priority === 'string' ? raw.priority : undefined
  return {
    type,
    object_id: objectId,
    title: typeof raw.title === 'string' && raw.title ? raw.title : objectId,
    ...(typeof raw.title_en === 'string' ? { title_en: raw.title_en } : {}),
    ...(typeof raw.title_zh === 'string' ? { title_zh: raw.title_zh } : {}),
    ...(type === 'workcase' ? { progress_group: progressGroup } : { status }),
    ...(priority ? { priority } : {}),
    read_status: typeof raw.read_status === 'string' ? raw.read_status : 'unknown',
    canonical_path: factCanonicalPath(type, objectId),
    relations,
  }
}

function projectWorkCaseHotspotFact(item: LocalFactItem): CommitHotspotBuildItem | null {
  if (item.fact_object === null) return null
  return buildCommitHotspotFact({
    ...item.fact_object,
    read_status: item.read_status,
  }, 'workcase', item.fact_object.relations)
}

function extractExplicitObjectIds(message: string): string[] {
  const ids = new Set<string>()
  for (const match of message.matchAll(/\b(workcase|adr|pitfall|spark|study)-\d{4,}\b/g)) {
    ids.add(factKey(match[1], match[0]))
  }
  return [...ids]
}

function mergeCommitMapping(
  target: Map<string, CommitHotspotRef>,
  nodeKey: string,
  commit: GitLogEntryWithFiles,
  mappedByPath: boolean,
  mappedById: boolean,
): void {
  if (!mappedByPath && !mappedById) return
  const mapping: CommitMappingKind = mappedByPath && mappedById
    ? 'both'
    : mappedByPath ? 'canonical_path' : 'explicit_id'
  const previous = target.get(nodeKey)
  if (!previous) {
    target.set(nodeKey, {
      hash: commit.hash,
      shortHash: commit.shortHash,
      date: commit.date,
      relativeTime: commit.relativeTime,
      mapping,
    })
    return
  }
  if (previous.mapping !== mapping) previous.mapping = 'both'
}

function compareCommitRef(a: CommitHotspotRef, b: CommitHotspotRef): number {
  if (a.date !== b.date) return a.date > b.date ? -1 : 1
  return a.hash.localeCompare(b.hash)
}

function compareHotspotNode(a: CommitHotspotNode, b: CommitHotspotNode): number {
  if (a.commitRefs.length !== b.commitRefs.length) return b.commitRefs.length - a.commitRefs.length
  const aLatest = a.commitRefs[0]?.date ?? ''
  const bLatest = b.commitRefs[0]?.date ?? ''
  if (aLatest !== bLatest) return aLatest > bLatest ? -1 : 1
  // 活跃度相同时，非终态 WorkCase 只作为稳定的阅读顺序兜底，不覆盖提交热点本身。
  const aWorkCase = a.type === 'workcase' && a.progress_group !== 'closed'
  const bWorkCase = b.type === 'workcase' && b.progress_group !== 'closed'
  if (aWorkCase !== bWorkCase) return aWorkCase ? -1 : 1
  return factKey(a.type, a.id).localeCompare(factKey(b.type, b.id))
}

function buildCommitHotspots(
  commits: GitLogEntryWithFiles[],
  facts: CommitHotspotBuildItem[],
  governedProjectId: string,
) {
  const byKey = new Map(facts.map((item) => [factKey(item.type, item.object_id), item]))
  const byPath = new Map(facts.map((item) => [item.canonical_path, item]))
  const mappings = new Map<string, Map<string, CommitHotspotRef>>()

  for (const commit of commits) {
    const pathMatches = new Set<string>()
    for (const filePath of commit.files) {
      const item = byPath.get(filePath)
      if (item) pathMatches.add(factKey(item.type, item.object_id))
    }
    const idMatches = new Set(extractExplicitObjectIds(`${commit.message}\n${commit.body}`).filter((key) => byKey.has(key)))
    for (const key of new Set([...pathMatches, ...idMatches])) {
      const refs = mappings.get(key) ?? new Map<string, CommitHotspotRef>()
      mergeCommitMapping(refs, key, commit, pathMatches.has(key), idMatches.has(key))
      mappings.set(key, refs)
    }
  }

  const hotspots = new Set(mappings.keys())
  const edges = new Map<string, CommitHotspotEdge>()
  for (const source of facts) {
    const sourceKey = factKey(source.type, source.object_id)
    if (!Array.isArray(source.relations)) continue
    for (const relation of source.relations) {
      if (!relation || typeof relation !== 'object' || Array.isArray(relation)) continue
      const record = relation as Record<string, unknown>
      const target = record.target
      if (typeof record.relation_key !== 'string' || !target || typeof target !== 'object' || Array.isArray(target)) continue
      const targetRecord = target as Record<string, unknown>
      if (targetRecord.governed_project_id !== governedProjectId
        || typeof targetRecord.fact_type_key !== 'string'
        || typeof targetRecord.object_id !== 'string') continue
      const targetKey = factKey(targetRecord.fact_type_key, targetRecord.object_id)
      if (!byKey.has(targetKey) || (!hotspots.has(sourceKey) && !hotspots.has(targetKey))) continue
      const edge: CommitHotspotEdge = { source: sourceKey, target: targetKey, relationKey: record.relation_key }
      edges.set(`${edge.source}\u0000${edge.target}\u0000${edge.relationKey}`, edge)
    }
  }

  const edgeValues = [...edges.values()]
  const connected = new Set(edgeValues.flatMap((edge) => [edge.source, edge.target]))
  const makeNode = (key: string): CommitHotspotNode => {
    const item = byKey.get(key)
    if (!item) throw new Error(`Commit hotspot fact not found: ${key}`)
    const refs = [...(mappings.get(key)?.values() ?? [])].sort(compareCommitRef)
    return {
      type: item.type,
      id: item.object_id,
      title: item.title,
      ...(item.title_en !== undefined ? { title_en: item.title_en } : {}),
      ...(item.title_zh !== undefined ? { title_zh: item.title_zh } : {}),
      ...(item.status !== undefined ? { status: item.status } : {}),
      ...(item.progress_group !== undefined ? { progress_group: item.progress_group } : {}),
      ...(item.priority !== undefined ? { priority: item.priority } : {}),
      read_status: item.read_status,
      typeColor: getTypeColor(item.type),
      commitRefs: refs,
    }
  }

  const adjacency = new Map<string, Set<string>>()
  for (const key of connected) adjacency.set(key, new Set())
  for (const edge of edgeValues) {
    adjacency.get(edge.source)?.add(edge.target)
    adjacency.get(edge.target)?.add(edge.source)
  }

  const visited = new Set<string>()
  const clusters: Array<{ nodes: CommitHotspotNode[]; edges: CommitHotspotEdge[] }> = []
  for (const start of [...connected].sort()) {
    if (visited.has(start)) continue
    const keys: string[] = []
    const queue = [start]
    visited.add(start)
    for (let index = 0; index < queue.length; index += 1) {
      const current = queue[index]
      keys.push(current)
      for (const neighbor of adjacency.get(current) ?? []) {
        if (visited.has(neighbor)) continue
        visited.add(neighbor)
        queue.push(neighbor)
      }
    }
    const members = new Set(keys)
    clusters.push({
      nodes: keys.map(makeNode).sort(compareHotspotNode),
      edges: edgeValues.filter((edge) => members.has(edge.source) && members.has(edge.target)),
    })
  }
  clusters.sort((a, b) => {
    const aCommits = a.nodes.reduce((total, node) => total + node.commitRefs.length, 0)
    const bCommits = b.nodes.reduce((total, node) => total + node.commitRefs.length, 0)
    if (aCommits !== bCommits) return bCommits - aCommits
    const aHotspots = a.nodes.filter((node) => node.commitRefs.length > 0).length
    const bHotspots = b.nodes.filter((node) => node.commitRefs.length > 0).length
    if (aHotspots !== bHotspots) return bHotspots - aHotspots
    if (a.nodes.length !== b.nodes.length) return b.nodes.length - a.nodes.length
    return a.nodes[0]?.id.localeCompare(b.nodes[0]?.id ?? '') ?? 0
  })

  return {
    totalCommits: commits.length,
    hotspotTotal: [...hotspots].filter((key) => connected.has(key)).length,
    relationTotal: edgeValues.length,
    clusters,
  }
}

router.get('/', async (req: Request, res: Response): Promise<void> => {
  const generatedAt = new Date().toISOString()
  try {
    const locale = String(req.query.locale || 'zh')
    const recentWindow = parseRecentActivityWindow(req.query.window)
    if (recentWindow === null) {
      res.status(400).json({ ok: false, error: 'Unsupported recent activity window' })
      return
    }
    const project = await requestProject(req)
    const factScope = { worktreeLocator: project.path, governedProjectId: project.id }

    const [workCaseResult, pitfallResult, adrResult, sparkResult, studyResult] = await Promise.all([
      listObjects('workcase', undefined, undefined, factScope),
      listObjects('pitfall', undefined, undefined, factScope),
      listObjects('adr', undefined, undefined, factScope),
      listObjects('spark', undefined, undefined, factScope),
      listObjects('study', undefined, undefined, factScope),
    ])
    const issues: CognitionIssue[] = []
    let sparkHealth: ReturnType<typeof buildSparkHealth> | undefined
    if (!sparkResult.ok || !('data' in sparkResult)) {
      const message = sparkResult.ok ? 'Spark 列表读取失败' : (sparkResult as { error: string }).error
      issues.push({ section: 'sparkHealth', code: 'spark_list_unavailable', message })
    } else {
      const data = sparkResult.data as { items: Array<Record<string, unknown>>; collection_issues?: Array<Record<string, unknown>> }
      for (const issue of Array.isArray(data.collection_issues) ? data.collection_issues : []) {
        issues.push({ ...toIssue(issue), section: 'sparkHealth' })
      }
      sparkHealth = buildSparkHealth(data.items, Date.parse(generatedAt))
    }
    const builds: InboxBuildItem[] = []
    if (!workCaseResult.ok || !('data' in workCaseResult)) {
      const message = workCaseResult.ok ? 'WorkCase 列表读取失败' : (workCaseResult as { error: string }).error
      issues.push({ section: 'inbox', code: 'workcase_list_unavailable', message })
    } else {
      const data = workCaseResult.data as { items: Array<Record<string, unknown>>; collection_issues?: Array<Record<string, unknown>> }
      for (const issue of Array.isArray(data.collection_issues) ? data.collection_issues : []) issues.push(toIssue(issue))
      for (const raw of data.items) {
        const object_id = String(raw.object_id ?? '')
        const status = String(raw.status ?? 'unknown')
        const phase = typeof raw.phase === 'string' ? raw.phase : undefined
        const progressGroup = deriveWorkCaseProgressProjection(status, phase)?.progressGroup ?? null
        if (progressGroup === null) {
          issues.push({ section: 'inbox', code: 'progress_group_unresolved', message: `WorkCase ${object_id} 的进展分组无法由当前 status=${status} 派生，未收入收件箱`, object_ref: object_id })
          continue
        }
        const inboxKind = deriveInboxKind(status, phase, progressGroup)
        if (inboxKind === null) continue
        builds.push({
          type: 'workcase', inboxKind, progress_group: progressGroup,
          object_id, title: String(raw.title ?? object_id),
          ...(typeof raw.title_en === 'string' ? { title_en: raw.title_en } : {}),
          ...(typeof raw.title_zh === 'string' ? { title_zh: raw.title_zh } : {}),
          status, phase, priority: typeof raw.priority === 'string' ? raw.priority : undefined,
          updated_at: typeof raw.updated_at === 'string' ? raw.updated_at : undefined,
          read_status: String(raw.read_status ?? 'unknown'), projection: raw,
          field_issues: Array.isArray(raw.field_issues) ? (raw.field_issues as Array<Record<string, unknown>>) : [],
          unparsed_structures: Array.isArray(raw.unparsed_structures) ? (raw.unparsed_structures as Array<Record<string, unknown>>) : [],
          read_issues: Array.isArray(raw.read_issues) ? (raw.read_issues as Array<Record<string, unknown>>) : [],
        })
      }
    }

    if (!pitfallResult.ok || !('data' in pitfallResult)) {
      const message = pitfallResult.ok ? 'Pitfall 列表读取失败' : (pitfallResult as { error: string }).error
      issues.push({ section: 'inbox', code: 'pitfall_list_unavailable', message })
    } else {
      const data = pitfallResult.data as { items: Array<Record<string, unknown>>; collection_issues?: Array<Record<string, unknown>> }
      for (const issue of Array.isArray(data.collection_issues) ? data.collection_issues : []) issues.push(toIssue(issue))
      for (const raw of data.items) {
        if (raw.status !== 'draft') continue
        const object_id = String(raw.object_id ?? '')
        builds.push({
          type: 'pitfall', inboxKind: 'pitfall_confirmation', object_id, title: String(raw.title ?? object_id),
          ...(typeof raw.title_en === 'string' ? { title_en: raw.title_en } : {}),
          ...(typeof raw.title_zh === 'string' ? { title_zh: raw.title_zh } : {}),
          status: 'draft', phase: undefined,
          updated_at: typeof raw.updated_at === 'string' ? raw.updated_at : undefined,
          read_status: String(raw.read_status ?? 'unknown'), projection: raw,
          field_issues: Array.isArray(raw.field_issues) ? (raw.field_issues as Array<Record<string, unknown>>) : [],
          unparsed_structures: Array.isArray(raw.unparsed_structures) ? (raw.unparsed_structures as Array<Record<string, unknown>>) : [],
          read_issues: Array.isArray(raw.read_issues) ? (raw.read_issues as Array<Record<string, unknown>>) : [],
        })
      }
    }

    builds.sort(compareInbox)

    const recentStart = new Date(generatedAt).getTime() - RECENT_ACTIVITY_WINDOWS[recentWindow] * 24 * 60 * 60 * 1000
    const recentBuilds: RecentActivityBuildItem[] = []
    const recentSources: Array<[ObjectType, typeof workCaseResult]> = [
      ['workcase', workCaseResult],
      ['pitfall', pitfallResult],
      ['adr', adrResult],
      ['spark', sparkResult],
      ['study', studyResult],
    ]
    for (const [type, source] of recentSources) {
      if (!source.ok || !('data' in source)) {
        const message = source.ok ? `${type} 列表读取失败` : (source as { error: string }).error
        issues.push({ section: 'recentActivity', code: `${type}_list_unavailable`, message })
        continue
      }
      const sourceData = source.data as { items: Array<Record<string, unknown>>; collection_issues?: Array<Record<string, unknown>> }
      for (const issue of Array.isArray(sourceData.collection_issues) ? sourceData.collection_issues : []) {
        issues.push({ ...toIssue(issue), section: 'recentActivity' })
      }
      for (const raw of sourceData.items) {
        const createdAt = raw.created_at
        const updatedAt = raw.updated_at
        if (timestampInWindow(createdAt, recentStart, Date.parse(generatedAt))) {
          recentBuilds.push(buildRecentActivityItem(raw, type, 'created', createdAt))
        }
        if (timestampInWindow(updatedAt, recentStart, Date.parse(generatedAt)) && updatedAt !== createdAt) {
          recentBuilds.push(buildRecentActivityItem(raw, type, 'updated', updatedAt))
        }
      }
    }
    recentBuilds.sort(compareRecentActivity)

    // 模块三只读取当前正式关系与 Git 的可回指证据：不从标题、关键词或相邻文件推断关联。
    let commitHotspots: ReturnType<typeof buildCommitHotspots> | undefined
    try {
      const graphFacts: CommitHotspotBuildItem[] = []
      const workCaseFacts = await listLocalFacts('workcase', factScope)
      if (workCaseFacts.status !== 'complete') {
        issues.push({ section: 'commitHotspots', code: 'workcase_relation_list_unavailable', message: workCaseFacts.issues[0]?.message ?? 'WorkCase 正式关系读取失败' })
      } else {
        for (const item of workCaseFacts.items) {
          const projected = projectWorkCaseHotspotFact(item)
          if (projected) graphFacts.push(projected)
        }
        for (const issue of workCaseFacts.issues) {
          issues.push({ section: 'commitHotspots', code: issue.code, message: issue.message })
        }
      }

      for (const [type, source] of recentSources.filter(([type]) => type !== 'workcase')) {
        if (!source.ok || !('data' in source)) {
          const message = source.ok ? `${type} 列表读取失败` : (source as { error: string }).error
          issues.push({ section: 'commitHotspots', code: `${type}_list_unavailable`, message })
          continue
        }
        const sourceData = source.data as { items: Array<Record<string, unknown>> }
        for (const raw of sourceData.items) {
          const projected = buildCommitHotspotFact(raw, type)
          if (projected) graphFacts.push(projected)
        }
      }

      const commits = await getGitLogWithFiles(new Date(recentStart), new Date(generatedAt), locale, project.path)
      commitHotspots = buildCommitHotspots(commits, graphFacts, project.id)
    } catch (caught) {
      issues.push({
        section: 'commitHotspots',
        code: 'commit_hotspot_data_unavailable',
        message: caught instanceof Error ? caught.message : '近期提交热点数据不可用',
      })
    }

    const items = builds.map((build) => {
      const card = Object.fromEntries(
        Object.entries(build.projection).filter(([key]) => !IDENTITY_PROJECTION_KEYS.has(key)),
      )
      const entry: Record<string, unknown> = {
        type: build.type,
        id: build.object_id,
        title: build.title,
        ...(build.title_en !== undefined ? { title_en: build.title_en } : {}),
        ...(build.title_zh !== undefined ? { title_zh: build.title_zh } : {}),
        relativeTime: getRelativeTime(build.updated_at ?? '', locale),
        typeColor: getTypeColor(build.type),
        inboxKind: build.inboxKind,
        read_status: build.read_status,
        card,
      }
      if (build.type === 'workcase') entry.progress_group = build.progress_group
      else entry.status = 'draft'
      // priority 缺失/非法落 P3 之后并省略优先级信号（Q8）。
      if (priorityRank(build.priority) < 4 && typeof build.priority === 'string') entry.priority = build.priority
      // updated_at 缺失排最后并省略时间显示（Q8）。
      if (build.updated_at) entry.updatedAt = build.updated_at
      // 字段级直读 readable 时携带 canonical_path，供条件显示"复制对象路径"（Q4）。
      if (build.read_status === 'readable') entry.canonical_path = canonicalPath(build.type, build.object_id)
      if (build.field_issues.length > 0) entry.field_issues = build.field_issues
      if (build.unparsed_structures.length > 0) entry.unparsed_structures = build.unparsed_structures
      if (build.read_issues.length > 0) entry.read_issues = build.read_issues
      return entry
    })

    const recentItems = recentBuilds.map((build) => ({
      type: build.type,
      id: build.object_id,
      title: build.title,
      ...(build.title_en !== undefined ? { title_en: build.title_en } : {}),
      ...(build.title_zh !== undefined ? { title_zh: build.title_zh } : {}),
      activity: build.activity,
      occurredAt: build.occurred_at,
      relativeTime: getRelativeTime(build.occurred_at, locale),
      typeColor: getTypeColor(build.type),
      ...(build.priority !== undefined ? { priority: build.priority } : {}),
      ...(build.type === 'workcase' && build.progress_group !== undefined
        ? { progress_group: build.progress_group }
        : build.type !== 'workcase' && build.status !== undefined ? { status: build.status } : {}),
      read_status: build.read_status,
      ...(build.field_issues.length > 0 ? { field_issues: build.field_issues } : {}),
      ...(build.unparsed_structures.length > 0 ? { unparsed_structures: build.unparsed_structures } : {}),
    }))

    res.json({
      generatedAt,
      scope: { governedProjectId: project.id },
      inbox: { items, total: items.length },
      recentActivity: {
        window: recentWindow,
        windowStart: new Date(recentStart).toISOString(),
        items: recentItems,
        total: recentItems.length,
      },
      ...(commitHotspots ? {
        commitHotspots: {
          window: recentWindow,
          totalCommits: commitHotspots.totalCommits,
          hotspotTotal: commitHotspots.hotspotTotal,
          relationTotal: commitHotspots.relationTotal,
          clusters: commitHotspots.clusters,
        },
      } : {}),
      ...(sparkHealth ? {
        sparkHealth: {
          total: sparkHealth.total,
          openTotal: sparkHealth.openTotal,
          terminalTotal: sparkHealth.terminalTotal,
          terminalByStatus: sparkHealth.terminalByStatus,
          openByPriority: sparkHealth.openByPriority,
          silentThresholdDays: sparkHealth.silentThresholdDays,
          silentCount: sparkHealth.silentCount,
          silentItems: sparkHealth.silentItems.map((item) => ({
            type: 'spark',
            id: item.object_id,
            title: item.title,
            ...(item.title_en !== undefined ? { title_en: item.title_en } : {}),
            ...(item.title_zh !== undefined ? { title_zh: item.title_zh } : {}),
            ...(item.priority !== undefined ? { priority: item.priority } : {}),
            updatedAt: item.updated_at,
            silentDays: item.silent_days,
            typeColor: getTypeColor('spark'),
            read_status: item.read_status,
            ...(item.field_issues.length > 0 ? { field_issues: item.field_issues } : {}),
            ...(item.unparsed_structures.length > 0 ? { unparsed_structures: item.unparsed_structures } : {}),
          })),
        },
      } : {}),
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
