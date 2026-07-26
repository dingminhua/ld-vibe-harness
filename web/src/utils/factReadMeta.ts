import { dump as dumpYaml } from 'js-yaml';

export type FactCarrier = 'yaml' | 'markdown';
export type FactReadStatus = 'readable' | 'mechanically_valid' | 'invalid' | 'not_found' | 'unavailable';

export type FactReadIssue = {
  category: string;
  fieldPath: string | null;
  summary: string;
};

export type FactReadMeta = {
  canonicalPath?: string;
  carrier?: FactCarrier;
  checkStatus?: FactReadStatus;
  observedAt?: string;
  issues: FactReadIssue[];
  isFailure: boolean;
};

const EXACT_READ_METADATA_FIELDS = new Set([
  'fact_read_failure',
  'object_ref',
  'canonical_path',
  'absolute_path',
  'carrier',
  'check_status',
  'content_fingerprint',
  'coverage_status',
  'observed_at',
  'read_issues',
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function asCarrier(value: unknown): FactCarrier | undefined {
  return value === 'yaml' || value === 'markdown' ? value : undefined;
}

function asReadStatus(value: unknown): FactReadStatus | undefined {
  return value === 'readable'
    || value === 'mechanically_valid'
    || value === 'invalid'
    || value === 'not_found'
    || value === 'unavailable'
    ? value
    : undefined;
}

function asIssues(value: unknown): FactReadIssue[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter(isRecord)
    .filter((issue) => typeof issue.category === 'string' && typeof issue.summary === 'string')
    .map((issue) => ({
      category: issue.category as string,
      fieldPath: typeof issue.field_path === 'string' ? issue.field_path : null,
      summary: issue.summary as string,
    }));
}

/** Source metadata is accepted only from an exact fact-detail payload, never from a route target or object ID. */
export function getFactReadMeta(value: Record<string, unknown> | undefined): FactReadMeta {
  const checkStatus = asReadStatus(value?.check_status);
  return {
    canonicalPath: typeof value?.canonical_path === 'string' && value.canonical_path.length > 0
      ? value.canonical_path
      : undefined,
    carrier: asCarrier(value?.carrier),
    checkStatus,
    observedAt: typeof value?.observed_at === 'string' && value.observed_at.length > 0
      ? value.observed_at
      : undefined,
    issues: asIssues(value?.read_issues),
    isFailure: value?.fact_read_failure === true,
  };
}

export function isReadableFact(meta: FactReadMeta): meta is FactReadMeta & {
  canonicalPath: string;
  carrier: FactCarrier;
  checkStatus: 'readable' | 'mechanically_valid';
} {
  return !meta.isFailure
    && (meta.checkStatus === 'readable' || meta.checkStatus === 'mechanically_valid')
    && typeof meta.canonicalPath === 'string'
    && meta.carrier !== undefined;
}

/** Strip the exact-read envelope before rendering reconstructed carrier data. */
export function projectFactObjectFields(value: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(value).filter(([field]) => !EXACT_READ_METADATA_FIELDS.has(field)),
  );
}

/** Reconstruct readable YAML data without changing scalar types or exposing the exact-read envelope. */
export function reconstructFactYaml(value: Record<string, unknown>): string {
  return dumpYaml(projectFactObjectFields(value), {
    noRefs: true,
    lineWidth: -1,
    sortKeys: false,
  });
}
