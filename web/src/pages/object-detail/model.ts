export const META_KEYS = [
  'id',
  'object_id',
  'type',
  'fact_type_key',
  'status',
  'created',
  'created_at',
  'updated',
  'updated_at',
  'title',
  'title_en',
  'title_zh',
  'path',
  'object_ref',
  'canonical_path',
  'absolute_path',
  'carrier',
  'coverage_status',
  'check_status',
  'read_issues',
  'fact_read_failure',
  'aggregated_related_docs',
  'aggregated_related_adrs',
  'aggregated_related_sparks',
  'aggregated_related_pitfalls',
  'aggregated_execution_refs',
];

export const COMMON_AUXILIARY_META_KEYS = ['priority', 'importance', 'tags', 'scope', 'impact', 'assignee'];
export const AUXILIARY_META_KEYS_BY_TYPE: Record<string, string[]> = {
  spark: ['priority', 'tags', 'source'],
  pitfall: ['tags'],
};

const FIELD_ORDER_BY_TYPE: Record<string, string[]> = {
  workcase: [
    'priority', 'description', 'success_criteria', 'source',
    'orchestration', 'verification_evidence', 'closure_evidence', 'related_workcases',
    'related_docs', 'related_adrs', 'related_sparks', 'related_pitfalls',
  ],
  adr: [
    'decision_question', 'decision', 'applicability', 'rationale', 'consequences',
    'urls', 'relations', 'disposition_summary',
  ],
  pitfall: [
    'symptoms', 'trigger_conditions', 'applicability', 'validation_summary', 'root_cause',
    'resolution', 'avoidance', 'urls', 'relations',
    'disposition_summary',
  ],
  spark: [
    'summary', 'evolution', 'urls', 'relations',
    'disposition_summary',
  ],
  study: [
    'research_intent', 'research_question', 'abstract', 'recommendation_summary', 'report_body',
    'urls', 'disposition_summary',
  ],
};

const RELATED_OBJECT_FIELD_ORDER: Record<string, number> = {
  related_workcases: 21,
  related_adrs: 22,
  related_pitfalls: 23,
  related_sparks: 20,
  related_studies: 24,
};

export type RelatedContentEntry = [string, unknown[]];

function normalizeRelatedFieldKey(fieldKey: string) {
  return fieldKey.startsWith('aggregated_') ? fieldKey.slice('aggregated_'.length) : fieldKey;
}

function isRelatedContentField(fieldKey: string) {
  const normalized = normalizeRelatedFieldKey(fieldKey);
  return normalized === 'urls' || normalized.startsWith('related_');
}

function hasContent(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === 'string') return value.trim().length > 0;
  return value !== null && value !== undefined;
}

export function sortRelatedContentEntries(entries: RelatedContentEntry[]) {
  return [...entries].sort((a, b) => {
    const aKey = normalizeRelatedFieldKey(a[0]);
    const bKey = normalizeRelatedFieldKey(b[0]);
    const aOrder = RELATED_OBJECT_FIELD_ORDER[aKey];
    const bOrder = RELATED_OBJECT_FIELD_ORDER[bKey];
    const aIsObject = aOrder !== undefined;
    const bIsObject = bOrder !== undefined;

    if (aIsObject && bIsObject) return aOrder - bOrder;
    if (aIsObject) return -1;
    if (bIsObject) return 1;
    return aKey.localeCompare(bKey, 'en');
  });
}

export function splitRelatedContentEntries(entries: Array<[string, unknown]>) {
  const primaryEntries: Array<[string, unknown]> = [];
  const relatedEntries: RelatedContentEntry[] = [];

  entries.forEach((entry) => {
    if (isRelatedContentField(entry[0])) {
      if (Array.isArray(entry[1]) && hasContent(entry[1])) {
        relatedEntries.push([entry[0], entry[1]]);
      }
    } else {
      primaryEntries.push(entry);
    }
  });

  return {
    primaryEntries,
    relatedEntries: sortRelatedContentEntries(relatedEntries),
  };
}

export function getObjectDetailContentEntries(obj: Record<string, unknown>, objType: string) {
  const auxiliaryMetaKeys = Array.from(new Set([...(AUXILIARY_META_KEYS_BY_TYPE[objType] || []), ...COMMON_AUXILIARY_META_KEYS]));
  const contentEntries = Object.entries(obj).filter(
    ([key]) => !META_KEYS.includes(key) && !auxiliaryMetaKeys.includes(key),
  );

  const fieldOrder = FIELD_ORDER_BY_TYPE[objType] || [];
  if (fieldOrder.length > 0) {
    contentEntries.sort((a, b) => {
      const aIdx = fieldOrder.indexOf(a[0]);
      const bIdx = fieldOrder.indexOf(b[0]);
      if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
      if (aIdx !== -1) return -1;
      if (bIdx !== -1) return 1;
      return 0;
    });
  }

  return contentEntries;
}
