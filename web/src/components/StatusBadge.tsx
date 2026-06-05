import { useTheme } from '@/hooks/useTheme';
import { getStatusColor } from '@/utils/statusColors';
import { getStatusHint } from '@/i18n/locales';
import { useI18n } from '@/i18n/context';

interface StatusBadgeProps {
  status: string;
  statusLabel?: string;  // Localized display text
  size?: 'sm' | 'md';
}

export default function StatusBadge({ status, statusLabel, size = 'sm' }: StatusBadgeProps) {
  const { resolved } = useTheme();
  const { locale } = useI18n();
  const color = getStatusColor(status);
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1';
  const display = statusLabel || status;
  const tooltip = getStatusHint(status, locale);

  return (
    <span
      key={resolved}
      className={`inline-flex items-center whitespace-nowrap rounded-full font-mono font-medium ${sizeClasses}`}
      style={{
        color,
        backgroundColor: `${color}18`,
        border: `1px solid ${color}30`,
      }}
      title={tooltip || undefined}
    >
      {display}
    </span>
  );
}
