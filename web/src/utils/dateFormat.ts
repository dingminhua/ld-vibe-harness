function pad2(value: number): string {
  return String(value).padStart(2, '0');
}

/** Format app timestamps as a single absolute UI convention: YYYY-MM-DD HH:mm. */
export function formatDateTime(value?: string | null): string {
  if (!value) return '-';

  const raw = String(value).trim();
  if (!raw || raw === '-') return '-';

  const normalized = raw.replace(' ', 'T');
  const isoLike = normalized.match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?)?/);
  if (isoLike) {
    const [, year, month, day, hour = '00', minute = '00'] = isoLike;
    return `${year}-${month}-${day} ${hour}:${minute}`;
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;

  return [
    date.getFullYear(),
    pad2(date.getMonth() + 1),
    pad2(date.getDate()),
  ].join('-') + ` ${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}
