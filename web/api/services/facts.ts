/** V4-only fact reader for Human-facing Web views. */

import {
  V4FactsTransportError,
} from '../internal/v4FactsTransport.js'
import { v4SparkReaderConfig, V4FactsConfigurationError } from './v4FactsConfig.js'
import { listV4Sparks, readV4Spark } from './v4SparkReader.js'
import { projectV4Spark, projectV4SparkList } from './v4SparkProjector.js'

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

function empty(type: ObjectType): WebFactResult {
  return result('list', type, { items: [], source_refs: [] })
}

export async function listObjects(type: ObjectType, _baseDir?: string, status?: string): Promise<WebFactResult | WebFactError> {
  if (type !== 'spark') return empty(type)
  try {
    const response = await listV4Sparks(v4SparkReaderConfig())
    if (!response.result || typeof response.result !== 'object' || Array.isArray(response.result)) {
      return error(new Error('V4 Spark list result is unavailable'))
    }
    const raw = response.result as Record<string, unknown>
    const projection = projectV4SparkList(raw.items)
    const items = projection.items.filter((item) => !status || item.status === status)
    const sourceRefs = items.flatMap((item) => Array.isArray(item.source_refs) ? item.source_refs : []) as SourceRef[]
    return result('list', type, {
      items,
      source_refs: sourceRefs,
      coverage_status: raw.status,
      projection_problems: projection.projection_problems,
      governance_resolution: raw.governance_resolution,
    })
  } catch (caught) {
    return error(caught)
  }
}

export async function showObject(id: string): Promise<WebFactResult | WebFactError> {
  if (!/^spark-\d+$/.test(id)) {
    return { ok: false, error: `Object not found: ${id}`, stderr: '', exitCode: 1 }
  }
  try {
    const response = await readV4Spark(v4SparkReaderConfig(), id)
    if (!response.result || typeof response.result !== 'object' || Array.isArray(response.result)) {
      return error(new Error('V4 Spark detail result is unavailable'))
    }
    const raw = response.result as Record<string, unknown>
    if (raw.status === 'not_found') return { ok: false, error: `Object not found: ${id}`, stderr: '', exitCode: 1 }
    const projection = projectV4Spark(raw.item)
    if (projection.ok === false) return { ok: false, error: projection.error, stderr: projection.code, exitCode: 1 }
    const data: Record<string, unknown> = {
      ...projection.data,
      source_refs: projection.data.source_refs ?? [],
      coverage_status: raw.coverage_status,
      governance_resolution: raw.governance_resolution,
    }
    return {
      ...result('show', id, data),
      summary: {
        id: typeof data.object_id === 'string' ? data.object_id : id,
        type: typeof data.fact_type_key === 'string' ? data.fact_type_key : 'spark',
        status: typeof data.status === 'string' ? data.status : 'unknown',
      },
    }
  } catch (caught) {
    return error(caught)
  }
}

/** Non-Spark V4 readers are intentionally absent in this increment: no V2/V3 fallback or compatibility read is allowed. */
export function readFactData(_filePath: string): Record<string, unknown> {
  return {}
}

export { V4FactsConfigurationError }
