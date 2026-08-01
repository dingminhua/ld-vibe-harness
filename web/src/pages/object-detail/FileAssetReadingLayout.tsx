import { useState } from 'react';
import { ChevronRight, FileSearch2 } from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { getFieldLabel, getFieldValueLabel } from '@/i18n/locales';
import {
  ReadingNodeSection,
  getReadingNodeNextState,
  type ReadingNodeState,
} from '@/pages/ObjectDetail';
import { formatDateTime } from '@/utils/dateFormat';
import { usePanel } from '@/utils/panelContext';

type FileAssetReadingLayoutProps = {
  obj: Record<string, unknown>;
  locale: string;
};

export function FileAssetReadingLayout({ obj, locale }: FileAssetReadingLayoutProps) {
  const { t } = useI18n();
  const { openPanel } = usePanel();
  const signature = asRecord(obj.signature);
  const recovery = asRecord(obj.recovery);
  const isDeleted = obj.status === 'deleted';
  const objectId = stringValue(obj.object_id);

  const openPreview = () => {
    if (!objectId || isDeleted) return;
    openPanel({
      type: 'file-preview',
      objectId,
      title: stringValue(obj.title) || stringValue(obj.filename) || objectId,
      data: {
        filename: stringValue(obj.filename),
        mediaType: stringValue(obj.media_type),
      },
    });
  };

  return (
    <div className="mb-6 flex flex-col gap-5">
      {!isDeleted && (
        <FileAssetSection title={t('objectDetail.fileContent')} locale={locale}>
          <div
            role="button"
            tabIndex={0}
            onClick={openPreview}
            onKeyDown={(event) => {
              if (event.key !== 'Enter' && event.key !== ' ') return;
              event.preventDefault();
              openPreview();
            }}
            title={t('objectDetail.openReadingPanel')}
            className="ldvh-body group flex min-h-10 w-full cursor-pointer items-center gap-2 rounded-md px-1.5 py-2 text-left transition-colors hover:bg-ldvh-border/25 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ldvh-accent/50"
          >
            <FileSearch2 size={13} className="shrink-0 text-ldvh-accent" />
            <span className="ldvh-meta-primary min-w-0 flex-1 truncate">{stringValue(obj.filename)}</span>
            <ChevronRight size={14} className="shrink-0 text-ldvh-text-secondary/70" />
          </div>
        </FileAssetSection>
      )}

      <FileAssetSection title={t('objectDetail.fileInformation')} locale={locale}>
        <MetadataGroup>
          <MetadataItem label={getFieldLabel('filename', locale)} value={stringValue(obj.filename)} />
          <MetadataItem label={getFieldLabel('media_type', locale)} value={stringValue(obj.media_type)} />
          <MetadataItem label={getFieldLabel('size_bytes', locale)} value={formatFileSize(obj.size_bytes, locale)} />
        </MetadataGroup>
      </FileAssetSection>

      <FileAssetSection title={t('objectDetail.contentIdentity')} locale={locale}>
        <MetadataGroup>
          <MetadataItem
            label={getFieldLabel('content_sha256', locale)}
            value={stringValue(obj.content_sha256)}
            hideLabel
            breakAll
          />
        </MetadataGroup>
      </FileAssetSection>

      <FileAssetSection title={getFieldLabel('signature', locale)} locale={locale}>
        <MetadataGroup>
          <MetadataItem
            label={getFieldLabel('signer_type', locale)}
            value={getFieldValueLabel('signer_type', stringValue(signature?.signer_type), locale)}
          />
          {signature?.agent_id !== undefined && (
            <MetadataItem label={getFieldLabel('agent_id', locale)} value={stringValue(signature.agent_id)} />
          )}
          {signature?.host_environment !== undefined && (
            <MetadataItem label={getFieldLabel('host_environment', locale)} value={stringValue(signature.host_environment)} />
          )}
        </MetadataGroup>
      </FileAssetSection>

      {isDeleted && (
        <FileAssetSection title={t('objectDetail.deletionRecord')} locale={locale}>
          <MetadataGroup>
            <MetadataItem
              label={getFieldLabel('deleted_at', locale)}
              value={formatDateTime(stringValue(obj.deleted_at)) || '—'}
            />
            {typeof obj.disposition_summary === 'string' && (
              <MetadataItem label={getFieldLabel('disposition_summary', locale)} value={obj.disposition_summary} />
            )}
          </MetadataGroup>
          {recovery && (
            <MetadataGroup separated>
              <MetadataItem label={getFieldLabel('commit', locale)} value={stringValue(recovery.commit)} breakAll />
              <MetadataItem label={getFieldLabel('path', locale)} value={stringValue(recovery.path)} breakAll />
              <MetadataItem label={getFieldLabel('blob_oid', locale)} value={stringValue(recovery.blob_oid)} breakAll />
            </MetadataGroup>
          )}
        </FileAssetSection>
      )}
    </div>
  );
}

function FileAssetSection({
  title,
  locale,
  children,
}: {
  title: string;
  locale: string;
  children: React.ReactNode;
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');

  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      {children}
    </ReadingNodeSection>
  );
}

function MetadataGroup({ children, separated = false }: { children: React.ReactNode; separated?: boolean }) {
  return (
    <div className={separated ? 'mt-3 border-t border-ldvh-border pt-3' : ''}>
      <dl className="ldvh-study-node-content grid min-w-0 grid-cols-[repeat(auto-fit,minmax(min(100%,14rem),1fr))] gap-x-6 gap-y-4">
        {children}
      </dl>
    </div>
  );
}

function MetadataItem({
  label,
  value,
  hideLabel = false,
  breakAll = false,
}: {
  label: string;
  value: string;
  hideLabel?: boolean;
  breakAll?: boolean;
}) {
  return (
    <div className="min-w-0">
      <dt className={hideLabel ? 'sr-only' : 'ldvh-caption-strong text-ldvh-text-secondary/80'}>{label}</dt>
      <dd
        aria-label={hideLabel ? label : undefined}
        className={`ldvh-detail-semantic-body ${hideLabel ? '' : 'mt-0.5'} !text-ldvh-text-primary/90 ${breakAll ? 'break-all' : 'break-words'}`}
      >
        {value || '—'}
      </dd>
    </div>
  );
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
  return value as Record<string, unknown>;
}

function stringValue(value: unknown): string {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  return '';
}

function formatFileSize(value: unknown, locale: string): string {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) return '—';
  const exact = new Intl.NumberFormat(locale === 'en' ? 'en-US' : 'zh-CN').format(value);
  if (value < 1024) return locale === 'en' ? `${exact} bytes` : `${exact} 字节`;

  const units = ['KB', 'MB', 'GB', 'TB'];
  let display = value / 1024;
  let unit = units[0];
  for (let index = 1; index < units.length && display >= 1024; index += 1) {
    display /= 1024;
    unit = units[index];
  }
  const compact = new Intl.NumberFormat(locale === 'en' ? 'en-US' : 'zh-CN', { maximumFractionDigits: 1 }).format(display);
  return `${compact} ${unit} · ${locale === 'en' ? `${exact} bytes` : `${exact} 字节`}`;
}
