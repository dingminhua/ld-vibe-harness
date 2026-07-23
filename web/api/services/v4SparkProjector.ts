export interface V4SparkProjectionProblem {
  code: 'spark_projection_invalid' | 'spark_projection_unrepresentable'
  error: string
  object_ref: Record<string, unknown> | null
  targets: Array<Record<string, unknown>>
}

export type V4SparkProjection =
  | { ok: true; data: Record<string, unknown> }
  | ({ ok: false } & V4SparkProjectionProblem)

export interface V4SparkListProjection {
  ok: boolean
  status: 'complete' | 'partial'
  items: Array<Record<string, unknown>>
  projection_problems: V4SparkProjectionProblem[]
}

function isProjectionProblem(
  value: V4SparkProjection,
): value is { ok: false } & V4SparkProjectionProblem {
  return !value.ok
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function optionalArray(value: Record<string, unknown>, key: string): boolean {
  return !(key in value) || Array.isArray(value[key])
}

function projectionProblem(
  item: unknown,
  code: V4SparkProjectionProblem['code'],
  error: string,
  targets: Array<Record<string, unknown>> = [],
): V4SparkProjection {
  return {
    ok: false,
    code,
    error,
    object_ref: isRecord(item) && isRecord(item.object_ref) ? item.object_ref : null,
    targets,
  }
}

export function projectV4Spark(item: unknown): V4SparkProjection {
  if (!isRecord(item) || item.check_status !== 'mechanically_valid' || !isRecord(item.fact_object)) {
    return projectionProblem(item, 'spark_projection_invalid', 'Spark item is not mechanically valid')
  }
  const facts = item.fact_object
  const objectRef = isRecord(item.object_ref) ? item.object_ref : null
  const projectId = objectRef?.governed_project_id
  const objectId = facts.object_id
  const status = facts.status
  if (typeof projectId !== 'string'
    || objectRef?.fact_type_key !== 'spark'
    || objectRef?.object_id !== objectId
    || typeof objectId !== 'string'
    || facts.fact_type_key !== 'spark'
    || typeof status !== 'string'
    || !['open', 'routed', 'discarded'].includes(status)
    || typeof facts.title !== 'string'
    || typeof facts.summary !== 'string'
    || typeof facts.created_at !== 'string'
    || typeof facts.updated_at !== 'string'
    || typeof item.absolute_path !== 'string'
    || !optionalArray(facts, 'urls')
    || !optionalArray(facts, 'relations')
    || !optionalArray(facts, 'evolution')
    || (status === 'open'
      && (typeof facts.priority !== 'string'
        || 'disposition_summary' in facts
        || 'closed_at' in facts))
    || (status !== 'open'
      && ('priority' in facts
        || typeof facts.disposition_summary !== 'string'
        || typeof facts.closed_at !== 'string'))) {
    return projectionProblem(item, 'spark_projection_invalid', 'Spark fields cannot form the existing DTO')
  }

  const data: Record<string, unknown> = {
    ...facts,
    object_ref: objectRef,
    canonical_path: item.canonical_path,
    absolute_path: item.absolute_path,
  }
  return { ok: true, data }
}

export function projectV4SparkList(items: unknown): V4SparkListProjection {
  if (!Array.isArray(items)) {
    return {
      ok: false,
      status: 'partial',
      items: [],
      projection_problems: [{
        code: 'spark_projection_invalid',
        error: 'Spark list is not an array',
        object_ref: null,
        targets: [],
      }],
    }
  }
  const projected = items.map(projectV4Spark)
  const successful = projected.filter((item): item is { ok: true; data: Record<string, unknown> } => item.ok)
  const problems = projected.filter(isProjectionProblem).map((item) => ({
    code: item.code,
    error: item.error,
    object_ref: item.object_ref,
    targets: item.targets,
  }))
  return {
    ok: problems.length === 0,
    status: problems.length === 0 ? 'complete' : 'partial',
    items: successful.map((item) => item.data),
    projection_problems: problems,
  }
}
