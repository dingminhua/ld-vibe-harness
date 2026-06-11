type SignalField = 'priority' | 'severity' | 'repeatability' | 'category';

export type ObjectSignalSource = Partial<Record<SignalField, unknown>>;

export const SIGNAL_FIELDS: SignalField[] = ['priority', 'severity', 'repeatability', 'category'];

const FIELD_LABELS: Record<SignalField, { zh: string; en: string }> = {
  priority: { zh: '优先级', en: 'Priority' },
  severity: { zh: '严重程度', en: 'Severity' },
  repeatability: { zh: '复现概率', en: 'Repeatability' },
  category: { zh: '分类', en: 'Category' },
};

const VALUE_LABELS: Partial<Record<SignalField, Record<string, { zh: string; en: string }>>> = {
  priority: {
    high: { zh: '高优先级', en: 'High priority' },
    medium: { zh: '中优先级', en: 'Medium priority' },
    low: { zh: '低优先级', en: 'Low priority' },
  },
  severity: {
    critical: { zh: '严重', en: 'Critical' },
    high: { zh: '高严重度', en: 'High severity' },
    medium: { zh: '中严重度', en: 'Medium severity' },
    low: { zh: '低严重度', en: 'Low severity' },
  },
  repeatability: {
    recurring: { zh: '反复出现', en: 'Recurring' },
    occasional: { zh: '偶发', en: 'Occasional' },
    one_off: { zh: '一次性', en: 'One-off' },
    once: { zh: '一次性', en: 'Once' },
    unknown: { zh: '未知', en: 'Unknown' },
  },
  category: {
    gap: { zh: '缺口', en: 'Gap' },
    question: { zh: '问题', en: 'Question' },
    discovery: { zh: '发现', en: 'Discovery' },
    reminder: { zh: '提醒', en: 'Reminder' },
    preference: { zh: '偏好', en: 'Preference' },
  },
};

const SIGNAL_CLASSES: Partial<Record<SignalField, Record<string, string>>> = {
  priority: {
    high: 'border-red-500/35 bg-red-500/10 text-red-500',
    medium: 'border-amber-500/35 bg-amber-500/10 text-amber-500',
    low: 'border-zinc-500/25 bg-zinc-500/10 text-ldvh-text-secondary',
  },
  severity: {
    critical: 'border-red-500/40 bg-red-500/10 text-red-500',
    high: 'border-orange-500/40 bg-orange-500/10 text-orange-500',
    medium: 'border-amber-500/35 bg-amber-500/10 text-amber-500',
    low: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500',
  },
  repeatability: {
    recurring: 'border-amber-500/35 bg-amber-500/10 text-amber-500',
    occasional: 'border-sky-500/30 bg-sky-500/10 text-sky-500',
    one_off: 'border-zinc-500/25 bg-zinc-500/10 text-ldvh-text-secondary',
    once: 'border-zinc-500/25 bg-zinc-500/10 text-ldvh-text-secondary',
    unknown: 'border-zinc-500/25 bg-zinc-500/10 text-ldvh-text-secondary',
  },
  category: {
    gap: 'border-red-500/30 bg-red-500/10 text-red-500',
    question: 'border-sky-500/30 bg-sky-500/10 text-sky-500',
    discovery: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500',
    reminder: 'border-violet-500/30 bg-violet-500/10 text-violet-500',
    preference: 'border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-500',
  },
};

const ACCENT_COLORS: Partial<Record<SignalField, Record<string, string>>> = {
  priority: {
    high: '#ef4444',
    medium: '#f59e0b',
  },
  severity: {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#f59e0b',
  },
  category: {
    gap: '#ef4444',
  },
};

function normalizeSignalValue(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  const normalized = String(value).trim();
  return normalized || null;
}

function localize(entry: { zh: string; en: string }, locale: string): string {
  return locale === 'en' ? entry.en : entry.zh;
}

export function isSignalField(field: string): field is SignalField {
  return SIGNAL_FIELDS.includes(field as SignalField);
}

export function getSignalFieldLabel(field: string, locale: string): string | null {
  if (!isSignalField(field)) return null;
  return localize(FIELD_LABELS[field], locale);
}

export function getSignalText(field: string, value: unknown, locale: string): string | null {
  if (!isSignalField(field)) return null;
  const normalized = normalizeSignalValue(value);
  if (!normalized) return null;
  const entry = VALUE_LABELS[field]?.[normalized];
  return entry ? localize(entry, locale) : normalized.replace(/_/g, ' ');
}

export function getSignalClassName(field: string, value: unknown): string {
  if (!isSignalField(field)) return 'border-ldvh-border bg-ldvh-bg text-ldvh-text-primary';
  const normalized = normalizeSignalValue(value);
  if (!normalized) return 'border-ldvh-border bg-ldvh-bg text-ldvh-text-primary';
  return SIGNAL_CLASSES[field]?.[normalized] ?? 'border-ldvh-border bg-ldvh-bg text-ldvh-text-primary';
}

export function getObjectSignalAccent(source: ObjectSignalSource): string | null {
  for (const field of SIGNAL_FIELDS) {
    const normalized = normalizeSignalValue(source[field]);
    if (!normalized) continue;
    const color = ACCENT_COLORS[field]?.[normalized];
    if (color) return color;
  }
  return null;
}

export function getObjectSignals(source: ObjectSignalSource) {
  return SIGNAL_FIELDS
    .map((field) => ({ field, value: normalizeSignalValue(source[field]) }))
    .filter((signal): signal is { field: SignalField; value: string } => Boolean(signal.value));
}
