import MetricCard from '@/components/MetricCard';
import StatusBanner from '@/components/StatusBanner';
import ContentCard from '@/components/ContentCard';
import PageHeader from '@/components/PageHeader';
import { useEffect, useState } from 'react'
import {
  AlertCircle,
  CheckCircle,
  Clock,
  ExternalLink,
  FileWarning,
  GitPullRequest,
  XCircle,
} from 'lucide-react'
import { useI18n } from '@/i18n/context'
import { formatDateTime } from '@/utils/dateFormat'

const API_BASE = '/api'

interface GateIssue {
  source?: string
  line?: number
  code?: string
  status?: string
  message?: string
}


interface GateReport {
  metadata?: {
    checked_file_count?: number
    record_count?: number
    issue_count?: number
    generated_at?: string
  }
  summary?: {
    status?: string
    by_status?: Record<string, number>
    by_code?: Record<string, number>
  }
  issues?: GateIssue[]
}

export default function Gate() {
  const [report, setReport] = useState<GateReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { t, getStatus } = useI18n()

  useEffect(() => {
    fetch(`${API_BASE}/gate`)
      .then(res => {
        if (!res.ok) throw new Error(`API error: ${res.status}`)
        return res.json()
      })
      .then(setReport)
      .catch(e => setError(e.message))
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

  if (!report) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    )
  }

  const meta = report.metadata || {}
  const summary = report.summary || {}
  const issues = report.issues || []
  const status = summary.status || 'unknown'
  const recordCount = meta.record_count || 0
  const issueCount = meta.issue_count || 0
  const checkedFileCount = meta.checked_file_count || 0


  // 按 code 分组
  const issuesByCode: Record<string, GateIssue[]> = {}
  for (const issue of issues) {
    const code = issue.code || 'unknown'
    if (!issuesByCode[code]) issuesByCode[code] = []
    issuesByCode[code].push(issue)
  }

  // 判断确认需求
  const confirmNeeded = issueCount > 0 || status === 'open'
  const needsHumanDecision = status === 'degraded' || recordCount === 0

  return (
    <div className="ldvh-page-frame space-y-6">
      <div className="ldvh-page-toolbar">
        <div>
          <PageHeader title={t('gate.title')} subtitle={t('gate.subtitle')} />

        </div>
        {meta.generated_at && (
          <span className="ldvh-meta truncate">
            {formatDateTime(meta.generated_at)}
          </span>
        )}
      </div>

      {/* 状态横幅 */}
      <StatusBanner
        status={status === 'closed' ? 'closed' as const : status === 'open' ? 'open' as const : 'degraded' as const}
        title={
          status === 'closed'
            ? t('gate.statusAllClear')
            : status === 'open'
            ? t('gate.statusNeedsConfirm')
            : t('gate.statusDegraded')
        }
        description={
          status === 'closed'
            ? t('gate.statusAllClearDesc')
            : status === 'open'
            ? t('gate.statusNeedsConfirmDesc')
            : t('gate.statusDegradedDesc', { count: String(issueCount) })
        }
      />

      {/* 摘要卡片 */}
      <div className="ldvh-metric-grid">
        <MetricCard
          icon={<FileWarning size={20} className="text-ldvh-text-secondary" />}
          value={checkedFileCount}
          label={t('gate.filesChecked')}
        />
        <MetricCard
          icon={<GitPullRequest size={20} className="text-sky-400" />}
          value={recordCount}
          label={t('gate.records')}
          tone={recordCount > 0 ? 'default' : 'default'}
        />
        <MetricCard
          icon={<AlertCircle size={20} className="text-red-400" />}
          value={issueCount}
          label={t('gate.issues')}
          tone={issueCount > 0 ? 'red' : 'green'}
        />
        <MetricCard
          icon={status === 'closed' ? <CheckCircle size={20} className="text-emerald-400" /> : <XCircle size={20} className="text-red-400" />}
          value={getStatus(status)}
          label={t('gate.status')}
          tone={status === 'closed' ? 'green' : status === 'open' ? 'red' : 'default'}
        />
      </div>

      {/* 确认面板 */}
      {confirmNeeded && (
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/10 p-5">
          <div className="mb-4 flex items-center gap-2">
            <ExternalLink size={16} className="text-sky-400" />
            <h2 className="ldvh-section-title">{t('gate.confirmPanel')}</h2>
          </div>
          <p className="ldvh-body-muted mb-4">{t('gate.confirmPanelDesc')}</p>

          {/* 按问题码分组展示 */}
          <div className="space-y-4">
            {Object.entries(issuesByCode).map(([code, codeIssues]) => {
              return (
                <ContentCard
                  key={code}
                  title={code}
                  headerExtra={<span className="ldvh-caption">{t('gate.codeCount', { count: String(codeIssues.length) })}</span>}
                >
                  <ul className="flex flex-col gap-2">
                    {codeIssues.map((issue, i) => (
                      <li key={i} className="rounded-md bg-ldvh-bg px-3 py-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="ldvh-meta">{issue.source}</span>
                          {issue.line && <span className="ldvh-meta">:{issue.line}</span>}
                        </div>
                        <p className="ldvh-body mt-1">{issue.message}</p>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-3 flex gap-2">
                    <button
                      disabled
                      className="ldvh-caption rounded-md border border-dashed border-ldvh-border px-3 py-1.5 opacity-60"
                      title={t('gate.confirmTitle')}
                    >
                      <CheckCircle size={14} className="inline-block" /> {t('gate.confirm')}
                    </button>
                    <button
                      disabled
                      className="ldvh-caption rounded-md border border-dashed border-ldvh-border px-3 py-1.5 opacity-60"
                      title={t('gate.deferTitle')}
                    >
                      <Clock size={14} className="inline-block" /> {t('gate.defer')}
                    </button>
                  </div>
                </ContentCard>
              )
            })}
          </div>
        </div>
      )}

      {/* 需要人工决策提示 */}
      {needsHumanDecision && !confirmNeeded && (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-5">
          <div className="flex items-start gap-3">
            <Clock size={18} className="mt-0.5 flex-shrink-0 text-yellow-400" />
            <div>
              <h3 className="ldvh-section-title">{t('gate.needsDecision')}</h3>
              <p className="ldvh-body-muted mt-1">{t('gate.needsDecisionDesc')}</p>
              <div className="ldvh-mini-grid mt-3">
                <div className="rounded-md bg-ldvh-panel p-2">
                  <p className="ldvh-meta-primary">{t('gate.records')}</p>
                  <p className="ldvh-caption">{recordCount}</p>
                </div>
                <div className="rounded-md bg-ldvh-panel p-2">
                  <p className="ldvh-meta-primary">{t('gt.filesChecked')}</p>
                  <p className="ldvh-caption">{checkedFileCount}</p>
                </div>
                <div className="rounded-md bg-ldvh-panel p-2">
                  <p className="ldvh-meta-primary">{t('gate.status')}</p>
                  <p className="ldvh-caption">{getStatus(status)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 全部通过 */}
      {status === 'closed' && (
        <div className="flex flex-col items-center justify-center py-12">
          <CheckCircle size={40} className="mb-3 text-emerald-400" />
          <p className="ldvh-body">{t('gate.allClear')}</p>
          <p className="ldvh-body-muted">{t('gate.allClearDesc')}</p>
        </div>
      )}
    </div>
  )
}
