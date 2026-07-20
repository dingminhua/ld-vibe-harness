/** V4-only fact reader for Human-facing Web views. */

import {
  V4FactsTransportError,
} from '../internal/v4FactsTransport.js'
import { V4FactsConfigurationError } from './v4FactsConfig.js'
// create-spark 写入路径（captureV4Spark，见 routes/sparks.ts）保持不变；
// 列表/详情读取已切换为本地直读，不再调用 listV4Sparks/readV4Spark。
import { listLocalFacts, readLocalFact, type LocalFactItem, type LocalFactScope } from './localFactReader.js'
import { getWorkCaseDisplayStatus } from '../../shared/workcaseStatus.js'

export const ACTIVE_OBJECT_TYPES = ['workcase', 'adr', 'pitfall', 'spark', 'study'] as const
export const OBJECT_TYPES = ACTIVE_OBJECT_TYPES
export type ObjectType = (typeof OBJECT_TYPES)[number]

type SourceRef = { path: string; role: string }

export interface WebFactResult {
  ok: true
  command: string
  action: string
  target: string
  summary: Record<string, unknown>
  issues: Array<Record<string, unknown>>
  data: Record<string, unknown>
}

export interface WebFactError {
  ok: false
  error: string
  stderr: string
  exitCode: number | string | null
}

function result(action: string, target: string, data: Record<string, unknown>): WebFactResult {
  return {
    ok: true,
    command: 'v4-web-facts',
    action,
    target,
    summary: { count: Array.isArray(data.items) ? data.items.length : undefined, source_refs: data.source_refs ?? [] },
    issues: [],
    data,
  }
}

function error(value: unknown): WebFactError {
  if (value instanceof V4FactsTransportError) {
    return { ok: false, error: value.message, stderr: value.diagnostic, exitCode: value.code }
  }
  return { ok: false, error: value instanceof Error ? value.message : 'V4 facts unavailable', stderr: '', exitCode: 1 }
}

/** item-02：目录缺失表示该类型尚未接入；返回非空诊断项，避免与“已接入但暂无数据”混淆。 */
function notIntegrated(type: ObjectType, message: string): WebFactResult {
  const listed = result('list', type, {
    items: [{
      id: `type-not-integrated-${type}`,
      type,
      status: 'type_not_integrated',
      title: message,
      path: `ldvh-base/${type}`,
      updated: '',
      kind: 'type_not_integrated',
      message,
    }],
    source_refs: [],
    coverage_status: 'type_not_integrated',
  })
  listed.issues = [{ code: 'type_not_integrated', message }]
  listed.summary.coverage_status = 'type_not_integrated'
  return listed
}

/** 与 v4SparkProjector 输出一致的扁平 DTO：fact_object 字段 + 传输元数据。 */
function projectItem(item: LocalFactItem): Record<string, unknown> {
  return {
    ...item.fact_object,
    object_ref: item.object_ref,
    canonical_path: item.canonical_path,
    absolute_path: item.absolute_path,
  }
}

export async function listObjects(type: ObjectType, _baseDir?: string, status?: string, scope?: LocalFactScope): Promise<WebFactResult | WebFactError> {
  try {
    const listed = await listLocalFacts(type, scope)
    if (listed.status !== 'complete') {
      const message = listed.issues[0]?.message ?? `类型 ${type} 尚无对象目录`
      return notIntegrated(type, message)
    }
    const projectionProblems: Array<Record<string, unknown>> = listed.items
      .filter((item) => item.issues.length > 0)
      .map((item) => ({
        code: 'local_read_issue',
        error: item.issues.map((issue) => issue.message).join('；'),
        object_ref: item.object_ref,
        targets: [],
      }))
    projectionProblems.push(...listed.issues.map((issue) => ({
      code: issue.code,
      error: issue.message,
      canonical_path: issue.path,
      targets: [],
    })))
    const items = listed.items
      .map(projectItem)
      .filter((item) => !status || item.status === status)
    const sourceRefs = items.flatMap((item) => Array.isArray(item.source_refs) ? item.source_refs : []) as SourceRef[]
    const response = result('list', type, {
      items,
      source_refs: sourceRefs,
      coverage_status: listed.status,
      projection_problems: projectionProblems,
    })
    response.issues = [
      ...listed.issues.map((issue) => ({ ...issue }) as Record<string, unknown>),
      ...listed.items.flatMap((item) => item.issues.map((issue) => ({ ...issue }) as Record<string, unknown>)),
    ]
    return response
  } catch (caught) {
    return error(caught)
  }
}

const OBJECT_ID_PATTERN = /^(workcase|adr|pitfall|spark|study)-\d+$/

export async function showObject(id: string, scope?: LocalFactScope): Promise<WebFactResult | WebFactError> {
  const match = OBJECT_ID_PATTERN.exec(id)
  if (!match) {
    return { ok: false, error: `Object not found: ${id}`, stderr: '', exitCode: 1 }
  }
  const type = match[1] as ObjectType
  try {
    const detail = await readLocalFact(type, id, scope)
    if (detail.status === 'not_found') return { ok: false, error: `Object not found: ${id}`, stderr: '', exitCode: 1 }
    if (detail.status === 'type_not_integrated') {
      return {
        ok: false,
        error: detail.issues[0]?.message ?? `Object not found: ${id}`,
        stderr: '',
        exitCode: 'type_not_integrated',
      }
    }
    if (detail.status === 'unavailable') {
      return {
        ok: false,
        error: detail.issues[0]?.message ?? `Object unavailable: ${id}`,
        stderr: '',
        exitCode: 'unexpected_fact_carrier',
      }
    }
    const data: Record<string, unknown> = {
      ...projectItem(detail.item),
      source_refs: Array.isArray(detail.item.fact_object.source_refs) ? detail.item.fact_object.source_refs : [],
      coverage_status: 'complete',
      check_status: detail.item.check_status,
      read_issues: detail.item.issues,
    }
    const response = {
      ...result('show', id, data),
      summary: {
        id: typeof data.object_id === 'string' ? data.object_id : id,
        type: typeof data.fact_type_key === 'string' ? data.fact_type_key : type,
        status: type === 'workcase'
          ? getWorkCaseDisplayStatus(
              typeof data.phase === 'string' ? data.phase : '',
              typeof data.status === 'string' ? data.status : 'unknown',
            )
          : typeof data.status === 'string' ? data.status : 'unknown',
      },
    }
    response.issues = detail.item.issues.map((issue) => ({ ...issue }) as Record<string, unknown>)
    return response
  } catch (caught) {
    return error(caught)
  }
}

/** Non-Spark V4 readers are intentionally absent in this increment: no V2/V3 fallback or compatibility read is allowed. */
export function readFactData(_filePath: string): Record<string, unknown> {
  return {}
}

export { V4FactsConfigurationError }
