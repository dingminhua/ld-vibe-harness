import { useEffect, useState, type ReactNode } from 'react'
import MetricCard from '@/components/MetricCard';
import PageHeader from '@/components/PageHeader';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  FileWarning,
  GitPullRequest,
  Layers,
  ShieldCheck,
} from 'lucide-react'
import {
  fetchValidation,
  type LdvhHumanGateReport,
  type LdvhLandingCheckReport,
  type LdvhLandingReport,
  type LdvhReportError,
  type ValidationData,
  type ValidationIssue,
} from '@/utils/api'
import { useI18n } from '@/i18n/context'

const API_BASE = '/api'

interface LandingPlanGapArea {
  owner_area: string
  label: string
  gap_count: number
  by_status: Record<string, number>
  suggested_writebacks: string[]
  subcategories?: Record<string, { label: string; total: number }>
  remediation?: Record<string, { label: string; total: number }>
}

interface LandingPlanData {
  metadata?: { generated_at?: string }
  scope?: { project_root?: string; landing_report_sources?: number; landing_report_requirements?: number }
  requirements?: { total: number; by_status: Record<string, number>; gap_total: number; gap_by_owner_area: Record<string, number> }
  gaps?: { by_owner_area: Record<string, number> }
  proposed_actions?: LandingPlanGapArea[]
  capabilities?: Array<{ id: string; source_area: string; status: string; issue_count: number }>
  validation_plan?: Record<string, string>
  human_gate?: { total_gaps: number; subcategories?: Record<string, { label: string; total: number }> }
  writes_required?: { required: boolean; targets: string[] }
  writeback_targets?: string[]
}

function isReportError(report: unknown): report is LdvhReportError {
  return typeof report === 'object' && report !== null && 'error' in report && 'exitCode' in report
}

function countText(value?: number): string {
  return typeof value === 'number' ? String(value) : '0'
}

function dateText(value?: string): string {
  if (!value) return '—'
  return value.replace('T', ' ').slice(0, 16)
}

function statusClasses(status?: string): string {
  switch (status) {
    case 'closed':
      return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
    case 'open':
      return 'border-red-500/30 bg-red-500/10 text-red-300'
    case 'degraded':
      return 'border-yellow-500/30 bg-yellow-500/10 text-yellow-300'
    case 'needs_human_gate':
      return 'border-sky-500/30 bg-sky-500/10 text-sky-300'
    default:
      return 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary'
  }
}

function StatusPill({ status, label }: { status?: string; label: string }) {
  return (
    <span className={`inline-flex max-w-full items-center rounded-md border px-2 py-1 text-xs font-medium ${statusClasses(status)}`}>
      <span className="truncate">{label}</span>
    </span>
  )
}

function ReportCard({
  title,
  icon,
  status,
  statusLabel,
  children,
}: {
  title: string
  icon: ReactNode
  status?: string
  statusLabel: string
  children: ReactNode
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
  )
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
  )
}

function LandingCheckCard({
  report,
  statusLabel,
  t,
}: {
  report: LdvhLandingCheckReport
  statusLabel: (status?: string) => string
  t: ReturnType<typeof useI18n>['t']
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
  )
}

function LandingReportCard({
  report,
  statusLabel,
  t,
}: {
  report: LdvhLandingReport
  statusLabel: (status?: string) => string
  t: ReturnType<typeof useI18n>['t']
}) {
  const open = report.summary.by_status.open ?? 0
  const degraded = report.summary.by_status.degraded ?? 0
  const needsHumanGate = report.summary.by_status.needs_human_gate ?? 0

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
        {t('validate.gapTotal')}: {countText(report.summary.gap_total)}
      </p>
    </ReportCard>
  )
}

function HumanGateCard({
  report,
  statusLabel,
  t,
}: {
  report: LdvhHumanGateReport
  statusLabel: (status?: string) => string
  t: ReturnType<typeof useI18n>['t']
}) {
  return (
    <ReportCard
      title={t('validate.humanGate')}
      icon={<ShieldCheck size={16} />}
      status={report.summary.status}
      statusLabel={statusLabel(report.summary.status)}
    >
      <div className="grid grid-cols-3 gap-3">
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.metadata.record_count)}</p>
          <p className="text-xs text-ldvh-text-secondary">{t('validate.records')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.metadata.checked_file_count)}</p>
          <p className="text-xs text-ldvh-text-secondary">{t('gt.filesChecked')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-red-300">{countText(report.metadata.issue_count)}</p>
          <p className="text-xs text-ldvh-text-secondary">{t('validate.issues')}</p>
        </div>
      </div>
    </ReportCard>
  )
}

function CompactList({
  title,
  items,
  empty,
}: {
  title: string
  items: Array<{ key: string; status?: string; title: string; detail?: string; writeback?: string }>
  empty: string
}) {
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
      <h3 className="mb-3 text-sm font-semibold text-ldvh-text-primary">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-ldvh-text-secondary">{empty}</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((item) => (
            <li key={item.key} className="rounded-md bg-ldvh-bg px-3 py-2">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm text-ldvh-text-primary">{item.title}</span>
                {item.status && (
                  <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${statusClasses(item.status)}`}>
                    {item.status}
                  </span>
                )}
              </div>
              {item.detail && <p className="mt-1 text-xs text-ldvh-text-secondary">{item.detail}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/** owner_area 颜色映射 */
const OWNER_AREA_COLORS: Record<string, string> = {
  code: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
  human_gate: 'border-sky-500/30 bg-sky-500/10 text-sky-300',
  runtime_projection: 'border-violet-500/30 bg-violet-500/10 text-violet-300',
  specs: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  workflow: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  unknown: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
}

const OWNER_AREA_LABELS: Record<string, string> = {
  code: 'Code',
  human_gate: 'Human Gate',
  runtime_projection: '运行投影',
  specs: '规范',
  workflow: '工作流',
  unknown: '未分类',
}

export default function Validate() {
  const [data, setData] = useState<ValidationData | null>(null)
  const [landingPlan, setLandingPlan] = useState<LandingPlanData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'validate' | 'landing'>('validate')
  const { t, getStatus } = useI18n()

  useEffect(() => {
    Promise.all([
      fetchValidation(),
      fetch(`${API_BASE}/landing-plan`).then(res => res.ok ? res.json() : null),
    ])
      .then(([valData, lpData]) => {
        setData(valData)
        if (lpData) setLandingPlan(lpData)
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="text-ldvh-text-secondary">{t('common.loadFailed')}</p>
          <p className="font-mono text-xs text-red-400">{error}</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    )
  }

  const issuesByFile: Record<string, ValidationIssue[]> = {}
  for (const issue of data.issues) {
    const path = issue.path || 'root'
    if (!issuesByFile[path]) issuesByFile[path] = []
    issuesByFile[path].push(issue)
  }

  const landingCheck = data.reports?.landingCheck
  const landingReport = data.reports?.landingReport
  const humanGateReport = data.reports?.humanGateReport
  const landingCheckData = landingCheck && !isReportError(landingCheck) ? landingCheck : null
  const landingReportData = landingReport && !isReportError(landingReport) ? landingReport : null
  const humanGateData = humanGateReport && !isReportError(humanGateReport) ? humanGateReport : null

  const remainingGapItems = landingCheckData?.remaining_gaps.map((gap, index) => ({
    key: `${gap.id || 'remaining-gap'}-${index}`,
    status: gap.status,
    title: gap.id || t('validate.remainingGaps'),
    detail: gap.message,
    writeback: gap.suggested_writeback,
  })) ?? []

  const capabilityGapItems = landingReportData?.capability_gaps.map((gap, index) => ({
    key: `${gap.id || 'capability-gap'}-${index}`,
    status: gap.status,
    title: gap.capability,
    detail: gap.evidence,
    writeback: gap.suggested_writeback,
  })) ?? []

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between gap-3">
        <PageHeader title={t('validate.title')} />
        {/* 视图切换 */}
        <div className="flex rounded-lg border border-ldvh-border bg-ldvh-bg p-0.5">
          <button
            onClick={() => setActiveTab('validate')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === 'validate'
                ? 'bg-ldvh-accent/20 text-ldvh-accent'
                : 'text-ldvh-text-secondary hover:text-ldvh-text-primary'
            }`}
          >
            {t('validate.tabValidate')}
          </button>
          <button
            onClick={() => setActiveTab('landing')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === 'landing'
                ? 'bg-ldvh-accent/20 text-ldvh-accent'
                : 'text-ldvh-text-secondary hover:text-ldvh-text-primary'
            }`}
          >
            {t('validate.tabLanding')}
          </button>
        </div>
      </div>

      {activeTab === 'validate' ? (
        /* === 校验视图 === */
        <>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <MetricCard
              icon={<FileWarning size={20} className="text-ldvh-text-secondary" />}
              value={countText(data.summary.files)}
              label={t('validate.filesChecked')}
              tone="default"
            />
            <MetricCard
              icon={<AlertCircle size={20} className="text-red-400" />}
              value={countText(data.summary.errors)}
              label={t('validate.errors')}
              tone="red"
            />
            <MetricCard
              icon={<AlertTriangle size={20} className="text-yellow-400" />}
              value={countText(data.summary.warnings)}
              label={t('validate.warnings')}
              tone="default"
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
              <CheckCircle size={40} className="mb-3 text-emerald-400" />
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
        </>
      ) : (
        /* === Landing Plan 按 owner_area 分组视图 === */
        <>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <MetricCard
              icon={<Layers size={20} className="text-ldvh-text-secondary" />}
              value={countText(landingPlan?.requirements?.total)}
              label={t('lp.totalRequirements')}
            />
            <MetricCard
              icon={<AlertCircle size={20} className="text-red-400" />}
              value={countText(landingPlan?.requirements?.gap_total)}
              label={t('lp.openGaps')}
              tone="red"
            />
            <MetricCard
              icon={<GitPullRequest size={20} className="text-ldvh-text-secondary" />}
              value={countText(landingPlan?.scope?.landing_report_sources)}
              label={t('lp.sourceFiles')}
            />
            <MetricCard
              icon={<ShieldCheck size={20} className="text-ldvh-text-secondary" />}
              value={landingPlan?.human_gate?.total_gaps !== undefined ? String(landingPlan.human_gate.total_gaps) : '—'}
              label={t('lp.humanGateGaps')}
            />
          </div>

          {/* 写入需求提示 */}
          {landingPlan?.writes_required?.required && (
            <div className="rounded-lg border border-sky-500/30 bg-sky-500/10 p-4">
              <p className="text-sm text-ldvh-text-primary">{t('lp.writesNeeded')}</p>
              <p className="mt-1 text-xs text-ldvh-text-secondary">
                {t('lp.writesNeededTargets')}: {(landingPlan.writeback_targets || []).join(', ')}
              </p>
            </div>
          )}

          {/* 按 owner_area 分组 */}
          <section className="space-y-4">
            <h2 className="text-base font-semibold text-ldvh-text-primary">{t('lp.gapsByOwner')}</h2>
            {landingPlan?.proposed_actions?.map((action) => {
              const areaColor = OWNER_AREA_COLORS[action.owner_area] || OWNER_AREA_COLORS.unknown
              const areaLabel = action.label || OWNER_AREA_LABELS[action.owner_area] || action.owner_area
              const openCount = action.by_status.open || 0
              const degradedCount = action.by_status.degraded || 0
              const hgCount = action.by_status.needs_human_gate || 0
              const closedCount = action.by_status.closed || 0
              const total = action.gap_count

              return (
                <div key={action.owner_area} className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`rounded px-2 py-0.5 text-xs font-medium ${areaColor}`}>{areaLabel}</span>
                      <span className="text-xs text-ldvh-text-secondary">{t('lp.gapCount', { count: String(total) })}</span>
                    </div>
                    {action.suggested_writebacks.length > 0 && (
                      <span className="truncate font-mono text-[10px] text-ldvh-text-secondary">
                        → {action.suggested_writebacks.join(', ')}
                      </span>
                    )}
                  </div>

                  {/* 状态分布条 */}
                  <div className="mt-2 flex h-2 overflow-hidden rounded-full bg-ldvh-border">
                    {closedCount > 0 && (
                      <div className="h-full bg-emerald-500/70" style={{ width: `${(closedCount / total) * 100}%` }} />
                    )}
                    {degradedCount > 0 && (
                      <div className="h-full bg-yellow-500/70" style={{ width: `${(degradedCount / total) * 100}%` }} />
                    )}
                    {openCount > 0 && (
                      <div className="h-full bg-red-500/70" style={{ width: `${(openCount / total) * 100}%` }} />
                    )}
                    {hgCount > 0 && (
                      <div className="h-full bg-sky-500/70" style={{ width: `${(hgCount / total) * 100}%` }} />
                    )}
                  </div>
                  <div className="mt-2 flex items-center gap-3 text-xs text-ldvh-text-secondary">
                    {openCount > 0 && <span className="text-red-300">open {openCount}</span>}
                    {degradedCount > 0 && <span className="text-yellow-300">degraded {degradedCount}</span>}
                    {hgCount > 0 && <span className="text-sky-300">needs_gate {hgCount}</span>}
                    {closedCount > 0 && <span className="text-emerald-300">closed {closedCount}</span>}
                  </div>

                  {/* 子类别 */}
                  {action.subcategories && Object.keys(action.subcategories).length > 0 && (
                    <div className="mt-3 border-t border-ldvh-border pt-3">
                      <p className="mb-2 text-xs font-medium text-ldvh-text-secondary">{t('lp.subcategories')}</p>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(action.subcategories).map(([key, sub]) => (
                          <div key={key} className="rounded-md bg-ldvh-bg px-3 py-1.5">
                            <span className="text-xs text-ldvh-text-primary">{sub.label || key}</span>
                            <span className="ml-2 font-mono text-xs text-ldvh-text-secondary">{sub.total}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 补救类型（仅 runtime_projection） */}
                  {action.remediation && Object.keys(action.remediation).length > 0 && (
                    <div className="mt-3 border-t border-ldvh-border pt-3">
                      <p className="mb-2 text-xs font-medium text-ldvh-text-secondary">{t('lp.remediation')}</p>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(action.remediation).map(([key, rem]) => (
                          <div key={key} className="rounded-md bg-ldvh-bg px-3 py-1.5">
                            <span className="text-xs text-ldvh-text-primary">{rem.label || key}</span>
                            <span className="ml-2 font-mono text-xs text-ldvh-text-secondary">{rem.total}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            }) || (
              <div className="flex flex-col items-center justify-center py-8">
                <CheckCircle size={32} className="mb-3 text-emerald-400" />
                <p className="text-sm text-ldvh-text-secondary">{t('lp.noGaps')}</p>
              </div>
            )}
          </section>

          {/* 验证计划状态 */}
          {landingPlan?.validation_plan && (
            <section className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
              <h2 className="mb-3 text-sm font-semibold text-ldvh-text-primary">{t('lp.validationStatus')}</h2>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                {Object.entries(landingPlan.validation_plan).map(([key, val]) => (
                  <div key={key} className="rounded-md bg-ldvh-bg p-3">
                    <p className="font-mono text-[10px] text-ldvh-text-secondary">{key}</p>
                    <p className={`mt-1 text-sm font-medium ${val === 'closed' ? 'text-emerald-300' : val === 'open' ? 'text-red-300' : 'text-yellow-300'}`}>
                      {val}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
