import { useEffect, useState, type ReactNode } from 'react'
import MetricCard from '@/components/MetricCard';
import ContentCard from '@/components/ContentCard';
import PageHeader from '@/components/PageHeader';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  FileWarning,
  GitPullRequest,
  ShieldCheck,
  Target,
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
import { formatDateTime } from '@/utils/dateFormat'

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
    <span className={`ldvh-chip inline-flex max-w-full items-center rounded-md border px-2 py-1 ${statusClasses(status)}`}>
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
    <ContentCard
      title={title}
      icon={icon}
      headerExtra={<StatusPill status={status} label={statusLabel} />}
    >
      {children}
    </ContentCard>
  )
}

function ReportError({ title, error }: { title: string; error: LdvhReportError }) {
  const { t } = useI18n()
  return (
    <ReportCard
      title={title}
      icon={<AlertCircle size={16} />}
      status="open"
      statusLabel={t('validate.error')}
    >
      <p className="ldvh-meta break-words text-red-300">{error.error}</p>
      {error.stderr && <p className="ldvh-meta mt-2 break-words">{error.stderr}</p>}
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
      <div className="ldvh-mini-grid">
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.summary.remaining_gap_count)}</p>
          <p className="ldvh-caption">{t('validate.remainingGaps')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.checks.length)}</p>
          <p className="ldvh-caption">{t('validate.checks')}</p>
        </div>
      </div>
      <p className="ldvh-caption mt-3 truncate">{formatDateTime(report.metadata.generated_at)}</p>
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
      <div className="ldvh-mini-grid">
        <div>
          <p className="font-mono text-xl font-semibold text-red-300">{countText(open)}</p>
          <p className="ldvh-caption">{statusLabel('open')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-yellow-300">{countText(degraded)}</p>
          <p className="ldvh-caption">{statusLabel('degraded')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-sky-300">{countText(needsHumanGate)}</p>
          <p className="ldvh-caption">{statusLabel('needs_human_gate')}</p>
        </div>
      </div>
      <p className="ldvh-caption mt-3">
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
      <div className="ldvh-mini-grid">
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.metadata.record_count)}</p>
          <p className="ldvh-caption">{t('validate.records')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{countText(report.metadata.checked_file_count)}</p>
          <p className="ldvh-caption">{t('gt.filesChecked')}</p>
        </div>
        <div>
          <p className="font-mono text-xl font-semibold text-red-300">{countText(report.metadata.issue_count)}</p>
          <p className="ldvh-caption">{t('validate.issues')}</p>
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
  items: Array<{ key: string; status?: string; statusLabel?: string; title: string; detail?: string; writeback?: string }>
  empty: string
}) {
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
      <h3 className="ldvh-section-title mb-3">{title}</h3>
      {items.length === 0 ? (
        <p className="ldvh-body-muted">{empty}</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((item) => (
            <li key={item.key} className="rounded-md bg-ldvh-bg px-3 py-2">
              <div className="flex items-center gap-2">
                <span className="ldvh-body truncate">{item.title}</span>
                {item.status && (
                  <span className={`ldvh-chip shrink-0 rounded px-1.5 py-0.5 ${statusClasses(item.status)}`}>
                    {item.statusLabel || item.status}
                  </span>
                )}
              </div>
              {item.detail && <p className="ldvh-caption mt-1">{item.detail}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/** owner_area 颜色映射 */
const OWNER_AREA_COLORS: Record<string, string> = {
  agent: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300',
  code: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
  human_gate: 'border-sky-500/30 bg-sky-500/10 text-sky-300',
  runtime_projection: 'border-violet-500/30 bg-violet-500/10 text-violet-300',
  specs: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  test: 'border-lime-500/30 bg-lime-500/10 text-lime-300',
  web: 'border-pink-500/30 bg-pink-500/10 text-pink-300',
  work_model: 'border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-300',
  workflow: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  unknown: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
}

type LocalizedLabel = { zh: string; en: string }

const OWNER_AREA_LABELS: Record<string, { zh: string; en: string }> = {
  agent: { zh: 'Agent', en: 'Agent' },
  code: { zh: 'Code / 测试', en: 'Code / Test' },
  human_gate: { zh: 'Human Gate', en: 'Human Gate' },
  runtime_projection: { zh: '运行投影', en: 'Runtime Projection' },
  specs: { zh: '规范', en: 'Specs' },
  test: { zh: '测试', en: 'Test' },
  web: { zh: 'Web', en: 'Web' },
  work_model: { zh: '工作模型', en: 'Work Model' },
  workflow: { zh: '工作流', en: 'Workflow' },
  unknown: { zh: '未分类', en: 'Uncategorized' },
}

const GAP_CATEGORY_LABELS: Record<string, LocalizedLabel> = {
  decision_record_required: { zh: '必须人类决策记录', en: 'Human decision record required' },
  policy_clarification: { zh: '规范口径说明', en: 'Policy clarification' },
  implementation_support: { zh: '承接实现支持', en: 'Implementation support' },
  diagnostic_coverage: { zh: 'Code 降级提示/覆盖', en: 'Code degraded coverage' },
  lifecycle_trigger_sync: { zh: '生命周期触发同步', en: 'Lifecycle trigger sync' },
  platform_capability_sync: { zh: '平台能力承接同步', en: 'Platform capability sync' },
  projection_coverage_diagnostic: { zh: '投影覆盖诊断降级', en: 'Projection coverage diagnostic' },
  third_party_skill_projection: { zh: '第三方 Skill 投影', en: 'Third-party Skill projection' },
}

const REMEDIATION_LABELS: Record<string, LocalizedLabel> = {
  doc_crossref_check: { zh: '文档交叉引用检查', en: 'Document cross-reference check' },
  entry_sync_check: { zh: '入口/配置同步检查', en: 'Entry/config sync check' },
  platform_mapping_check: { zh: '平台能力映射检查', en: 'Platform capability mapping check' },
  drift_diagnostic: { zh: '漂移诊断', en: 'Drift diagnostic' },
  skill_projection_check: { zh: 'Skill 投影检查', en: 'Skill projection check' },
}

const WRITEBACK_LABELS: Record<string, LocalizedLabel> = {
  agent_or_44: { zh: 'Agent / 44 多角色思考', en: 'Agent / 44 multi-role thinking' },
  code_request_or_test: { zh: 'Code / 测试需求', en: 'Code / test request' },
  fact_yaml_fix_or_task: { zh: '事实 YAML 修复 / 任务', en: 'Fact YAML fix / task' },
  governed_projects_config: { zh: '管辖项目配置', en: 'Governed projects config' },
  human_gate_record: { zh: 'Human Gate 记录', en: 'Human Gate record' },
  landing_report_followup: { zh: '落地报告跟进', en: 'Landing report follow-up' },
  manual_review: { zh: '人工复核', en: 'Manual review' },
  none: { zh: '无需回写', en: 'No writeback' },
  runtime_projection_or_env_record: { zh: '运行投影 / 环境记录', en: 'Runtime projection / env record' },
  spec_fix_or_task: { zh: '规范修复 / 任务', en: 'Spec fix / task' },
  specs: { zh: '规范文档', en: 'Specs document' },
  workflow_or_skill_candidate: { zh: '工作流 / Skill 候选', en: 'Workflow / Skill candidate' },
}

const VALIDATION_PLAN_LABELS: Record<string, LocalizedLabel> = {
  spec_validate_status: { zh: '规范校验', en: 'Spec validation' },
  fact_validate_status: { zh: '事实校验', en: 'Fact validation' },
  runtime_projection_status: { zh: '运行投影', en: 'Runtime projection' },
  human_gate_status: { zh: 'Human Gate', en: 'Human Gate' },
}

function localizeLabel(
  labels: Record<string, LocalizedLabel>,
  key: string,
  fallback: string | undefined,
  locale: 'zh' | 'en',
) {
  const entry = labels[key]
  if (entry) return locale === 'en' ? entry.en : entry.zh
  return fallback || key
}

export default function Validate() {
  const [data, setData] = useState<ValidationData | null>(null)
  const [landingPlan, setLandingPlan] = useState<LandingPlanData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'validate' | 'landing'>('validate')
  const { t, getStatus, locale } = useI18n()

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
          <p className="ldvh-body-muted">{t('common.loadFailed')}</p>
          <p className="ldvh-meta text-red-400">{error}</p>
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
    statusLabel: gap.status ? getStatus(gap.status) : undefined,
    title: gap.id || t('validate.remainingGaps'),
    detail: gap.message,
    writeback: gap.suggested_writeback,
  })) ?? []

  const capabilityGapItems = landingReportData?.capability_gaps.map((gap, index) => ({
    key: `${gap.id || 'capability-gap'}-${index}`,
    status: gap.status,
    statusLabel: gap.status ? getStatus(gap.status) : undefined,
    title: gap.capability,
    detail: gap.evidence,
    writeback: gap.suggested_writeback,
  })) ?? []

  return (
    <div className="ldvh-page-frame space-y-6">
      <div className="ldvh-page-toolbar">
        <PageHeader title={t('validate.title')} />
        {/* 视图切换 */}
        <div className="flex rounded-lg border border-ldvh-border bg-ldvh-bg p-0.5">
          <button
            onClick={() => setActiveTab('validate')}
            className={`ldvh-chip rounded-md px-3 py-1.5 transition-colors ${
              activeTab === 'validate'
                ? 'bg-ldvh-accent/20 text-ldvh-accent'
                : 'text-ldvh-text-secondary hover:text-ldvh-text-primary'
            }`}
          >
            {t('validate.tabValidate')}
          </button>
          <button
            onClick={() => setActiveTab('landing')}
            className={`ldvh-chip rounded-md px-3 py-1.5 transition-colors ${
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
          <div className="ldvh-metric-grid">
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
              <h2 className="ldvh-section-title">{t('validate.ldvhChecks')}</h2>
              {landingReportData?.metadata.generated_at && (
                <span className="ldvh-meta truncate">
                  {formatDateTime(landingReportData.metadata.generated_at)}
                </span>
              )}
            </div>

            <div className="ldvh-section-grid">
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

            <div className="ldvh-panel-grid">
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
              <p className="ldvh-body">{t('validate.allPassed')}</p>
              <p className="ldvh-body-muted">{t('validate.noIssues')}</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <h2 className="ldvh-section-title">{t('validate.byFile')}</h2>
              {Object.entries(issuesByFile).map(([file, issues]) => (
                <div
                  key={file}
                  className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4"
                >
                  <h3 className="ldvh-meta-primary mb-3 break-words">{file}</h3>
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
                            <span className="ldvh-meta-primary font-medium">
                              {issue.code}
                            </span>
                            <span className={`ldvh-meta ${issue.level === 'error' ? 'text-red-400' : 'text-yellow-400'}`}>
                              {issue.level === 'error' ? t('validate.error') : t('validate.warning')}
                            </span>
                            {issue.field && (
                              <span className="ldvh-meta break-words">
                                → {issue.field}
                              </span>
                            )}
                          </div>
                          <p className="ldvh-body-muted break-words">{issue.message}</p>
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
          <div className="ldvh-metric-grid">
            <MetricCard
              icon={<Target size={20} className="text-ldvh-text-secondary" />}
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
              <p className="ldvh-body">{t('lp.writesNeeded')}</p>
              <p className="ldvh-caption mt-1">
                {t('lp.writesNeededTargets')}: {(landingPlan.writeback_targets || [])
                  .map((target) => localizeLabel(WRITEBACK_LABELS, target, undefined, locale))
                  .join(', ')}
              </p>
            </div>
          )}

          {/* 按 owner_area 分组 */}
          <section className="space-y-4">
            <h2 className="ldvh-section-title">{t('lp.gapsByOwner')}</h2>
            {landingPlan?.proposed_actions?.map((action) => {
              const areaColor = OWNER_AREA_COLORS[action.owner_area] || OWNER_AREA_COLORS.unknown
              const areaLabel = localizeLabel(OWNER_AREA_LABELS, action.owner_area, action.label, locale)
              const openCount = action.by_status.open || 0
              const degradedCount = action.by_status.degraded || 0
              const hgCount = action.by_status.needs_human_gate || 0
              const closedCount = action.by_status.closed || 0
              const total = action.gap_count

              return (
                <div key={action.owner_area} className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`ldvh-chip rounded px-2 py-0.5 ${areaColor}`}>{areaLabel}</span>
                      <span className="ldvh-caption">{t('lp.gapCount', { count: String(total) })}</span>
                    </div>
                    {action.suggested_writebacks.length > 0 && (
                      <span className="ldvh-meta truncate">
                        → {action.suggested_writebacks.map((target) => localizeLabel(WRITEBACK_LABELS, target, undefined, locale)).join(', ')}
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
                  <div className="ldvh-caption mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
                    {openCount > 0 && <span className="text-red-300">{getStatus('open')} {openCount}</span>}
                    {degradedCount > 0 && <span className="text-yellow-300">{getStatus('degraded')} {degradedCount}</span>}
                    {hgCount > 0 && <span className="text-sky-300">{getStatus('needs_human_gate')} {hgCount}</span>}
                    {closedCount > 0 && <span className="text-emerald-300">{getStatus('closed')} {closedCount}</span>}
                  </div>

                  {/* 子类别 */}
                  {action.subcategories && Object.keys(action.subcategories).length > 0 && (
                    <div className="mt-3 border-t border-ldvh-border pt-3">
                      <p className="ldvh-caption-strong mb-2">{t('lp.subcategories')}</p>
                      <div className="ldvh-compact-grid">
                        {Object.entries(action.subcategories).map(([key, sub]) => (
                          <div key={key} title={key} className="rounded-md bg-ldvh-bg px-3 py-1.5">
                            <span className="ldvh-caption text-ldvh-text-primary">
                              {localizeLabel(GAP_CATEGORY_LABELS, key, sub.label, locale)}
                            </span>
                            <span className="ldvh-meta ml-2">{sub.total}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 补救类型（仅 runtime_projection） */}
                  {action.remediation && Object.keys(action.remediation).length > 0 && (
                    <div className="mt-3 border-t border-ldvh-border pt-3">
                      <p className="ldvh-caption-strong mb-2">{t('lp.remediation')}</p>
                      <div className="ldvh-compact-grid">
                        {Object.entries(action.remediation).map(([key, rem]) => (
                          <div key={key} title={key} className="rounded-md bg-ldvh-bg px-3 py-1.5">
                            <span className="ldvh-caption text-ldvh-text-primary">
                              {localizeLabel(REMEDIATION_LABELS, key, rem.label, locale)}
                            </span>
                            <span className="ldvh-meta ml-2">{rem.total}</span>
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
                <p className="ldvh-body-muted">{t('lp.noGaps')}</p>
              </div>
            )}
          </section>

          {/* 验证计划状态 */}
          {landingPlan?.validation_plan && (
            <section className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
              <h2 className="ldvh-section-title mb-3">{t('lp.validationStatus')}</h2>
              <div className="ldvh-metric-grid">
                {Object.entries(landingPlan.validation_plan).map(([key, val]) => (
                  <div key={key} title={key} className="rounded-md bg-ldvh-bg p-3">
                    <p className="ldvh-caption">{localizeLabel(VALIDATION_PLAN_LABELS, key, undefined, locale)}</p>
                    <p className={`ldvh-card-title mt-1 ${val === 'closed' ? 'text-emerald-300' : val === 'open' ? 'text-red-300' : 'text-yellow-300'}`}>
                      {getStatus(val)}
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
