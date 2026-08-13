import CopyPathButton from '@/components/CopyPathButton';
import { useI18n } from '@/i18n/context';
import { formatObjectReference } from '@/utils/objectReference';
import { useProjectScope } from '@/utils/projectContext';

export default function ObjectReferenceCopyButton({
  objectId,
  projectId,
  className,
  label,
  copiedLabel,
  objectType,
  shortRef,
}: {
  objectId?: string;
  projectId?: string;
  className?: string;
  label?: string;
  copiedLabel?: string;
  objectType?: string;
  shortRef?: string;
}) {
  const { selectedProjectId } = useProjectScope();
  const { t } = useI18n();
  const reference = formatObjectReference(projectId ?? selectedProjectId, objectId, objectType, shortRef);

  return <CopyPathButton
    path={reference}
    className={className}
    label={label ?? t('common.copyObjectId')}
    copiedLabel={copiedLabel ?? t('common.copiedObjectId')}
  />;
}
