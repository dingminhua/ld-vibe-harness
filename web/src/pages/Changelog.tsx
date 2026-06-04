import { useEffect, useState } from 'react';
import { GitCommit, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { fetchChangelog, fetchCommitDetail, type ChangelogEntry } from '@/utils/api';
import { useI18n } from '@/i18n/context';

export default function Changelog() {
  const { locale, t } = useI18n();
  const [entries, setEntries] = useState<ChangelogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedHash, setExpandedHash] = useState<string | null>(null);
  const [commitDetail, setCommitDetail] = useState<string | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    fetchChangelog(50)
      .then(setEntries)
      .catch((e) => setError(e.message));
  }, []);

  const handleToggle = async (hash: string) => {
    if (expandedHash === hash) {
      setExpandedHash(null);
      setCommitDetail(null);
      return;
    }

    setExpandedHash(hash);
    setCommitDetail(null);
    setLoadingDetail(true);

    try {
      const detail = await fetchCommitDetail(hash);
      setCommitDetail(detail.stat);
    } catch {
      setCommitDetail(t('changelog.detailFailed'));
    } finally {
      setLoadingDetail(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleString(locale === 'zh' ? 'zh-CN' : 'en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="text-ldvh-text-secondary">{t('changelog.loadFailed')}</p>
          <p className="font-mono text-xs text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-ldvh-text-primary">{t('changelog.title')}</h1>
        <p className="mt-1 text-sm text-ldvh-text-secondary">
          {t('changelog.subtitle')}
        </p>
      </div>

      <div className="flex flex-col gap-1">
        {entries.map((entry) => {
          const isExpanded = expandedHash === entry.hash;
          return (
            <div
              key={entry.hash}
              className="rounded-lg border border-ldvh-border bg-ldvh-panel transition-colors"
            >
              <button
                className="flex w-full items-start gap-3 px-4 py-3 text-left"
                onClick={() => handleToggle(entry.hash)}
              >
                <span className="mt-0.5 flex-shrink-0 text-ldvh-text-secondary">
                  {isExpanded ? (
                    <ChevronDown size={16} />
                  ) : (
                    <ChevronRight size={16} />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-ldvh-accent">
                      {entry.shortHash}
                    </span>
                    <span className="truncate text-sm text-ldvh-text-primary">
                      {entry.message}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-ldvh-text-secondary">
                    <span>{entry.author}</span>
                    <span>{formatDate(entry.date)}</span>
                  </div>
                </div>
                <GitCommit size={14} className="mt-1 flex-shrink-0 text-ldvh-text-secondary" />
              </button>

              {isExpanded && (
                <div className="border-t border-ldvh-border px-4 py-3">
                  {loadingDetail ? (
                    <div className="flex items-center gap-2">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
                      <span className="text-xs text-ldvh-text-secondary">{t('common.loading')}</span>
                    </div>
                  ) : (
                    <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-relaxed text-ldvh-text-secondary">
                      {commitDetail}
                    </pre>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
