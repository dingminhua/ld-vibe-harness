/**
 * The fact carrier may prefix a model with its hosting product, such as
 * `chatgpt/gpt-5.6-terra`. Web display consumes the model identity only.
 */
export function normalizeModelName(value: unknown): string {
  if (typeof value !== 'string') return ''
  const trimmed = value.trim()
  if (!trimmed) return ''
  return trimmed.slice(trimmed.lastIndexOf('/') + 1).trim()
}

/** Product and runtime names retain their spelling after an uppercase initial. */
export function normalizeSignatureName(value: unknown): string {
  if (typeof value !== 'string') return ''
  const trimmed = value.trim()
  if (!trimmed) return ''
  return `${trimmed.charAt(0).toUpperCase()}${trimmed.slice(1)}`
}

/** Runtime display uses only its family name before the first connector. */
export function normalizeRuntimeName(value: unknown): string {
  if (typeof value !== 'string') return ''
  return normalizeSignatureName(value.trim().split('-', 1)[0])
}
