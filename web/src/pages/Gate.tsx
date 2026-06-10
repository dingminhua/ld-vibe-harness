import MetricCard from '@/components/MetricCard';
import StatusBanner from '@/components/StatusBanner';
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

function dateText(value?: string): string {
  if (!value) return '—'
  return value.replace('T', ' ').slice(0, 16)
}




export default function Gate() {
  const [report, setReport] = useState<GateReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { t } = useI18n()

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
          <p className="text-ldvh-text-secondary">{t('common.loadFailed')}</p>
          <p className="font-mono text-xs text-red-400">{error}</p>
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
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-ldvh-text-primary">{t('gate.title')}</h1>
          <p className="mt-1 text-sm text-ldvh-text-secondary">{t('gate.subtitle')}</p>
        </div>
        {meta.generated_at && (
          <span className="truncate font-mono text-xs text-ldvh-text-secondary">
            {dateText(meta.generated_at)}
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
      <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
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
          value={status}
          label={t('gate.status')}
          tone={status === 'closed' ? 'green' : status === 'open' ? 'red' : 'default'}
        />
      </div>

      {/* 确认面板 */}
      {confirmNeeded && (
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/10 p-5">
          <div className="mb-4 flex items-center gap-2">
            <ExternalLink size={16} className="text-sky-400" />
            <h2 className="text-sm font-semibold text-ldvh-text-primary">{t('gate.confirmPanel')}</h2>
          </div>
          <p className="mb-4 text-sm text-ldvh-text-secondary">{t('gate.confirmPanelDesc')}</p>

          {/* 按问题码分组展示 */}
          {Object.entries(issuesByCode).map(([code, codeIssues]) => {
            return (
              <div key={code} className="mb-4 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 last:mb-0">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-red-500/20 px-2 py-0.5 font-mono text-xs text-red-300">{code}</span>
                    <span className="text-sm text-ldvh-text-secondary">{t('gate.codeCount', { count: String(codeIssues.length) })}</span>
                  </div>
                </div>
                <ul className="flex flex-col gap-2">
                  {codeIssues.map((issue, i) => (
                    <li key={i} className="rounded-md bg-ldvh-bg px-3 py-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs text-ldvh-text-secondary">{issue.source}</span>
                        {issue.line && <span className="font-mono text-xs text-ldvh-text-secondary">:{issue.line}</span>}
                      </div>
                      <p className="mt-1 text-sm text-ldvh-text-primary">{issue.message}</p>
                    </li>
                  ))}
                </ul>
                <div className="mt-3 flex gap-2">
                  <button
                    disabled
                    className="rounded-md border border-dashed border-ldvh-border px-3 py-1.5 text-xs text-ldvh-text-secondary opacity-60"
                    title={t('gate.confirmTitle')}
                  >
                    <CheckCircle size={14} className="inline-block" /> {t('gate.confirm')}
                  </button>
                  <button
                    disabled
                    className="rounded-md border border-dashed border-ldvh-border px-3 py-1.5 text-xs text-ldvh-text-secondary opacity-60"
                    title={t('gate.deferTitle')}
                  >
                    <Clock size={14} className="inline-block" /> {t('gate.defer')}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* 需要人工决策提示 */}
      {needsHumanDecision && !confirmNeeded && (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-5">
          <div className="flex items-start gap-3">
            <Clock size={18} className="mt-0.5 flex-shrink-0 text-yellow-400" />
            <div>
              <h3 className="text-sm font-semibold text-ldvh-text-primary">{t('gate.needsDecision')}</h3>
              <p className="mt-1 text-sm text-ldvh-text-secondary">{t('gate.needsDecisionDesc')}</p>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-3">
                <div className="rounded-md bg-ldvh-panel p-2">
                  <p className="font-mono text-ldvh-text-primary">Human Gate 记录</p>
                  <p className="text-ldvh-text-secondary">{recordCount}</p>
                </div>
                <div className="rounded-md bg-ldvh-panel p-2">
                  <p className="font-mono text-ldvh-text-primary">检查文件</p>
                  <p className="text-ldvh-text-secondary">{checkedFileCount}</p>
                </div>
                <div className="rounded-md bg-ldvh-panel p-2">
                  <p className="font-mono text-ldvh-text-primary">状态</p>
                  <p className="text-ldvh-text-secondary">{status}</p>
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
          <p className="text-ldvh-text-primary">{t('gate.allClear')}</p>
          <p className="text-sm text-ldvh-text-secondary">{t('gate.allClearDesc')}</p>
        </div>
      )}
    </div>
  )
}
