import type { CommitSignature } from '@/utils/api';

/**
 * Returns the newest complete attribution carried by a fact's update log.
 *
 * This intentionally reads only the immutable update-log carrier.  Header
 * attribution is therefore never inferred from the object itself or from a
 * partial signature record.
 */
export function getLatestFactChangeSignature(value: unknown): CommitSignature | undefined {
  if (!Array.isArray(value)) return undefined;

  for (let index = value.length - 1; index >= 0; index -= 1) {
    const entry = value[index];
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) continue;

    const signature = (entry as Record<string, unknown>).signature;
    if (!signature || typeof signature !== 'object' || Array.isArray(signature)) continue;
    const signatureRecord = signature as Record<string, unknown>;

    const productName = typeof signatureRecord.product_name === 'string'
      ? signatureRecord.product_name.trim()
      : '';
    const modelName = typeof signatureRecord.model_name === 'string'
      ? signatureRecord.model_name.trim()
      : '';
    const agentRuntimeName = typeof signatureRecord.agent_runtime_name === 'string'
      ? signatureRecord.agent_runtime_name.trim()
      : '';
    if (productName || modelName || agentRuntimeName) {
      return {
        ...(productName ? { productName } : {}),
        ...(modelName ? { modelName } : {}),
        ...(agentRuntimeName ? { agentRuntimeName } : {}),
      };
    }
  }

  return undefined;
}
