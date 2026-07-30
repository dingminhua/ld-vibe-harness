/**
 * 项目认知中心（02 §3 / §4.1 / §5，第一期只建设模块一 待决定事项）。
 *
 * - 默认只读：不提供批准、关闭、分流、处置或任何写入口（02 §2.2 / §7.2）。
 * - 一切从既有字段派生：观察时间取 API generatedAt；模块标题带"派生视图"弱标签（02 §5.1）。
 * - 决定依据区与 WorkCase 列表 Card 同源消费（复用 ObjectList 导出的内容组件与
 *   projectWorkCaseCard 投影，Q3），不在本页另写摘要逻辑（02 §7.5）。
 * - 复制语义：条目级"复制对象路径"仅在字段级直读 read_status=readable 时显示（Q4）；
 *   "复制决定摘要 / 复制模块摘要"为面向 AI 对话的多行文本（02 §4.1 / §5.3）。
 * - 负担有界（H3）：超出首屏按服务端排序截断，底部如实提示总数与未显示数量，不分页。
 * - 模块级降级：issues 就地显示实际不可用范围与原因，其它内容正常呈现（02 §5.2）。
 */
import { useEffect, useState } from 'react';
import { AlertCircle, Inbox } from 'lucide-react';
import PageHeader from '@/components/PageHeader';
import CopyPathButton from '@/components/CopyPathButton';
import PriorityIcon from '@/components/PriorityIcon';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import {
  WorkCaseClosureConfirmationContent,
  WorkCasePlanConfirmationContent,
} from '@/pages/ObjectList';
import { fetchCognition, type CognitionData, type CognitionInboxItem, type CognitionInboxKind, type CognitionIssue } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { usePanel } from '@/utils/panelContext';
import { useI18n } from '@/i18n/context';
import { getFieldLabel, getFieldValueLabel, getLocalizedObjectTitle, type LocaleKey } from '@/i18n/locales';

/** 首屏截断阈值：Web 展示参数，不是事实；截断时底部如实提示总数与未显示数量。 */
const INBOX_FIRST_SCREEN_LIMIT = 8;

const INBOX_KIND_LABEL_KEYS: Record<CognitionInboxKind, LocaleKey> = {
  plan_confirmation: 'cognition.kind.plan_confirmation',
  closure_confirmation: 'cognition.kind.closure_confirmation',
};

/** 待决类型徽章：两个 Human Gate 均使用待确认紫色系。 */
const INBOX_KIND_BADGE_CLASS: Record<CognitionInboxKind, string> = {
  plan_confirmation: 'border-violet-400/30 bg-violet-500/10 text-violet-700/90 dark:text-violet-300/90',
  closure_confirmation: 'border-violet-400/30 bg-violet-500/10 text-violet-700/90 dark:text-violet-300/90',
};

type Translate = ReturnType<typeof useI18n>['t'];

function InboxKindBadge({ kind, t }: { kind: CognitionInboxKind; t: Translate }) {
  return (
    <span className={`ldvh-chip inline-flex shrink-0 items-center whitespace-nowrap rounded-full border px-2 py-0.5 ${INBOX_KIND_BADGE_CLASS[kind]}`}>
      {t(INBOX_KIND_LABEL_KEYS[kind])}
    </span>
  );
}

/** 面向 AI 对话的条目决定摘要：对象稳定 ID、待决类型、决定依据要点；readable 时含 canonical_path。 */
function buildDecisionSummary(item: CognitionInboxItem, generatedAt: string, locale: string, t: Translate): string {
  const lines: string[] = [];
  lines.push(`${item.id} · ${t(INBOX_KIND_LABEL_KEYS[item.inboxKind])} (${item.inboxKind})`);
  lines.push(getLocalizedObjectTitle(item, locale, item.id));
  if (item.inboxKind === 'plan_confirmation') {
    for (const [key, value] of [
      ['goal', item.card.goal],
      ['scope', item.card.scope],
      ['success_criterion_definitions', item.card.success_criterion_definitions],
      ['work_items', item.card.work_items],
      ['creation_reviews', item.card.creation_reviews],
      ['execution_authorization', item.card.execution_authorization],
      ['execution_approval', item.card.execution_approval],
    ] as Array<[string, unknown]>) {
      appendDecisionValue(lines, getFieldLabel(key, locale), value, locale);
    }
  } else if (item.inboxKind === 'closure_confirmation') {
    if (typeof item.card.goal === 'string' && item.card.goal.trim()) lines.push(`${getFieldLabel('goal', locale)}: ${item.card.goal}`);
    const proposal = item.card.closureProposal;
    if (proposal) {
      lines.push(`${getFieldLabel('proposed_outcome', locale)}: ${getFieldValueLabel('proposed_outcome', proposal.proposedOutcome, locale)} (${proposal.proposedOutcome})`);
      if (proposal.dispositionSummary.trim()) lines.push(proposal.dispositionSummary);
      for (const decision of proposal.residualDecisions) lines.push(`- [${decision.proposedDisposition}] ${decision.summary}`);
      for (const suggestion of proposal.sparkSuggestions) lines.push(`- [${suggestion.suggestionKind}] ${suggestion.summary}`);
    }
  }
  if (item.canonical_path) lines.push(`canonical_path: ${item.canonical_path}`);
  lines.push(t('cognition.observedAt', { time: formatDateTime(generatedAt) }));
  return lines.join('\n');
}

function appendDecisionValue(lines: string[], label: string, value: unknown, locale: string, indent = ''): void {
  if (value === undefined || value === null || value === '') {
    lines.push(`${indent}${label}: [${getFieldValueLabel('field_issue_reason', 'missing', locale)}]`);
    return;
  }
  if (Array.isArray(value)) {
    lines.push(`${indent}${label}:`);
    if (value.length === 0) lines.push(`${indent}- []`);
    for (const entry of value) appendDecisionValue(lines, '-', entry, locale, `${indent}  `);
    return;
  }
  if (typeof value === 'object') {
    lines.push(`${indent}${label}:`);
    for (const [key, entry] of Object.entries(value as Record<string, unknown>)) {
      appendDecisionValue(lines, getFieldLabel(key, locale), entry, locale, `${indent}  `);
    }
    return;
  }
  lines.push(`${indent}${label}: ${String(value)}`);
}

/** 面向 AI 对话的模块摘要：模块名、观察时间、关键计数与条目稳定 ID 列表（不含未精确读取的路径）。 */
function buildModuleSummary(data: CognitionData, locale: string, t: Translate): string {
  const lines: string[] = [];
  lines.push(t('cognition.inbox.title'));
  lines.push(t('cognition.observedAt', { time: formatDateTime(data.generatedAt) }));
  const counts: Record<CognitionInboxKind, number> = { plan_confirmation: 0, closure_confirmation: 0 };
  for (const item of data.inbox.items) counts[item.inboxKind] += 1;
  const countParts = (Object.keys(counts) as CognitionInboxKind[])
    .filter((kind) => counts[kind] > 0)
    .map((kind) => `${t(INBOX_KIND_LABEL_KEYS[kind])} ${counts[kind]}`);
  lines.push(`total: ${data.inbox.total}${countParts.length > 0 ? ` (${countParts.join(', ')})` : ''}`);
  for (const item of data.inbox.items) {
    lines.push(`- ${item.id} · ${t(INBOX_KIND_LABEL_KEYS[item.inboxKind])} · ${getLocalizedObjectTitle(item, locale, item.id)}`);
  }
  return lines.join('\n');
}

/** 读取问题与未解析结构在消费位置就地显示（02 §5.4）。 */
function InboxItemReadNotes({ item, locale }: { item: CognitionInboxItem; locale: string }) {
  const fieldIssues = item.field_issues ?? [];
  const unparsed = item.unparsed_structures ?? [];
  const showReadStatus = item.read_status !== 'readable';
  if (!showReadStatus && fieldIssues.length === 0 && unparsed.length === 0) return null;
  return (
    <div className="mt-2 grid min-w-0 gap-1">
      {showReadStatus && (
        <p className="ldvh-caption text-red-400">
          {getFieldLabel('read_status', locale)}: {getFieldValueLabel('read_status', item.read_status, locale)}
        </p>
      )}
      {fieldIssues.map((issue, index) => (
        <p key={`field-${index}`} className="ldvh-caption break-words text-red-400">
          {issue.path}: {getFieldValueLabel('field_issue_reason', issue.reason, locale)}
        </p>
      ))}
      {unparsed.map((structure, index) => (
        <p key={`unparsed-${index}`} className="ldvh-caption break-words text-amber-600 dark:text-amber-300">
          {structure.path}: {structure.reason}
        </p>
      ))}
    </div>
  );
}

function InboxDecisionBasis({ item, t }: { item: CognitionInboxItem; t: Translate }) {
  if (item.inboxKind === 'plan_confirmation') {
    return (
      <WorkCasePlanConfirmationContent
        goal={item.card.goal}
        scope={item.card.scope}
        successCriteria={item.card.successCriteria}
        successCriterionDefinitions={item.card.success_criterion_definitions}
        workItems={item.card.work_items}
        creationReviews={item.card.creation_reviews}
        executionAuthorization={item.card.execution_authorization}
        executionApproval={item.card.execution_approval}
        t={t}
      />
    );
  }
  if (item.inboxKind === 'closure_confirmation') {
    return <WorkCaseClosureConfirmationContent goal={item.card.goal} closureProposal={item.card.closureProposal} />;
  }
  return null;
}

function InboxItemRow({ item, generatedAt }: { item: CognitionInboxItem; generatedAt: string }) {
  const { t, locale } = useI18n();
  const { openPanel } = usePanel();
  const title = getLocalizedObjectTitle(item, locale, item.id);

  return (
    <li className="min-w-0 rounded-md border border-ldvh-border/70 bg-ldvh-bg/50 px-3 py-2.5">
      <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1.5">
        <span
          className="ldvh-chip inline-flex shrink-0 items-center gap-1.5 rounded px-1.5 py-0.5"
          style={{ backgroundColor: `${item.typeColor}20`, color: item.typeColor }}
        >
          <ObjectTypeIcon type="workcase" size={12} className="shrink-0" />
          {t('nav.workcases')}
        </span>
        <span className="ldvh-meta shrink-0 font-mono text-ldvh-text-secondary/60">{item.id}</span>
        <InboxKindBadge kind={item.inboxKind} t={t} />
        <PriorityIcon source={item} type="workcase" locale={locale} size="xs" />
        <span className="ldvh-caption ml-auto whitespace-nowrap">
          {item.updatedAt ? t('cognition.updatedAt', { time: formatDateTime(item.updatedAt) }) : null}
        </span>
        <span className="flex shrink-0 items-center">
          {/* Q4：仅精确读取取得可消费 canonical_path 的条目显示"复制对象路径" */}
          <CopyPathButton
            path={item.canonical_path}
            label={t('common.copyObjectPath')}
            copiedLabel={t('common.copiedObjectPath')}
          />
          <CopyPathButton
            path={buildDecisionSummary(item, generatedAt, locale, t)}
            label={t('cognition.copyDecisionSummary')}
            copiedLabel={t('cognition.copiedDecisionSummary')}
          />
        </span>
      </div>
      {/* 点击标题打开右侧扩展阅读（同源 WorkCaseReadingLayout）；标题以外区域不触发路由 */}
      <button
        type="button"
        onClick={() => openPanel({ type: 'object', title, objectType: 'workcase', objectId: item.id })}
        className="ldvh-body mt-1 flex w-full items-center rounded text-left transition-colors hover:text-ldvh-accent focus-visible:outline focus-visible:outline-1 focus-visible:outline-ldvh-accent/50"
      >
        <span className="min-w-0 break-words font-medium">{title}</span>
      </button>
      <div className="mt-2">
        <InboxDecisionBasis item={item} t={t} />
      </div>
      <InboxItemReadNotes item={item} locale={locale} />
    </li>
  );
}

function ModuleIssuesNotice({ issues, t }: { issues: CognitionIssue[]; t: Translate }) {
  if (issues.length === 0) return null;
  return (
    <div role="status" className="mb-3 min-w-0 rounded-md border border-red-400/25 border-l-2 border-l-red-400 bg-red-500/5 px-2.5 py-2">
      <p className="ldvh-caption text-red-500 dark:text-red-300">{t('cognition.inbox.unavailable')}</p>
      <ul className="mt-1 grid min-w-0 gap-0.5">
        {issues.map((issue, index) => (
          <li key={`${issue.code}-${index}`} className="ldvh-caption break-words text-red-400">
            [{issue.code}] {issue.message}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function CognitionCenter() {
  const [data, setData] = useState<CognitionData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const { t, locale } = useI18n();

  // 进入路由或切换语言触发新的直读请求，不复用旧 payload（02 §3）。
  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    fetchCognition(locale)
      .then((next) => {
        if (!cancelled) setData(next);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [locale]);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="text-ldvh-text-secondary">{t('common.loadFailed')}</p>
          <p className="ldvh-meta text-red-400">{error}</p>
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

  const observedAt = t('cognition.observedAt', { time: formatDateTime(data.generatedAt) });
  const inboxIssues = (data.issues ?? []).filter((issue) => issue.section === 'inbox');
  const items = data.inbox.items;
  const truncated = !showAll && items.length > INBOX_FIRST_SCREEN_LIMIT;
  const visibleItems = truncated ? items.slice(0, INBOX_FIRST_SCREEN_LIMIT) : items;

  return (
    <div className="p-4 sm:p-6">
      <PageHeader title={t('cognition.title')} subtitle={t('cognition.subtitle')} />
      <p className="ldvh-caption -mt-4 mb-4">{observedAt}</p>

      {/* 模块一 待决定事项：全宽主面板，置顶（02 §3） */}
      <section className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
        <div className="mb-3 flex min-w-0 flex-wrap items-center gap-2">
          <Inbox size={16} className="shrink-0 text-ldvh-accent" aria-hidden="true" />
          <h3 className="ldvh-section-title min-w-0">{t('cognition.inbox.title')}</h3>
          {data.inbox.total > 0 && (
            <span className="ldvh-meta shrink-0 text-ldvh-text-secondary/70">{data.inbox.total}</span>
          )}
          {/* 全局信任标记（02 §5.1 / §5.3）：派生视图弱标签 + 观察时间 + 复制模块摘要 */}
          <span className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
            <span className="ldvh-meta whitespace-nowrap rounded border border-ldvh-border/70 px-1.5 py-0.5 text-ldvh-text-secondary/60">
              {t('cognition.derivedView')}
            </span>
            <span className="ldvh-caption hidden whitespace-nowrap sm:inline">{observedAt}</span>
            <CopyPathButton
              path={buildModuleSummary(data, locale, t)}
              label={t('cognition.copyModuleSummary')}
              copiedLabel={t('cognition.copiedModuleSummary')}
            />
          </span>
        </div>

        <ModuleIssuesNotice issues={inboxIssues} t={t} />

        {items.length === 0 ? (
          inboxIssues.length === 0 && <p className="ldvh-body-muted">{t('cognition.inbox.empty')}</p>
        ) : (
          <ul className="ldvh-section-grid min-w-0">
            {visibleItems.map((item) => (
              <InboxItemRow key={item.id} item={item} generatedAt={data.generatedAt} />
            ))}
          </ul>
        )}

        {/* 负担有界（H3）：截断时如实提示总数与未显示数量，不用分页掩盖待决规模 */}
        {items.length > INBOX_FIRST_SCREEN_LIMIT && (
          <div className="mt-3 flex min-w-0 flex-wrap items-center justify-between gap-2">
            <p className="ldvh-caption min-w-0">
              {truncated
                ? t('cognition.inbox.truncated', {
                  total: String(data.inbox.total),
                  shown: String(visibleItems.length),
                  hidden: String(items.length - visibleItems.length),
                })
                : null}
            </p>
            <button
              type="button"
              onClick={() => setShowAll((prev) => !prev)}
              className="ldvh-caption inline-flex h-8 shrink-0 items-center rounded-md border border-ldvh-border px-3 text-ldvh-text-secondary transition-colors hover:border-ldvh-accent/50 hover:text-ldvh-accent"
            >
              {truncated ? t('cognition.inbox.showAll') : t('cognition.inbox.collapse')}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
