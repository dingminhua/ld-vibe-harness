import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { fetchObjectDetail } from '@/utils/api';
import { isObjectRef } from '@/utils/fieldFormats';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import StatusBadge from '@/components/StatusBadge';
import CopyPathButton from '@/components/CopyPathButton';
import { getObjectStatusLocale } from '@/i18n/locales';
import { usePanel } from '@/utils/panelContext';
import { ObjectTypeIcon } from '@/components/SemanticIcon';

/** 对象类型中英映射（与 ObjectDetail 页面保持一致） */
const TYPE_LOCALES: Record<string, { zh: string; en: string }> = {
  workarea: { zh: '工作域', en: 'Work Area' },
  workcase: { zh: '工作项', en: 'WorkCase' },
  adr: { zh: '决策', en: 'ADR' },
  pitfall: { zh: '踩坑', en: 'Pitfall' },
  spark: { zh: '火花', en: 'Spark' },
  study: { zh: '研究', en: 'Study' },
  change: { zh: '提交', en: 'Commit' },
};

/** 从引用 ID 解析对象类型（如 workcase-0001 → workcase） */
function parseRefType(refId: string): string | null {
  if (!isObjectRef(refId)) return null;
  const m = refId.match(/^([a-z]+)-\d+$/);
  return m ? m[1] : null;
}

interface ReferenceCardProps {
  refs: string[];
  showType?: boolean;
  showStatus?: boolean;
  showPanelIcon?: boolean;
  variant?: 'card' | 'plain';
}

export default function ReferenceCard({ refs, showType = true, showStatus = true, showPanelIcon = true, variant = 'card' }: ReferenceCardProps) {
  if (refs.length === 0) return null;

  return (
    <div className="flex flex-col gap-1.5">
      {refs.map((ref, i) => (
        <ReferenceItem key={i} refId={ref} showType={showType} showStatus={showStatus} showPanelIcon={showPanelIcon} variant={variant} />
      ))}
    </div>
  );
}

function ReferenceItem({
  refId,
  showType,
  showStatus,
  showPanelIcon,
  variant,
}: {
  refId: string;
  showType: boolean;
  showStatus: boolean;
  showPanelIcon: boolean;
  variant: 'card' | 'plain';
}) {
  const navigate = useNavigate();
  const { locale, t } = useI18n();
  const { isOpen: panelOpen, content: panelContent } = usePanel();
  const [info, setInfo] = useState<{ type: string; title: string; status: string; path: string } | null>(null);
  const [loading, setLoading] = useState(true);

  const refType = parseRefType(refId);

  useEffect(() => {
    if (!refType) { setLoading(false); return; }
    fetchObjectDetail(refType, refId)
      .then((detail) => {
        const obj = detail.data;
        const title = (locale === 'en'
          ? (obj.title_en as string || obj.title as string)
          : (obj.title_zh as string || obj.title as string)) || refId;
        setInfo({ type: refType, title, status: detail.summary.status, path: String(obj.path || detail.target || '') });
      })
      .catch(() => setInfo(null))
      .finally(() => setLoading(false));
  }, [refType, refId, locale]);

  const typeColor = refType ? (CATEGORY_COLORS[refType] || CATEGORY_COLORS.other) : CATEGORY_COLORS.other;
  const typeLabel = TYPE_LOCALES[refType || '']
    ? (locale === 'en' ? TYPE_LOCALES[refType!].en : TYPE_LOCALES[refType!].zh)
    : refType;
  const isCurrentPanelOpen = Boolean(panelOpen && refType && panelContent?.type === 'object' && panelContent.objectType === refType && panelContent.objectId === refId);
  const PanelIcon = isCurrentPanelOpen ? ChevronLeft : ChevronRight;
  const itemClassName = variant === 'plain'
    ? `ldvh-body group flex w-full items-center gap-2 rounded-md px-1.5 py-2 text-left transition-colors ${refType ? 'cursor-pointer hover:bg-ldvh-border/25' : 'cursor-default'}`
    : `ldvh-body group flex w-full items-center gap-2 rounded-lg border border-ldvh-border bg-ldvh-bg px-3 py-2 text-left transition-colors ${refType ? 'cursor-pointer hover:bg-ldvh-border/30' : 'cursor-default'}`;

  const handleClick = () => {
    if (!refType) return;
    // Emit custom event for reading panel; if preventDefault is called (desktop),
    // open the panel instead of navigating
    const event = new CustomEvent('ldvh:ref-preview', {
      detail: { refType, refId, title: info?.title || refId },
      bubbles: true,
      cancelable: true,
    });
    const notPrevented = document.dispatchEvent(event);
    if (notPrevented) {
      navigate(`/objects/${refType}/${refId}`);
    }
  };

  return (
    <div
      role={refType ? 'button' : undefined}
      tabIndex={refType ? 0 : -1}
      onClick={handleClick}
      onKeyDown={(event) => {
        if (!refType) return;
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          handleClick();
        }
      }}
      className={itemClassName}
    >
      <ObjectTypeIcon type={refType} size={13} className="shrink-0" style={{ color: typeColor }} />
      <span className="ldvh-meta shrink-0 text-ldvh-accent">{refId}</span>
      {showType && typeLabel && (
        <span
          className="ldvh-chip shrink-0 rounded px-1.5 py-0.5"
          style={{ backgroundColor: `${typeColor}20`, color: typeColor }}
        >
          {typeLabel}
        </span>
      )}
      <span className="min-w-0 flex-1 truncate text-ldvh-text-primary">
        {loading ? <span className="text-ldvh-text-secondary">{refId}</span> : (info?.title || refId)}
      </span>
      {showStatus && info?.status && (
        <span className="shrink-0">
          <StatusBadge status={info.status} statusLabel={getObjectStatusLocale(info.type, info.status, locale)} objectType={info.type} size="sm" />
        </span>
      )}
      <CopyPathButton path={info?.path} label={t('common.copyObjectPath')} copiedLabel={t('common.copiedObjectPath')} />
      {showPanelIcon && refType && (
        <PanelIcon
          size={16}
          aria-hidden="true"
          className="shrink-0 text-ldvh-text-secondary/70 transition-colors group-hover:text-ldvh-accent"
        />
      )}
    </div>
  );
}
