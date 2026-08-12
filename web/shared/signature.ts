export interface SignatureInput {
  productName?: unknown
  modelName?: unknown
  agentRuntimeName?: unknown
}

export interface NormalizedSignature {
  productName: string
  modelName: string
  agentRuntimeName: string
}

function normalizeModelName(value: unknown): string {
  if (typeof value !== 'string') return ''
  const trimmed = value.trim()
  if (!trimmed) return ''
  const model = trimmed.slice(trimmed.lastIndexOf('/') + 1).trim()
  return model.replace(/(?:\s*\[[^\[\]]*\]\s*)+$/, '').trim()
}

/** Product and runtime names retain their spelling after an uppercase initial. */
function normalizeProductName(value: unknown): string {
  if (typeof value !== 'string') return ''
  const trimmed = value.trim()
  if (!trimmed) return ''
  return `${trimmed.charAt(0).toUpperCase()}${trimmed.slice(1)}`
}

/** Runtime display uses only its family name before the first connector. */
function normalizeAgentRuntimeName(value: unknown): string {
  if (typeof value !== 'string') return ''
  return normalizeProductName(value.trim().split('-', 1)[0])
}

/**
 * One presentation dispatcher for all three LDVH signature fields. It never
 * infers a missing field, and makes cards, commit metadata, and aggregates
 * consume identical display identities.
 */
export function normalizeSignature(value: SignatureInput): NormalizedSignature {
  const productName = normalizeProductName(value.productName);
  const agentRuntimeName = normalizeAgentRuntimeName(value.agentRuntimeName);
  const identityKey = (name: string) => name.replace(/\s/g, '').toLocaleLowerCase();
  const sameIdentity = Boolean(
    productName
      && agentRuntimeName
      && identityKey(productName) === identityKey(agentRuntimeName),
  );

  return {
    productName,
    modelName: normalizeModelName(value.modelName),
    agentRuntimeName: sameIdentity ? '' : agentRuntimeName,
  };
}
