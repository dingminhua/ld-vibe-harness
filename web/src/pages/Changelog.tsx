import { useEffect, useMemo, useState, type KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import CopyPathButton from '@/components/CopyPathButton';
import CommitBreakingBadge from '@/components/CommitBreakingBadge';
import CommitPushStatusBadge from '@/components/CommitPushStatusBadge';
import CommitSignatureMeta from '@/components/CommitSignatureMeta';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { fetchChangelog, fetchCommitDetail, type ChangelogEntry } from '@/utils/api';
import { getCommitScopeLabel, getCommitTypeLabel } from '@/utils/commitLabels';
import { useI18n } from '@/i18n/context';
import { formatDateTime } from '@/utils/dateFormat';
import { usePanel } from '@/utils/panelContext';
import { CATEGORY_COLORS } from '@/utils/categoryColors';

const CHANGELOG_COUNT_OPTIONS = [50, 100, 200] as const;
type ChangelogCount = typeof CHANGELOG_COUNT_OPTIONS[number];
const COMMIT_COPY_BODY_PREVIEW_LIMIT = 180;

function getCommitFilterOptions(entries: ChangelogEntry[], field: 'category' | 'scope'): string[] {
  return [...new Set(entries.map((entry) => entry[field]).filter((value): value is string => Boolean(value)))]
    .sort((a, b) => a.localeCompare(b));
}

function CommitFilterGroup({
  allLabel,
  options,
  activeValue,
  onChange,
  getLabel,
}: {
  allLabel: string;
  options: string[];
  activeValue: string | null;
  onChange: (value: string | null) => void;
  getLabel: (value: string) => string;
}) {
  return (
    <div className="ldvh-tab-list min-w-0">
      <button
        type="button"
        onClick={() => onChange(null)}
        className={`ldvh-tab-button ${activeValue === null ? 'ldvh-tab-button-active' : 'ldvh-tab-button-idle'}`}
      >
        {allLabel}
      </button>
      {options.map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={`ldvh-tab-button ${activeValue === option ? 'ldvh-tab-button-active' : 'ldvh-tab-button-idle'}`}
        >
          {getLabel(option)}
        </button>
      ))}
    </div>
  );
}

function CommitCountGroup({
  activeValue,
  onChange,
  labelForCount,
}: {
  activeValue: ChangelogCount;
  onChange: (value: ChangelogCount) => void;
  labelForCount: (value: ChangelogCount) => string;
}) {
  return (
    <div className="ldvh-tab-list min-w-0">
      {CHANGELOG_COUNT_OPTIONS.map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={`ldvh-tab-button ${activeValue === option ? 'ldvh-tab-button-active' : 'ldvh-tab-button-idle'}`}
        >
          {labelForCount(option)}
        </button>
      ))}
    </div>
  );
}

function getCommitCopyContext(entry: ChangelogEntry): string {
  const body = entry.body?.trim() ?? '';
  const bodyPreview = body.length > COMMIT_COPY_BODY_PREVIEW_LIMIT
    ? `${body.slice(0, COMMIT_COPY_BODY_PREVIEW_LIMIT).trimEnd()}\n[truncated; fetch full body/stat by hash]`
    : body;

  return [
    'LDVH Commit',
    `hash: ${entry.hash}`,
    `type: ${entry.category || '-'}`,
    `scope: ${entry.scope || '-'}`,
    `description: ${entry.description || entry.message || '-'}`,
    `detail: /changelog/${entry.hash}`,
    ...(bodyPreview ? [`body:\n${bodyPreview}`] : []),
  ].join('\n');
}

export default function Changelog() {
  const { locale, t } = useI18n();
  const { isOpen: panelOpen, content: panelContent, openPanel, closePanel } = usePanel();
  const navigate = useNavigate();
  const [entries, setEntries] = useState<ChangelogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedHash, setSelectedHash] = useState<string | null>(null);
  const [loadingHash, setLoadingHash] = useState<string | null>(null);
  const [activeType, setActiveType] = useState<string | null>(null);
  const [activeScope, setActiveScope] = useState<string | null>(null);
  const [logCount, setLogCount] = useState<ChangelogCount>(50);

  const typeOptions = useMemo(
    () => getCommitFilterOptions(entries, 'category')
      .sort((a, b) => getCommitTypeLabel(a, locale).localeCompare(getCommitTypeLabel(b, locale))),
    [entries, locale],
  );
  const scopeOptions = useMemo(
    () => getCommitFilterOptions(entries, 'scope')
      .sort((a, b) => getCommitScopeLabel(a, locale).localeCompare(getCommitScopeLabel(b, locale))),
    [entries, locale],
  );
  const filteredEntries = useMemo(() => entries.filter((entry) => {
    if (activeType && entry.category !== activeType) return false;
    if (activeScope && entry.scope !== activeScope) return false;
    return true;
  }), [activeScope, activeType, entries]);

  useEffect(() => {
    let cancelled = false;
    setEntries([]);
    setError(null);

    fetchChangelog(logCount, locale)
      .then((result) => {
        if (!cancelled) setEntries(result);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });

    return () => {
      cancelled = true;
    };
  }, [locale, logCount]);

  const handleSelectCommit = async (entry: ChangelogEntry) => {
    const hash = entry.hash;
    const panelTitle = `${entry.description || entry.message}`;
    if (panelOpen && panelContent?.type === 'diff' && selectedHash === hash) {
      closePanel();
      setSelectedHash(null);
      return;
    }

    setSelectedHash(hash);
    setLoadingHash(hash);

    try {
      const detail = await fetchCommitDetail(hash, locale);
      const detailEntry = detail.entry ?? { ...entry, body: detail.body || entry.body };
      openPanel({
        type: 'diff',
        title: panelTitle,
        data: { entry: detailEntry, stat: detail.stat },
      });
    } catch {
      openPanel({
        type: 'diff',
        title: panelTitle,
        data: t('changelog.detailFailed'),
      });
    } finally {
      setLoadingHash(null);
    }
  };

  const openCommitPage = (entry: ChangelogEntry) => {
    closePanel();
    setSelectedHash(null);
    navigate(`/changelog/${entry.hash}`);
  };

  const handleKeyboardOpen = (event: KeyboardEvent<HTMLDivElement>, open: () => void) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open();
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
      <div className="sticky top-0 z-20 -mx-6 -mt-6 mb-4 flex flex-col gap-2 border-b border-ldvh-border bg-ldvh-bg/95 px-6 py-3 backdrop-blur">
        <CommitCountGroup
          activeValue={logCount}
          onChange={(value) => {
            setLogCount(value);
            setSelectedHash(null);
          }}
          labelForCount={(value) => t('changelog.recentCount', { count: String(value) })}
        />
        <CommitFilterGroup
          allLabel={t('changelog.allTypes')}
          options={typeOptions}
          activeValue={activeType}
          onChange={(value) => {
            setActiveType(value);
            setSelectedHash(null);
          }}
          getLabel={(value) => getCommitTypeLabel(value, locale)}
        />
        <CommitFilterGroup
          allLabel={t('changelog.allScopes')}
          options={scopeOptions}
          activeValue={activeScope}
          onChange={(value) => {
            setActiveScope(value);
            setSelectedHash(null);
          }}
          getLabel={(value) => getCommitScopeLabel(value, locale)}
        />
      </div>

      <div className="ldvh-section-grid">
        {filteredEntries.length === 0 ? (
          <div className="rounded-lg border border-dashed border-ldvh-border bg-ldvh-panel px-4 py-8 text-center">
            <p className="ldvh-body-muted">{t('changelog.noMatches')}</p>
          </div>
        ) : filteredEntries.map((entry) => {
          const isSelected = panelOpen && selectedHash === entry.hash;
          const isLoading = loadingHash === entry.hash;
          const PanelIcon = isSelected ? ChevronLeft : ChevronRight;
          const panelLabel = isSelected
            ? t('changelog.closeDetails')
            : t('changelog.openDetails');
          const typeColor = CATEGORY_COLORS[entry.category] || CATEGORY_COLORS.other;
          return (
            <div
              key={entry.hash}
              role="button"
              tabIndex={0}
              className={`group/card flex w-full min-w-0 flex-col gap-3 rounded-lg border p-4 text-left transition-colors ${
                isSelected
                  ? 'border-ldvh-accent/45 bg-ldvh-accent/5'
                  : 'border-ldvh-border bg-ldvh-panel hover:border-ldvh-accent/40 hover:bg-ldvh-panel/95'
              }`}
              onClick={() => openCommitPage(entry)}
              onKeyDown={(event) => handleKeyboardOpen(event, () => openCommitPage(entry))}
            >
              <div className="flex min-w-0 items-center justify-between gap-2">
                <div className="ldvh-meta-muted flex min-w-0 flex-wrap items-center gap-1.5">
                  <span>{getCommitTypeLabel(entry.category, locale)}</span>
                  {entry.scope && (
                    <>
                      <span className="px-0.5" aria-hidden="true">·</span>
                      <span>{getCommitScopeLabel(entry.scope, locale)}</span>
                    </>
                  )}
                  {entry.isBreaking && (
                    <CommitBreakingBadge className="ml-1.5" />
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <CommitPushStatusBadge status={entry.pushStatus} />
                  <CopyPathButton
                    path={getCommitCopyContext(entry)}
                    label={t('changelog.copyContext')}
                    copiedLabel={t('changelog.copiedContext')}
                  />
                </div>
              </div>
              <div
                className="-mx-1 flex min-w-0 items-center gap-2 rounded-md border-l-2 bg-ldvh-bg/65 px-2.5 py-2 text-left ring-1 ring-inset ring-ldvh-border/50 transition-colors group-hover/card:bg-ldvh-bg/85"
                style={{ borderLeftColor: typeColor }}
              >
                <ObjectTypeIcon type="changelog" size={14} className="flex-shrink-0 transition-colors group-hover/card:text-ldvh-accent" style={{ color: typeColor }} />
                <div className="min-w-0 flex-1">
                  <div className="ldvh-card-title whitespace-normal break-words leading-snug transition-colors group-hover/card:text-ldvh-accent">
                    {entry.description || entry.message}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleSelectCommit(entry);
                  }}
                  title={panelLabel}
                  aria-label={panelLabel}
                  className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-transparent bg-transparent transition-colors focus-visible:border-ldvh-accent/50 focus-visible:outline-none ${
                    isSelected
                      ? 'text-ldvh-accent'
                      : 'text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent'
                  }`}
                >
                  {isLoading ? <Loader2 size={16} className="animate-spin" /> : <PanelIcon size={16} aria-hidden="true" />}
                </button>
              </div>
              <div className="ldvh-meta-muted self-end">
                {t('changelog.commitAt', { time: formatDateTime(entry.date) })}
                <CommitSignatureMeta signature={entry.signature} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
