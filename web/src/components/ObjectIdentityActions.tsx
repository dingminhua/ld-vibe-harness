import type { ReactNode } from 'react';
import CopyPathButton from '@/components/CopyPathButton';
import ObjectReferenceCopyButton from '@/components/ObjectReferenceCopyButton';
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
  statusLeadingBadges,
  actionBadges,
  copyLabel,
  copiedLabel,
  shortRef,
  showCopyAction = true,
  compact = false,
}: {
  status?: string;
  statusLabel?: string;
  objectType?: string;
  target?: string;
  statusLeadingBadges?: ReactNode;
  actionBadges?: ReactNode;
  copyLabel?: string;
  copiedLabel?: string;
  shortRef?: string;
  showCopyAction?: boolean;
  compact?: boolean;
}) {
  if (!statusLeadingBadges && !status && !actionBadges && !showCopyAction) return null;

  return (
    <div className={`flex ${compact ? 'h-[18px]' : 'h-7'} shrink-0 items-center gap-1`}>
      {statusLeadingBadges}
      {status && (
        <StatusBadge
          status={status}
          statusLabel={statusLabel}
          objectType={objectType}
          size={compact ? 'xs' : undefined}
          variant={compact ? 'compact' : undefined}
        />
      )}
      {actionBadges}
      {showCopyAction && (objectType === 'workcase' || objectType === 'adr' || objectType === 'pitfall' || objectType === 'spark' || objectType === 'study') && (
        <ObjectReferenceCopyButton objectId={target} objectType={objectType} shortRef={shortRef} label={copyLabel} copiedLabel={copiedLabel} />
      )}
      {showCopyAction && objectType !== 'workcase' && objectType !== 'adr' && objectType !== 'pitfall' && objectType !== 'spark' && objectType !== 'study' && (
        <CopyPathButton path={target} label={copyLabel} copiedLabel={copiedLabel} />
      )}
    </div>
  );
}
