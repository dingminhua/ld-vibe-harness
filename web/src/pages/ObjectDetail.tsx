import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ChevronDown, ChevronRight } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import { fetchObjectDetail, type ObjectDetail } from '@/utils/api';
import { useI18n } from '@/i18n/context';

export default function ObjectDetail() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showYaml, setShowYaml] = useState(false);
  const { t, getStatus, locale } = useI18n();

  useEffect(() => {
    if (!type || !id) return;
    fetchObjectDetail(type, id)
      .then(setDetail)
      .catch((e) => setError(e.message));
  }, [type, id]);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-ldvh-text-secondary">{t('common.loadFailed')}</p>
          <p className="font-mono text-xs text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  const obj = detail.data;
  const objId = detail.summary.id;
  const objType = detail.summary.type;
  const objStatus = detail.summary.status;

  const displayTitle = (locale === 'en'
    ? ((obj.title_en as string) || obj.title as string)
    : ((obj.title_zh as string) || obj.title as string)) || objId;

  // Fields to show in metadata grid
  const metaKeys = ['id', 'type', 'status', 'created', 'updated', 'closed_at'];
  // Remaining fields for content section
  const contentEntries = Object.entries(obj).filter(
    ([key]) => !metaKeys.includes(key)
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <button
          onClick={() => navigate(`/objects/${type}`)}
          className="flex items-center gap-1 rounded-md px-2 py-1 text-sm text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
        >
          <ArrowLeft size={16} />
          {t('objectDetail.back')}
        </button>
        <h1 className="text-lg font-semibold text-ldvh-text-primary">
          {displayTitle}
        </h1>
      </div>

      {/* Metadata grid */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-3">
          <p className="mb-1 text-xs text-ldvh-text-secondary">{t('objectDetail.id')}</p>
          <p className="font-mono text-sm text-ldvh-text-primary">{objId}</p>
        </div>
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-3">
          <p className="mb-1 text-xs text-ldvh-text-secondary">{t('objectDetail.type')}</p>
          <p className="font-mono text-sm text-ldvh-text-primary">{objType}</p>
        </div>
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-3">
          <p className="mb-1 text-xs text-ldvh-text-secondary">{t('objectDetail.status')}</p>
          <StatusBadge status={objStatus} statusLabel={getStatus(objStatus)} size="md" />
        </div>
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-3">
          <p className="mb-1 text-xs text-ldvh-text-secondary">{t('objectDetail.created')}</p>
          <p className="font-mono text-sm text-ldvh-text-primary">{obj.created as string || '-'}</p>
        </div>
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-3">
          <p className="mb-1 text-xs text-ldvh-text-secondary">{t('objectDetail.updated')}</p>
          <p className="font-mono text-sm text-ldvh-text-primary">{obj.updated as string || '-'}</p>
        </div>
      </div>

      {/* Content fields */}
      <div className="mb-6 rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
        <h3 className="mb-4 text-sm font-medium text-ldvh-text-primary">{t('objectDetail.content')}</h3>
        <div className="flex flex-col gap-4">
          {contentEntries.map(([key, value]) => (
            <div key={key}>
              <p className="mb-1 font-mono text-xs text-ldvh-text-secondary">{key}</p>
              <FieldValue value={value} />
            </div>
          ))}
        </div>
      </div>

      {/* YAML source */}
      <div className="rounded-lg border border-ldvh-border bg-ldvh-panel">
        <button
          onClick={() => setShowYaml(!showYaml)}
          className="flex w-full items-center justify-between p-4 text-sm text-ldvh-text-secondary transition-colors hover:text-ldvh-text-primary"
        >
          <span className="font-mono">{t('objectDetail.yamlSource')}</span>
          {showYaml ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
        {showYaml && (
          <div className="border-t border-ldvh-border p-4">
            <pre className="max-h-96 overflow-auto font-mono text-xs text-ldvh-text-secondary">
              {JSON.stringify(obj, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

function FieldValue({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    return <span className="font-mono text-xs text-ldvh-text-secondary italic">null</span>;
  }

  if (typeof value === 'string') {
    if (value.includes('\n') || value.length > 120) {
      return (
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-md bg-ldvh-bg p-3 font-mono text-sm text-ldvh-text-primary">
          {value}
        </pre>
      );
    }
    return <span className="text-sm text-ldvh-text-primary">{value}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="font-mono text-xs text-ldvh-text-secondary italic">empty</span>;
    }
    if (typeof value[0] === 'string') {
      return (
        <ul className="flex flex-col gap-1 pl-4">
          {value.map((item, i) => (
            <li key={i} className="text-sm text-ldvh-text-primary">
              <span className="mr-2 text-ldvh-text-secondary">•</span>
              {item}
            </li>
          ))}
        </ul>
      );
    }
    return (
      <ul className="flex flex-col gap-2 pl-4">
        {value.map((item, i) => (
          <li key={i} className="rounded-md bg-ldvh-bg p-2">
            <FieldValue value={item} />
          </li>
        ))}
      </ul>
    );
  }

  if (typeof value === 'object') {
    return (
      <div className="rounded-md bg-ldvh-bg p-3">
        {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
          <div key={k} className="mb-1 last:mb-0">
            <span className="font-mono text-xs text-ldvh-text-secondary">{k}: </span>
            <FieldValue value={v} />
          </div>
        ))}
      </div>
    );
  }

  return <span className="font-mono text-sm text-ldvh-text-primary">{String(value)}</span>;
}
