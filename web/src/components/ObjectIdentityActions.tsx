import type { ReactNode } from 'react';
import CopyPathButton from '@/components/CopyPathButton';
import StatusBadge from '@/components/StatusBadge';

/**
 * The identity-row action cluster shared by fact cards, full details, and
 * secondary reading. Keeping the status badge and copy affordance in one
 * component prevents each surface from drifting in visual spacing.
 */
export default function ObjectIdentityActions({
  status,
  statusLabel,
  objectType,
  target,
  actionBadges,
  copyLabel,
  copiedLabel,
  showCopyAction = true,
}: {
  status?: string;
  statusLabel?: string;
  objectType?: string;
  target?: string;
  actionBadges?: ReactNode;
  copyLabel?: string;
  copiedLabel?: string;
  showCopyAction?: boolean;
}) {
  if (!status && !actionBadges && !showCopyAction) return null;

  return (
    <div className="flex h-7 shrink-0 items-center gap-1">
      {status && (
        <StatusBadge
          status={status}
          statusLabel={statusLabel}
          objectType={objectType}
        />
      )}
      {actionBadges}
      {showCopyAction && (
        <CopyPathButton path={target} label={copyLabel} copiedLabel={copiedLabel} />
      )}
    </div>
  );
}
