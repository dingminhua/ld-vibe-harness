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

    const modelId = typeof signatureRecord.model_id === 'string'
      ? signatureRecord.model_id.trim()
      : '';
    const hostName = typeof signatureRecord.agent_workbench === 'string'
      ? signatureRecord.agent_workbench.trim()
      : typeof signatureRecord.host_name === 'string'
        ? signatureRecord.host_name.trim()
        : '';
    if (modelId && hostName) return { modelId, hostName };

    const agentId = typeof signatureRecord.agent_id === 'string'
      ? signatureRecord.agent_id.trim()
      : '';
    const hostEnvironment = typeof signatureRecord.host_environment === 'string'
      ? signatureRecord.host_environment.trim()
      : '';

    if (agentId && hostEnvironment) return { agentId, hostEnvironment };
  }

  return undefined;
}
