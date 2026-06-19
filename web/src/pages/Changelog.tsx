import { useEffect, useState } from 'react';
import { GitCommit, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { fetchChangelog, fetchCommitDetail, type ChangelogEntry } from '@/utils/api';
import { useI18n } from '@/i18n/context';
import PageHeader from '@/components/PageHeader';
import { formatDateTime } from '@/utils/dateFormat';
import { usePanel } from '@/utils/panelContext';

export default function Changelog() {
  const { locale, t } = useI18n();
  const { openPanel } = usePanel();
  const [entries, setEntries] = useState<ChangelogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedHash, setExpandedHash] = useState<string | null>(null);
  const [commitDetail, setCommitDetail] = useState<string | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    fetchChangelog(50, locale)
      .then(setEntries)
      .catch((e) => setError(e.message));
  }, [locale]);

  const handleToggle = async (entry: ChangelogEntry) => {
    const hash = entry.hash;
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
      openPanel({
        type: 'diff',
        title: `${entry.shortHash} ${entry.description}`,
        data: detail.stat,
      });
    } catch {
      setCommitDetail(t('changelog.detailFailed'));
    } finally {
      setLoadingDetail(false);
    }
  };

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="ldvh-body-muted">{t('changelog.loadFailed')}</p>
          <p className="ldvh-meta text-red-400">{error}</p>
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
    <div className="ldvh-page-frame">
      <PageHeader title={t('changelog.title')} subtitle={t('changelog.subtitle')} />

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
                onClick={() => handleToggle(entry)}
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
                    <span className="ldvh-meta text-ldvh-accent">
                      {entry.shortHash}
                    </span>
                    <span className="ldvh-body truncate">
                      {entry.message}
                    </span>
                  </div>
                  <div className="ldvh-caption mt-1 flex items-center gap-3">
                    <span>{entry.author}</span>
                    <span>{formatDateTime(entry.date)}</span>
                  </div>
                </div>
                <GitCommit size={14} className="mt-1 flex-shrink-0 text-ldvh-text-secondary" />
              </button>

              {isExpanded && (
                <div className="border-t border-ldvh-border px-4 py-3">
                  {loadingDetail ? (
                    <div className="flex items-center gap-2">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
                      <span className="ldvh-caption">{t('common.loading')}</span>
                    </div>
                  ) : (
                    <pre className="ldvh-meta overflow-x-auto whitespace-pre-wrap">
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
