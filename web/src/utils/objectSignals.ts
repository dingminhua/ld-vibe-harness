import { getFieldLabel, getFieldValueLabel } from '../i18n/locales.ts';

type SignalField = 'priority' | 'importance' | 'category';

export type ObjectSignalSource = Partial<Record<SignalField, unknown>>;
export type SignalObjectType = 'workcase' | 'adr' | 'pitfall' | 'spark' | 'study' | 'change' | string;

export const SIGNAL_FIELDS: SignalField[] = ['priority', 'importance', 'category'];

const SIGNAL_FIELDS_BY_TYPE: Record<string, SignalField[]> = {
  workcase: ['priority'],
  spark: ['priority'],
};

const SIGNAL_CLASSES: Partial<Record<SignalField, Record<string, string>>> = {
  priority: {
    P0: 'border-rose-500/20 bg-transparent text-rose-300/90 font-medium',
    P1: 'border-orange-500/20 bg-transparent text-orange-300/90 font-medium',
    P2: 'border-amber-500/20 bg-transparent text-amber-300/90 font-medium',
    P3: 'border-zinc-500/20 bg-transparent text-ldvh-text-secondary font-medium',
  },
  importance: {
    high: 'border-transparent bg-transparent text-ldvh-text-secondary',
    medium: 'border-transparent bg-transparent text-ldvh-text-tertiary',
    low: 'border-transparent bg-transparent text-ldvh-text-tertiary',
  },
  category: {
    gap: 'border-red-500/30 bg-red-500/10 text-red-500',
    question: 'border-sky-500/30 bg-sky-500/10 text-sky-500',
    discovery: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500',
    reminder: 'border-violet-500/30 bg-violet-500/10 text-violet-500',
    preference: 'border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-500',
  },
};

const SIGNAL_DOT_CLASSES: Partial<Record<SignalField, Record<string, string>>> = {
  importance: {
    high: 'bg-orange-300/80',
    medium: 'bg-sky-300/70',
    low: 'bg-zinc-400/70',
  },
};

const ACCENT_COLORS: Partial<Record<SignalField, Record<string, string>>> = {
  priority: {
    P0: '#ef4444',
    P1: '#f97316',
  },
  importance: {
    high: '#f97316',
    medium: '#f59e0b',
  },
  category: {
    gap: '#ef4444',
  },
};

const PRIORITY_ICON_CLASSES: Record<string, string> = {
  P0: 'border-rose-400/45 bg-rose-500/10 text-rose-400',
  P1: 'border-orange-400/45 bg-orange-500/10 text-orange-400',
  P2: 'border-amber-400/45 bg-amber-500/10 text-amber-400',
  P3: 'border-zinc-400/35 bg-zinc-500/10 text-zinc-400',
};

function normalizeSignalValue(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  const normalized = String(value).trim();
  return normalized || null;
}

export function isSignalField(field: string): field is SignalField {
  return SIGNAL_FIELDS.includes(field as SignalField);
}

export function getSignalFieldLabel(field: string, locale: string): string | null {
  if (!isSignalField(field)) return null;
  return getFieldLabel(field, locale);
}

export function getSignalText(field: string, value: unknown, locale: string): string | null {
  if (!isSignalField(field)) return null;
  const normalized = normalizeSignalValue(value);
  if (!normalized) return null;
  const localized = getFieldValueLabel(field, normalized, locale);
  return localized === normalized ? normalized.replace(/_/g, ' ') : localized;
}

export function getObjectPriority(source: ObjectSignalSource, type?: SignalObjectType): string | null {
  if (type !== 'workcase' && type !== 'spark') return null;
  return normalizeSignalValue(source.priority);
}

export function getPriorityLabel(value: unknown, locale: string): string | null {
  const normalized = normalizeSignalValue(value);
  if (!normalized) return null;
  const fieldLabel = getFieldLabel('priority', locale);
  const valueLabel = getFieldValueLabel('priority', normalized, locale);
  return `${fieldLabel}: ${valueLabel}`;
}

export function getPriorityIconClassName(value: unknown): string {
  const normalized = normalizeSignalValue(value);
  if (!normalized) return 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary';
  return PRIORITY_ICON_CLASSES[normalized] ?? 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary';
}

export function getSignalClassName(field: string, value: unknown): string {
  if (!isSignalField(field)) return 'border-ldvh-border bg-ldvh-bg text-ldvh-text-primary';
  const normalized = normalizeSignalValue(value);
  if (!normalized) return 'border-ldvh-border bg-ldvh-bg text-ldvh-text-primary';
  return SIGNAL_CLASSES[field]?.[normalized] ?? 'border-ldvh-border bg-ldvh-bg text-ldvh-text-primary';
}

export function getSignalDotClassName(field: string, value: unknown): string | null {
  if (!isSignalField(field)) return null;
  const normalized = normalizeSignalValue(value);
  if (!normalized) return null;
  return SIGNAL_DOT_CLASSES[field]?.[normalized] ?? null;
}

function getAllowedSignalFields(type?: SignalObjectType): SignalField[] {
  if (!type) return SIGNAL_FIELDS;
  return SIGNAL_FIELDS_BY_TYPE[type] ?? [];
}

export function getObjectSignalAccent(source: ObjectSignalSource, type?: SignalObjectType): string | null {
  for (const field of getAllowedSignalFields(type)) {
    const normalized = normalizeSignalValue(source[field]);
    if (!normalized) continue;
    const color = ACCENT_COLORS[field]?.[normalized];
    if (color) return color;
  }
  return null;
}

export function getObjectSignals(source: ObjectSignalSource, type?: SignalObjectType) {
  return getAllowedSignalFields(type)
    .map((field) => ({ field, value: normalizeSignalValue(source[field]) }))
    .filter((signal): signal is { field: SignalField; value: string } => Boolean(signal.value));
}
