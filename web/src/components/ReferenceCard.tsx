import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link2 } from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { fetchObjectDetail } from '@/utils/api';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import StatusBadge from '@/components/StatusBadge';

/** 对象类型中英映射（与 ObjectDetail 页面保持一致） */
const TYPE_LOCALES: Record<string, { zh: string; en: string }> = {
  intent: { zh: '意图', en: 'Intent' },
  task: { zh: '任务', en: 'Task' },
  adr: { zh: 'ADR', en: 'ADR' },
  pitfall: { zh: '踩坑', en: 'Pitfall' },
  memo: { zh: '备忘', en: 'Memo' },
  profile: { zh: '画像', en: 'Profile' },
  change: { zh: '变更', en: 'Change' },
};

/** 从引用 ID 解析对象类型（如 task-0001 → task） */
function parseRefType(refId: string): string | null {
  const m = refId.match(/^([a-z]+)-\d+$/);
  return m ? m[1] : null;
}

interface ReferenceCardProps {
  refs: string[];
}

export default function ReferenceCard({ refs }: ReferenceCardProps) {
  if (refs.length === 0) return null;

  return (
    <div className="flex flex-col gap-1.5">
      {refs.map((ref, i) => (
        <ReferenceItem key={i} refId={ref} />
      ))}
    </div>
  );
}

function ReferenceItem({ refId }: { refId: string }) {
  const navigate = useNavigate();
  const { locale, getStatus } = useI18n();
  const [info, setInfo] = useState<{ title: string; status: string } | null>(null);
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
        setInfo({ title, status: detail.summary.status });
      })
      .catch(() => setInfo(null))
      .finally(() => setLoading(false));
  }, [refType, refId, locale]);

  const typeColor = refType ? (CATEGORY_COLORS[refType] || CATEGORY_COLORS.other) : CATEGORY_COLORS.other;
  const typeLabel = TYPE_LOCALES[refType || '']
    ? (locale === 'en' ? TYPE_LOCALES[refType!].en : TYPE_LOCALES[refType!].zh)
    : refType;

  const handleClick = () => {
    if (!refType) return;
    // Emit custom event for reading panel; if preventDefault is called (desktop),
    // open the panel instead of navigating
    const event = new CustomEvent('ldvh:ref-preview', {
      detail: { refType, refId },
      bubbles: true,
      cancelable: true,
    });
    const notPrevented = document.dispatchEvent(event);
    if (notPrevented) {
      navigate(`/objects/${refType}/${refId}`);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={!refType}
      className="flex w-full items-center gap-2 rounded-lg border border-ldvh-border bg-ldvh-bg px-3 py-2 text-left text-sm transition-colors hover:bg-ldvh-border/30 disabled:cursor-default"
    >
      <Link2 size={13} className="shrink-0" style={{ color: typeColor }} />
      <span className="shrink-0 font-mono text-xs text-ldvh-accent">{refId}</span>
      {typeLabel && (
        <span
          className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium"
          style={{ backgroundColor: `${typeColor}20`, color: typeColor }}
        >
          {typeLabel}
        </span>
      )}
      <span className="min-w-0 flex-1 truncate text-ldvh-text-primary">
        {loading ? <span className="text-ldvh-text-secondary">{refId}</span> : (info?.title || refId)}
      </span>
      {info?.status && (
        <span className="shrink-0">
          <StatusBadge status={info.status} statusLabel={getStatus(info.status)} size="sm" />
        </span>
      )}
    </button>
  );
}
