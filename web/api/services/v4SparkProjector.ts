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

const STATUS_MAP: Record<string, string> = {
  open: 'pending',
  routed: 'resolved',
  discarded: 'discarded',
}

const RELATED_ALIASES: Record<string, string> = {
  workcase: 'related_workcases',
  adr: 'related_adrs',
  pitfall: 'related_pitfalls',
  spark: 'related_sparks',
  study: 'related_studies',
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function optionalArray(value: Record<string, unknown>, key: string): boolean {
  return !(key in value) || Array.isArray(value[key])
}

function targetOf(value: unknown): Record<string, unknown> | null {
  if (!isRecord(value) || !isRecord(value.target)) return null
  const target = value.target
  if (typeof target.governed_project_id !== 'string'
    || typeof target.fact_type_key !== 'string'
    || typeof target.object_id !== 'string') return null
  return target
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
    || STATUS_MAP[status] === undefined
    || typeof facts.title !== 'string'
    || typeof facts.summary !== 'string'
    || typeof facts.created_at !== 'string'
    || typeof facts.updated_at !== 'string'
    || !Array.isArray(facts.source_refs)
    || facts.source_refs.length === 0
    || typeof item.absolute_path !== 'string'
    || !optionalArray(facts, 'evidence_refs')
    || !optionalArray(facts, 'relations')
    || !optionalArray(facts, 'evolution')
    || (status === 'open'
      && (typeof facts.priority !== 'string'
        || 'disposition_summary' in facts
        || 'closed_at' in facts))
    || (status !== 'open'
      && ('priority' in facts
        || typeof facts.disposition_summary !== 'string'
        || typeof facts.closed_at !== 'string'
        || !Array.isArray(facts.evidence_refs)
        || facts.evidence_refs.length === 0))) {
    return projectionProblem(item, 'spark_projection_invalid', 'Spark fields cannot form the existing DTO')
  }

  const relations = (facts.relations ?? []) as unknown[]
  const routedRelations = relations.filter(
    (relation) => isRecord(relation) && relation.relation_key === 'routed-to',
  )
  const routedTargets = routedRelations
    .map(targetOf)
    .filter((target): target is Record<string, unknown> => target !== null)
  if (routedTargets.length !== routedRelations.length) {
    return projectionProblem(item, 'spark_projection_invalid', 'A routed-to relation has no valid target', routedTargets)
  }
  if (status === 'routed') {
    const representable = routedTargets.length === 1 && routedTargets[0].governed_project_id === projectId
    if (!representable) {
      return projectionProblem(
        item,
        'spark_projection_unrepresentable',
        'The existing single resolved_to field cannot represent every routed-to target',
        routedTargets,
      )
    }
  }

  const aliases: Record<string, string[]> = {}
  for (const relation of relations) {
    if (!isRecord(relation) || relation.relation_key !== 'related-to') continue
    const target = targetOf(relation)
    if (!target || target.governed_project_id !== projectId) continue
    const alias = RELATED_ALIASES[String(target.fact_type_key)]
    if (!alias) continue
    const refs = aliases[alias] ?? []
    refs.push(String(target.object_id))
    aliases[alias] = refs
  }

  const data: Record<string, unknown> = {
    ...facts,
    ...aliases,
    id: objectId,
    type: 'spark',
    status: STATUS_MAP[status],
    title: facts.title,
    path: item.absolute_path,
    created: facts.created_at,
    updated: facts.updated_at,
    description: facts.summary,
  }
  if (status === 'open') data.priority = facts.priority
  if (status === 'routed') {
    data.resolved_to = {
      type: routedTargets[0].fact_type_key,
      ref: routedTargets[0].object_id,
    }
    data.resolved_at = facts.closed_at
  }
  if (status === 'discarded') {
    data.discard_reason = facts.disposition_summary
  }
  for (const key of Object.keys(data)) {
    if (data[key] === undefined) delete data[key]
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
