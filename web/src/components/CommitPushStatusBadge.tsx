import { useI18n } from '@/i18n/context';
import type { GitPushStatus } from '@/utils/api';

export default function CommitPushStatusBadge({
  status,
  className = '',
}: {
  status: GitPushStatus;
  className?: string;
}) {
  const { t } = useI18n();

  if (status === 'unknown') return null;

  const isPushed = status === 'pushed';
  return (
    <span
      className={`${className} inline-flex shrink-0 items-center rounded-md border px-2 py-0.5 text-[10px] font-medium leading-4 ${
        isPushed
          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
          : 'border-amber-500/35 bg-amber-500/10 text-amber-700 dark:text-amber-300'
      }`}
    >
      {t(isPushed ? 'changelog.pushed' : 'changelog.unpushed')}
    </span>
  );
}
