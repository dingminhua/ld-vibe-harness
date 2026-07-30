/**
 * 项目认知中心（02 §3 / §4.1 / §5，第一期只建设模块一 待决定事项）。
 *
 * - 默认只读：不提供批准、关闭、分流、处置或任何写入口（02 §2.2 / §7.2）。
 * - 一切从既有字段派生：观察时间取 API generatedAt；模块标题带"派生视图"弱标签（02 §5.1）。
 * - 决定依据区与 WorkCase 列表 Card 同源消费（复用 ObjectList 导出的内容组件与
 *   projectWorkCaseCard 投影，Q3），不在本页另写摘要逻辑（02 §7.5）。
 * - 复制语义：模块级"复制模块摘要"为面向 AI 对话的多行文本；条目本身不叠加聚焦页专属操作，
 *   保持与对象列表 Card 相同的可读形态（02 §4.1 / §5.3）。
 * - 负担有界（H3）：超出首屏按服务端排序截断，底部如实提示总数与未显示数量，不分页。
 * - 模块级降级：issues 就地显示实际不可用范围与原因，其它内容正常呈现（02 §5.2）。
 */
import { useEffect, useState } from 'react';
import { AlertCircle, ChevronDown, ChevronUp, Inbox } from 'lucide-react';
import PageHeader from '@/components/PageHeader';
import CopyPathButton from '@/components/CopyPathButton';
import {
  ObjectCardFrame,
  WorkCaseContributionsContent,
  WorkCaseClosureConfirmationContent,
  WorkCasePlanConfirmationContent,
} from '@/pages/ObjectList';
import { fetchCognition, type CognitionData, type CognitionInboxItem, type CognitionInboxKind, type CognitionIssue, type ObjectItem } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { usePanel } from '@/utils/panelContext';
import { useI18n } from '@/i18n/context';
import { getFieldLabel, getFieldValueLabel, getLocalizedObjectTitle, type LocaleKey } from '@/i18n/locales';

/** 首屏截断阈值：Web 展示参数，不是事实；截断时底部如实提示总数与未显示数量。 */
const INBOX_FIRST_SCREEN_LIMIT = 8;

const INBOX_KIND_LABEL_KEYS: Record<CognitionInboxKind, LocaleKey> = {
  plan_confirmation: 'cognition.kind.plan_confirmation',
  closure_confirmation: 'cognition.kind.closure_confirmation',
  pitfall_confirmation: 'cognition.kind.pitfall_confirmation',
};

type Translate = ReturnType<typeof useI18n>['t'];

/** 面向 AI 对话的模块摘要：模块名、观察时间、关键计数与条目稳定 ID 列表（不含未精确读取的路径）。 */
function buildModuleSummary(data: CognitionData, locale: string, t: Translate): string {
  const lines: string[] = [];
  lines.push(t('cognition.inbox.title'));
  lines.push(t('cognition.observedAt', { time: formatDateTime(data.generatedAt) }));
  const counts: Record<CognitionInboxKind, number> = { plan_confirmation: 0, closure_confirmation: 0, pitfall_confirmation: 0 };
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

function InboxCardContent({ item, t, locale }: { item: CognitionInboxItem; t: Translate; locale: string }) {
  if (item.type === 'workcase' && item.inboxKind === 'plan_confirmation') {
    return (
      <WorkCasePlanConfirmationContent
        mode="card"
        goal={item.card.goal}
        successCriteria={item.card.successCriteria}
        successCriterionDefinitions={item.card.success_criterion_definitions}
        executionAuthorization={item.card.execution_authorization}
        t={t}
      />
    );
  }
  if (item.type === 'workcase' && item.inboxKind === 'closure_confirmation') {
    return (
      <>
        <WorkCaseClosureConfirmationContent goal={item.card.goal} closureProposal={item.card.closureProposal} />
        <WorkCaseContributionsContent contributions={item.card.contributedTo} locale={locale} />
      </>
    );
  }
  return null;
}

function toObjectCard(item: CognitionInboxItem): ObjectItem {
  return {
    ...(item.card as unknown as ObjectItem),
    id: item.id,
    type: item.type,
    title: item.title,
    ...(item.title_en ? { title_en: item.title_en } : {}),
    ...(item.title_zh ? { title_zh: item.title_zh } : {}),
    status: item.type === 'workcase' ? item.progress_group : item.status,
    ...(item.type === 'workcase' ? { progress_group: item.progress_group } : {}),
    path: item.canonical_path ?? '',
    updated: item.updatedAt ?? '',
    ...(item.priority ? { priority: item.priority } : {}),
    object_id: item.id,
    fact_type_key: item.type,
    ...(item.canonical_path ? { canonical_path: item.canonical_path } : {}),
    read_status: item.read_status as ObjectItem['read_status'],
  };
}

function InboxItemRow({ item }: { item: CognitionInboxItem }) {
  const { t, locale } = useI18n();
  const { openPanel } = usePanel();
  const title = getLocalizedObjectTitle(item, locale, item.id);
  const objectCard = toObjectCard(item);

  return (
    <li className="min-w-0">
      <ObjectCardFrame
        obj={objectCard}
        locale={locale}
        onOpen={() => openPanel({ type: 'object', title, objectType: item.type, objectId: item.id })}
      >
        <InboxCardContent item={item} t={t} locale={locale} />
        <InboxItemReadNotes item={item} locale={locale} />
      </ObjectCardFrame>
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
  const [inboxExpanded, setInboxExpanded] = useState(true);
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

      {/* 模块一 待决定事项：全宽主面板，置顶（02 §3） */}
      <section className="rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
        <div className={`flex min-w-0 flex-wrap items-center gap-2 ${inboxExpanded ? 'mb-4' : ''}`}>
          <Inbox size={16} className="shrink-0 text-ldvh-accent" aria-hidden="true" />
          <h3 className="ldvh-section-title min-w-0">{t('cognition.inbox.title')}</h3>
          {data.inbox.total > 0 && (
            <span className="ldvh-meta shrink-0 text-ldvh-text-secondary/70">{data.inbox.total}</span>
          )}
          {/* 全局信任标记（02 §5.1 / §5.3）：观察时间 + 复制模块摘要 */}
          <span className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
            <span className="ldvh-caption hidden whitespace-nowrap sm:inline">{observedAt}</span>
            <CopyPathButton
              path={buildModuleSummary(data, locale, t)}
              label={t('cognition.copyModuleSummary')}
              copiedLabel={t('cognition.copiedModuleSummary')}
            />
            <button
              type="button"
              aria-expanded={inboxExpanded}
              aria-controls="cognition-inbox-content"
              onClick={() => setInboxExpanded((expanded) => !expanded)}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-bg hover:text-ldvh-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50"
              title={t(inboxExpanded ? 'cognition.inbox.collapseSection' : 'cognition.inbox.expandSection')}
            >
              {inboxExpanded ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
              <span className="sr-only">{t(inboxExpanded ? 'cognition.inbox.collapseSection' : 'cognition.inbox.expandSection')}</span>
            </button>
          </span>
        </div>

        {inboxExpanded && (
          <div id="cognition-inbox-content">
            <ModuleIssuesNotice issues={inboxIssues} t={t} />

            {items.length === 0 ? (
              inboxIssues.length === 0 && <p className="ldvh-body-muted">{t('cognition.inbox.empty')}</p>
            ) : (
              <ul className="ldvh-section-grid min-w-0">
                {visibleItems.map((item) => (
                  <InboxItemRow key={item.id} item={item} />
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
          </div>
        )}
      </section>
    </div>
  );
}
