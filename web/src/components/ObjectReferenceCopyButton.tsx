import CopyPathButton from '@/components/CopyPathButton';
import { useI18n } from '@/i18n/context';
import { useProjectScope } from '@/utils/projectContext';

/** Stable cross-surface fact identity; never expose a source-file path as an object copy value. */
export function formatObjectReference(projectId: string | undefined, objectId: string | undefined): string | undefined {
  if (!projectId || !objectId) return undefined;
  return `${projectId}@${objectId}`;
}

export default function ObjectReferenceCopyButton({
  objectId,
  projectId,
  className,
  label,
  copiedLabel,
}: {
  objectId?: string;
  projectId?: string;
  className?: string;
  label?: string;
  copiedLabel?: string;
}) {
  const { selectedProjectId } = useProjectScope();
  const { t } = useI18n();
  const reference = formatObjectReference(projectId ?? selectedProjectId, objectId);

  return <CopyPathButton
    path={reference}
    className={className}
    label={label ?? t('common.copyObjectId')}
    copiedLabel={copiedLabel ?? t('common.copiedObjectId')}
  />;
}
