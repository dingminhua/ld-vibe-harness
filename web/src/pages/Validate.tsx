import { useEffect, useState, type ReactNode } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  FileWarning,
  GitPullRequest,
  ShieldCheck,
} from 'lucide-react';
import {
  fetchValidation,
  type LdvhHumanGateReport,
  type LdvhLandingCheckReport,
  type LdvhLandingReport,
  type LdvhReportError,
  type ValidationData,
  type ValidationIssue,
} from '@/utils/api';
import { useI18n } from '@/i18n/context';

function isReportError(report: unknown): report is LdvhReportError {
  return typeof report === 'object' && report !== null && 'error' in report && 'exitCode' in report;
}

function countText(value?: number): string {
  return typeof value === 'number' ? String(value) : '0';
}

function dateText(value?: string): string {
  if (!value) return '—';
  return value.replace('T', ' ').slice(0, 16);
}

function statusClasses(status?: string): string {
  switch (status) {
    case 'closed':
      return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
    case 'open':
      return 'border-red-500/30 bg-red-500/10 text-red-300';
    case 'degraded':
      return 'border-yellow-500/30 bg-yellow-500/10 text-yellow-300';
    case 'needs_human_gate':
      return 'border-sky-500/30 bg-sky-500/10 text-sky-300';
    default:
      return 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary';
  }
}

function StatusPill({ status, label }: { status?: string; label: string }) {
  return (
    <span className={`inline-flex max-w-full items-center rounded-md border px-2 py-1 text-xs font-medium ${statusClasses(status)}`}>
      <span className="truncate">{label}</span>
    </span>
  );
}

function MetricCard({
  icon,
  value,
  label,
  valueClassName = 'text-ldvh-text-primary',
}: {
  icon: ReactNode;
  value: string;
  label: string;
  valueClassName?: string;
}) {
  return (
    <div className="flex min-w-0 items-center gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
      <div className="flex-shrink-0">{icon}</div>
      <div className="min-w-0">
        <p className={`font-mono text-2xl font-semibold ${valueClassName}`}>{value}</p>
        <p className="truncate text-xs text-ldvh-text-secondary">{label}</p>
      </div>
    </div>
  );
}

function ReportCard({
  title,
  icon,
  status,
  statusLabel,
  children,
}: {
  title: string;
  icon: ReactNode;
  status?: string;
  statusLabel: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
      <div className="mb-4 flex min-w-0 items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <span className="flex-shrink-0 text-ldvh-text-secondary">{icon}</span>
          <h2 className="truncate text-sm font-semibold text-ldvh-text-primary">{title}</h2>
        </div>
        <StatusPill status={status} label={statusLabel} />
      </div>
      {children}
    </div>
  );
}

function ReportError({ title, error }: { title: string; error: LdvhReportError }) {
  return (
    <ReportCard
      title={title}
      icon={<AlertCircle size={16} />}
      status="open"
      statusLabel="error"
    >
      <p className="break-words font-mono text-xs text-red-300">{error.error}</p>
      {error.stderr && <p className="mt-2 break-words font-mono text-xs text-ldvh-text-secondary">{error.stderr}</p>}
    </ReportCard>
  );
}

function LandingCheckCard({
  report,
  statusLabel,
  t,
}: {
  report: LdvhLandingCheckReport;
  statusLabel: (status?: string) => string;
  t: ReturnType<typeof useI18n>['t'];
}) {
  return (
    <ReportCard
      title={t('validate.landingCheck')}
      icon={<GitPullRequest size={16} />}
      status={report.summary.status}
      statusLabel={statusLabel(report.summary.status)}
    >
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.summary.remaining_gap_count)}</p>
          <p className="text-xs text-ldvh-text-secondary">{t('validate.remainingGaps')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.checks.length)}</p>
          <p className="text-xs text-ldvh-text-secondary">{t('validate.checks')}</p>
        </div>
      </div>
      <p className="mt-3 truncate text-xs text-ldvh-text-secondary">{dateText(report.metadata.generated_at)}</p>
    </ReportCard>
  );
}

function LandingReportCard({
  report,
  statusLabel,
  t,
}: {
  report: LdvhLandingReport;
  statusLabel: (status?: string) => string;
  t: ReturnType<typeof useI18n>['t'];
}) {
  const open = report.summary.by_status.open ?? 0;
  const degraded = report.summary.by_status.degraded ?? 0;
  const needsHumanGate = report.summary.by_status.needs_human_gate ?? 0;

  return (
    <ReportCard
      title={t('validate.landingReport')}
      icon={<Activity size={16} />}
      status={open > 0 ? 'open' : degraded > 0 ? 'degraded' : 'closed'}
      statusLabel={statusLabel(open > 0 ? 'open' : degraded > 0 ? 'degraded' : 'closed')}
    >
      <div className="grid grid-cols-3 gap-3">
        <div>
          <p className="font-mono text-xl font-semibold text-red-300">{countText(open)}</p>
          <p className="text-xs text-ldvh-text-secondary">{statusLabel('open')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-yellow-300">{countText(degraded)}</p>
          <p className="text-xs text-ldvh-text-secondary">{statusLabel('degraded')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-sky-300">{countText(needsHumanGate)}</p>
          <p className="text-xs text-ldvh-text-secondary">{statusLabel('needs_human_gate')}</p>
        </div>
      </div>
      <p className="mt-3 text-xs text-ldvh-text-secondary">
        {t('validate.gapTotal')}: <span className="font-mono text-ldvh-text-primary">{countText(report.summary.gap_total)}</span>
      </p>
    </ReportCard>
  );
}

function HumanGateCard({
  report,
  statusLabel,
  t,
}: {
  report: LdvhHumanGateReport;
  statusLabel: (status?: string) => string;
  t: ReturnType<typeof useI18n>['t'];
}) {
  return (
    <ReportCard
      title={t('validate.humanGate')}
      icon={<ShieldCheck size={16} />}
      status={report.summary.status}
      statusLabel={statusLabel(report.summary.status)}
    >
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.metadata.record_count)}</p>
          <p className="text-xs text-ldvh-text-secondary">{t('validate.records')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.metadata.checked_file_count)}</p>
          <p className="text-xs text-ldvh-text-secondary">{t('validate.filesChecked')}</p>
        </div>
      </div>
      <p className="mt-3 text-xs text-ldvh-text-secondary">
        {t('validate.issues')}: <span className="font-mono text-ldvh-text-primary">{countText(report.metadata.issue_count)}</span>
      </p>
    </ReportCard>
  );
}

function CompactList({
  title,
  items,
  empty,
}: {
  title: string;
  items: Array<{ key: string; status?: string; title?: string; detail?: string; writeback?: string }>;
  empty: string;
}) {
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
      <h2 className="mb-3 text-sm font-semibold text-ldvh-text-primary">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-ldvh-text-secondary">{empty}</p>
      ) : (
        <ul className="divide-y divide-ldvh-border">
          {items.map((item) => (
            <li key={item.key} className="py-3">
              <div className="mb-1 flex min-w-0 items-center gap-2">
                {item.status && (
                  <span className={`h-2 w-2 flex-shrink-0 rounded-full ${item.status === 'open' ? 'bg-red-400' : item.status === 'degraded' ? 'bg-yellow-400' : item.status === 'needs_human_gate' ? 'bg-sky-400' : 'bg-emerald-400'}`} />
                )}
                <p className="min-w-0 flex-1 truncate text-sm font-medium text-ldvh-text-primary">{item.title}</p>
              </div>
              {item.detail && <p className="break-words text-xs text-ldvh-text-secondary">{item.detail}</p>}
              {item.writeback && <p className="mt-1 break-words font-mono text-xs text-ldvh-text-secondary">{item.writeback}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Validate() {
  const [data, setData] = useState<ValidationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { t, getStatus } = useI18n();

  useEffect(() => {
    fetchValidation()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="text-ldvh-text-secondary">{t('common.loadFailed')}</p>
          <p className="font-mono text-xs text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  const issuesByFile = data.issues.reduce<Record<string, ValidationIssue[]>>((acc, issue) => {
    const file = issue.path;
    if (!acc[file]) acc[file] = [];
    acc[file].push(issue);
    return acc;
  }, {});

  const landingCheck = data.reports?.landingCheck;
  const landingReport = data.reports?.landingReport;
  const humanGateReport = data.reports?.humanGateReport;

  const landingCheckData = landingCheck && !isReportError(landingCheck) ? landingCheck : null;
  const landingReportData = landingReport && !isReportError(landingReport) ? landingReport : null;
  const humanGateData = humanGateReport && !isReportError(humanGateReport) ? humanGateReport : null;

  const remainingGapItems = landingCheckData?.remaining_gaps.map((gap, index) => ({
    key: `${gap.id || 'remaining-gap'}-${index}`,
    status: gap.status,
    title: gap.id || t('validate.remainingGaps'),
    detail: gap.message,
    writeback: gap.suggested_writeback,
  })) ?? [];

  const capabilityGapItems = landingReportData?.capability_gaps.map((gap, index) => ({
    key: `${gap.id || 'capability-gap'}-${index}`,
    status: gap.status,
    title: gap.capability,
    detail: gap.evidence,
    writeback: gap.suggested_writeback,
  })) ?? [];

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-xl font-semibold text-ldvh-text-primary">{t('validate.title')}</h1>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <MetricCard
          icon={<FileWarning size={20} className="text-ldvh-text-secondary" />}
          value={countText(data.summary.files)}
          label={t('validate.filesChecked')}
        />
        <MetricCard
          icon={<AlertCircle size={20} className="text-red-400" />}
          value={countText(data.summary.errors)}
          label={t('validate.errors')}
          valueClassName="text-red-400"
        />
        <MetricCard
          icon={<AlertTriangle size={20} className="text-yellow-400" />}
          value={countText(data.summary.warnings)}
          label={t('validate.warnings')}
          valueClassName="text-yellow-400"
        />
      </div>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-ldvh-text-primary">{t('validate.ldvhChecks')}</h2>
          {landingReportData?.metadata.generated_at && (
            <span className="truncate font-mono text-xs text-ldvh-text-secondary">
              {dateText(landingReportData.metadata.generated_at)}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
          {landingCheck && isReportError(landingCheck) ? (
            <ReportError title={t('validate.landingCheck')} error={landingCheck} />
          ) : landingCheckData ? (
            <LandingCheckCard report={landingCheckData} statusLabel={getStatus} t={t} />
          ) : null}

          {landingReport && isReportError(landingReport) ? (
            <ReportError title={t('validate.landingReport')} error={landingReport} />
          ) : landingReportData ? (
            <LandingReportCard report={landingReportData} statusLabel={getStatus} t={t} />
          ) : null}

          {humanGateReport && isReportError(humanGateReport) ? (
            <ReportError title={t('validate.humanGate')} error={humanGateReport} />
          ) : humanGateData ? (
            <HumanGateCard report={humanGateData} statusLabel={getStatus} t={t} />
          ) : null}
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <CompactList
            title={t('validate.remainingGaps')}
            items={remainingGapItems}
            empty={t('validate.noRemainingGaps')}
          />
          <CompactList
            title={t('validate.capabilityGaps')}
            items={capabilityGapItems}
            empty={t('validate.noCapabilityGaps')}
          />
        </div>
      </section>

      {data.issues.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16">
          <CheckCircle size={40} className="mb-3 text-green-400" />
          <p className="text-ldvh-text-primary">{t('validate.allPassed')}</p>
          <p className="text-sm text-ldvh-text-secondary">{t('validate.noIssues')}</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <h2 className="text-base font-semibold text-ldvh-text-primary">{t('validate.byFile')}</h2>
          {Object.entries(issuesByFile).map(([file, issues]) => (
            <div
              key={file}
              className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4"
            >
              <h3 className="mb-3 break-words font-mono text-sm text-ldvh-text-primary">{file}</h3>
              <ul className="flex flex-col gap-2">
                {issues.map((issue, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 rounded-md bg-ldvh-bg px-3 py-2"
                  >
                    {issue.level === 'error' ? (
                      <AlertCircle size={14} className="mt-0.5 flex-shrink-0 text-red-400" />
                    ) : (
                      <AlertTriangle size={14} className="mt-0.5 flex-shrink-0 text-yellow-400" />
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-medium text-ldvh-text-primary">
                          {issue.code}
                        </span>
                        <span className={`font-mono text-xs ${issue.level === 'error' ? 'text-red-400' : 'text-yellow-400'}`}>
                          {issue.level === 'error' ? t('validate.error') : t('validate.warning')}
                        </span>
                        {issue.field && (
                          <span className="break-words font-mono text-xs text-ldvh-text-secondary">
                            → {issue.field}
                          </span>
                        )}
                      </div>
                      <p className="break-words text-sm text-ldvh-text-secondary">{issue.message}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
