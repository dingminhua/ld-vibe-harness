/** Human/AI communication reference: friendly short UID projection, with an explicit legacy fallback. */
export function formatObjectReference(
  projectId: string | undefined,
  objectId: string | undefined,
  objectType?: string,
  shortRef?: string,
): string | undefined {
  const typeCode = { adr: 'A', workcase: 'C', pitfall: 'P', spark: 'S', study: 'T' }[objectType ?? ''];
  if (typeCode && shortRef?.startsWith(typeCode) && /^[ACPST][A-Z]{5}$/.test(shortRef)) {
    return projectId ? `${projectId}@${shortRef}` : shortRef;
  }
  if (!projectId || !objectId) return undefined;
  return `${projectId}@${objectId}`;
}
