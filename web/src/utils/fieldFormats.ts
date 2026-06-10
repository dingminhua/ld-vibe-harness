/** Fields whose string content is Markdown-capable Narrative / Decision / Log. */
export const SUMMARY_TEXT_FIELDS = [
  'description', 'source', 'context', 'consequences', 'success_criteria', 'constraints',
  'rationale', 'observation', 'analysis', 'mitigation', 'resolution', 'decision',
  'symptoms', 'trigger_conditions', 'root_cause', 'avoidance', 'applicability',
  'governance_scope', 'archive_reason', 'notes', 'transition_reasons',
  'risk_assessment', 'status_history', 'alternatives', 'reason',
  'scope', 'impact', 'summary', 'details', 'outcome', 'next_steps',
  'lessons', 'background', 'motivation',
];

/** Markdown fields that should switch to ChecklistCard when the value is a GFM task list. */
export const CHECKLIST_COMPAT_FIELDS = [
  'success_criteria', 'constraints', 'verification', 'risk_assessment',
  'trigger_conditions', 'avoidance', 'next_steps',
];

/** Evidence fields use the EvidenceBlock renderer. */
export const EVIDENCE_FIELDS = ['closure_evidence', 'verification', 'completion_evidence', 'evidence'];

/** Object ID reference fields render through ReferenceCard when values look like LDVH object IDs. */
export const REFERENCE_FIELDS = [
  'blocked_by', 'source_intent', 'parent_task', 'sub_tasks', 'related_intents',
  'related_tasks', 'related_adrs', 'related_memos', 'related_pitfalls',
  'related_profiles', 'source_tasks', 'source_memos', 'source_objects',
  'related_objects', 'superseded_by', 'resolved_to',
];

/** Path / URL reference fields render through DocPreviewLink when values are previewable paths. */
export const DOC_LINK_FIELDS = [
  'related_docs', 'deliverables', 'affected_docs', 'related_rules', 'affects',
  'superseded_by',
];

export const PATH_TEXT_FIELDS = ['project_path', 'ldvh_base_path', 'docs_path', 'rules_path', 'skills_path'];

/** Fields that can be folded in detail view. */
export const COLLAPSIBLE_FIELDS = [
  'related_intents', 'related_tasks', 'related_docs', 'related_adrs', 'related_memos',
  'related_pitfalls', 'related_profiles', 'deliverables', 'affected_docs', 'related_rules',
  'source_tasks', 'source_memos', 'blocked_by',
];

export function isPreviewableDocPath(value: string) {
  return value.startsWith('http://') || value.startsWith('https://') || /^(docs\/|specs\/|web\/docs\/|rules\/|skills\/|tools\/|web\/)/.test(value);
}

export function hasChecklist(value: string) {
  return /^\s*- \[[ xX]\]/m.test(value);
}

export function isObjectRef(refId: string) {
  const match = refId.match(/^([a-z]+)-\d+$/);
  if (!match) return false;
  return ['intent', 'task', 'adr', 'pitfall', 'memo', 'profile'].includes(match[1]);
}
