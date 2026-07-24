export type FactCarrier = 'yaml' | 'markdown';
export type FactReadStatus = 'readable' | 'invalid' | 'not_found' | 'unavailable';

export type FactReadIssue = {
  code?: string;
  message?: string;
  path?: string;
};

export type FactReadMeta = {
  canonicalPath?: string;
  carrier?: FactCarrier;
  checkStatus?: FactReadStatus;
  issues: FactReadIssue[];
  isFailure: boolean;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function asCarrier(value: unknown): FactCarrier | undefined {
  return value === 'yaml' || value === 'markdown' ? value : undefined;
}

function asReadStatus(value: unknown): FactReadStatus | undefined {
  return value === 'readable' || value === 'invalid' || value === 'not_found' || value === 'unavailable'
    ? value
    : undefined;
}

function asIssues(value: unknown): FactReadIssue[] {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord).map((issue) => ({
    code: typeof issue.code === 'string' ? issue.code : undefined,
    message: typeof issue.message === 'string' ? issue.message : undefined,
    path: typeof issue.path === 'string' ? issue.path : undefined,
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
    issues: asIssues(value?.read_issues),
    isFailure: value?.fact_read_failure === true,
  };
}

export function isReadableFact(meta: FactReadMeta): meta is FactReadMeta & {
  canonicalPath: string;
  carrier: FactCarrier;
  checkStatus: 'readable';
} {
  return !meta.isFailure
    && meta.checkStatus === 'readable'
    && typeof meta.canonicalPath === 'string'
    && meta.carrier !== undefined;
}
