function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

export function hasUnavailableIndependentSubagentReview(source: unknown): boolean {
  if (!isRecord(source)) return false;
  if (source.independentSubagentUnavailable === true) return true;
  const authorization = source.execution_authorization;
  if (!isRecord(authorization) || !Array.isArray(authorization.capability_limitations)) return false;
  return authorization.capability_limitations.some((limitation) => (
    isRecord(limitation)
    && limitation.capability === 'independent-subagent-review'
    && limitation.availability === 'unavailable'
  ));
}
