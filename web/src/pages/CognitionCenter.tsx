/**
 * 项目认知中心（02 §3 / §4.1 / §4.2 / §5）。
 *
 * - 默认只读：不提供批准、关闭、分流、处置或任何写入口（02 §2.2 / §7.2）。
 * - 一切从既有字段派生：近期动态只标记 created_at / updated_at（02 §5.1）。
 * - 决定依据区与 WorkCase 列表 Card 同源消费（复用 ObjectList 导出的内容组件与
 *   source-bound WorkCase Card 投影，Q3），不在本页另写摘要逻辑（02 §7.5）。
 * - 复制语义：模块级"复制模块摘要"为面向 AI 对话的多行文本；条目本身不叠加聚焦页专属操作，
 *   保持与对象列表 Card 相同的可读形态（02 §4.1 / §5.3）。
 * - 待决规模如实可见：超出首屏按服务端排序截断，底部如实提示总数与未显示数量，不分页。
 * - 模块级降级：issues 就地显示实际不可用范围与原因，其它内容正常呈现（02 §5.2）。
 */
import { useEffect, useState, type KeyboardEvent } from 'react';
import { AlertCircle, ChevronDown, ChevronUp, CirclePlay, GitFork, HeartPulse, History, Inbox } from 'lucide-react';
import PageHeader from '@/components/PageHeader';
import CopyPathButton from '@/components/CopyPathButton';
import {
  ObjectCardFrame,
  PitfallCardContent,
  WorkCaseBlockingNotice,
  WorkCaseContributionsContent,
  WorkCaseClosureConfirmationContent,
  WorkCasePlanConfirmationContent,
  WorkCaseProgressingContent,
} from '@/pages/ObjectList';
import StatusBadge from '@/components/StatusBadge';
import PriorityIcon from '@/components/PriorityIcon';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { CommitHotspotCluster, CommitHotspotLegend } from '@/pages/cognition/CommitHotspotGraph';
import {
  fetchCognition,
  type CognitionActiveWorkCaseItem,
  type CognitionCommitHotspotNode,
  type CognitionData,
  type CognitionInboxItem,
  type CognitionInboxKind,
  type CognitionIssue,
  type CognitionRecentActivityItem,
  type CognitionRecentActivityWindow,
  type CognitionSparkHealthItem,
  type ObjectItem,
} from '@/utils/api';
import { usePanel } from '@/utils/panelContext';
import { useI18n } from '@/i18n/context';
import { getFieldLabel, getFieldValueLabel, getLocalizedObjectTitle, getObjectStatusLocale, type LocaleKey } from '@/i18n/locales';

/** 首屏截断阈值：Web 展示参数，不是事实；截断时底部如实提示总数与未显示数量。 */
const INBOX_FIRST_SCREEN_LIMIT = 8;
const ACTIVE_WORKCASE_FIRST_SCREEN_LIMIT = 8;
const RECENT_ACTIVITY_FIRST_SCREEN_LIMIT = 12;
const SPARK_HEALTH_FIRST_SCREEN_LIMIT = 3;
const SPARK_PRIORITIES = ['P0', 'P1', 'P2', 'P3'];

const RECENT_ACTIVITY_WINDOWS: CognitionRecentActivityWindow[] = ['1d', '3d', '7d', '14d'];

type CommitHotspotStatusFilter = 'all' | 'progressing' | 'decision' | 'settled';

const COMMIT_HOTSPOT_STATUS_FILTERS: CommitHotspotStatusFilter[] = ['all', 'progressing', 'decision', 'settled'];
const COMMIT_HOTSPOT_TERMINAL_STATUSES: Record<string, Set<string>> = {
  workcase: new Set(['closed']),
  adr: new Set(['retired']),
  pitfall: new Set(['discarded']),
  spark: new Set(['routed', 'implemented', 'discarded']),
  study: new Set(['retired']),
};

function getCommitHotspotStatusGroup(node: CognitionCommitHotspotNode): Exclude<CommitHotspotStatusFilter, 'all'> {
  if (node.type === 'workcase') {
    if (node.progress_group === 'plan_confirmation' || node.progress_group === 'closure_confirmation') return 'decision';
    if (node.progress_group === 'closed') return 'settled';
    return 'progressing';
  }
  if (node.type === 'pitfall' && node.status === 'draft') return 'decision';
  if (node.status && COMMIT_HOTSPOT_TERMINAL_STATUSES[node.type]?.has(node.status)) return 'settled';
  return 'progressing';
}

const INBOX_KIND_LABEL_KEYS: Record<CognitionInboxKind, LocaleKey> = {
  plan_confirmation: 'cognition.kind.plan_confirmation',
  closure_confirmation: 'cognition.kind.closure_confirmation',
  blocked_resolution: 'cognition.kind.blocked_resolution',
  pitfall_confirmation: 'cognition.kind.pitfall_confirmation',
};

type Translate = ReturnType<typeof useI18n>['t'];

/** 面向 AI 对话的模块摘要：模块名、关键计数与条目稳定 ID 列表（不含未精确读取的路径）。 */
function buildModuleSummary(data: CognitionData, locale: string, t: Translate): string {
  const lines: string[] = [];
  lines.push(t('cognition.inbox.title'));
  const counts: Record<CognitionInboxKind, number> = {
    plan_confirmation: 0,
    closure_confirmation: 0,
    blocked_resolution: 0,
    pitfall_confirmation: 0,
  };
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

function buildRecentActivitySummary(data: CognitionData, locale: string, t: Translate): string {
  const recent = data.recentActivity;
  const lines = [
    t('cognition.recent.title'),
    t(`cognition.recent.window.${recent.window}` as LocaleKey),
    `total: ${recent.total}`,
  ];
  for (const item of recent.items) {
    lines.push(`- ${item.id} · ${t(`cognition.recent.${item.activity}` as LocaleKey)} · ${getLocalizedObjectTitle(item, locale, item.id)}`);
  }
  return lines.join('\n');
}

function buildActiveWorkCaseSummary(data: CognitionData, locale: string, t: Translate): string {
  const lines = [t('cognition.active.title'), `total: ${data.activeWorkCases.total}`];
  for (const item of data.activeWorkCases.items) {
    lines.push(`- ${item.id} · ${getLocalizedObjectTitle(item, locale, item.id)}`);
  }
  return lines.join('\n');
}

function buildSparkHealthSummary(data: CognitionData, locale: string, t: Translate): string {
  const health = data.sparkHealth;
  if (!health) return t('cognition.sparkHealth.title');
  const terminal = (['routed', 'implemented', 'discarded'] as const)
    .filter((status) => health.terminalByStatus[status] > 0)
    .map((status) => `${getObjectStatusLocale('spark', status, locale)} ${health.terminalByStatus[status]}`)
    .join(', ');
  const lines = [
    t('cognition.sparkHealth.title'),
    `${t('cognition.sparkHealth.settled', { count: String(health.terminalTotal) })}${terminal ? ` (${terminal})` : ''}`,
    t('cognition.sparkHealth.pending', { count: String(health.openTotal) }),
    t('cognition.sparkHealth.silentSummary', { count: String(health.silentCount), days: String(health.silentThresholdDays) }),
  ];
  for (const item of health.silentItems) {
    lines.push(`- ${item.id} · ${t('cognition.sparkHealth.silentDays', { days: String(item.silentDays) })} · ${getLocalizedObjectTitle(item, locale, item.id)}`);
  }
  return lines.join('\n');
}

function buildCommitHotspotSummary(data: CognitionData, locale: string, t: Translate): string {
  const hotspots = data.commitHotspots;
  if (!hotspots) return t('cognition.commitHotspots.title');
  const lines = [
    t('cognition.commitHotspots.title'),
    t(`cognition.recent.window.${hotspots.window}` as LocaleKey),
    t('cognition.commitHotspots.totalCommits', { count: String(hotspots.totalCommits) }),
    t('cognition.commitHotspots.summary', { hotspots: String(hotspots.hotspotTotal), relations: String(hotspots.relationTotal) }),
  ];
  for (const cluster of hotspots.clusters) {
    const item = cluster.primary;
    lines.push(`- ${item.id} · ${item.commitRefs.length} · ${getLocalizedObjectTitle(item, locale, item.id)}`);
  }
  return lines.join('\n');
}

/** 读取问题与未解析结构在消费位置就地显示（02 §5.4）。 */
type CognitionCardItem = CognitionInboxItem | CognitionActiveWorkCaseItem;

function InboxItemReadNotes({ item, locale }: { item: CognitionCardItem; locale: string }) {
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
  if (item.type === 'pitfall') return <PitfallCardContent obj={toObjectCard(item)} />;
  if (item.inboxKind === 'blocked_resolution') {
    return (
      <div className="grid min-w-0 gap-2">
        <WorkCaseBlockingNotice blockingSummary={item.card.blocking_summary} t={t} />
        <section className="min-w-0 rounded-md border border-amber-400/25 border-l-2 border-l-amber-400 bg-amber-500/[0.035] px-3.5 py-3">
          <h3 className="ldvh-card-decision-title text-amber-700/85 dark:text-amber-200/85">
            {t('cognition.kind.blocked_resolution')}
          </h3>
          <p className="ldvh-card-decision-body mt-1.5 text-amber-950/70 dark:text-amber-100/75">
            {t('cognition.blocked.position', {
              position: getObjectStatusLocale('workcase', item.progress_group, locale),
            })}
          </p>
        </section>
      </div>
    );
  }
  if (item.inboxKind === 'plan_confirmation') {
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
  if (item.inboxKind === 'closure_confirmation') {
    return (
      <>
        <WorkCaseClosureConfirmationContent goal={item.card.goal} closureProposal={item.card.closureProposal} />
        <WorkCaseContributionsContent contributions={item.card.contributedTo} locale={locale} />
      </>
    );
  }
  return null;
}

function toObjectCard(item: CognitionCardItem): ObjectItem {
  return {
    ...(item.card as unknown as ObjectItem),
    id: item.id,
    type: item.type,
    title: item.title,
    ...(item.title_en ? { title_en: item.title_en } : {}),
    ...(item.title_zh ? { title_zh: item.title_zh } : {}),
    status: item.type === 'workcase'
      ? item.isBlocked ? 'blocked' : item.progress_group
      : item.status,
    ...(item.type === 'workcase' ? { progress_group: item.progress_group } : {}),
    ...(item.type === 'workcase' ? {
      lifecycle_position: item.lifecycle_position,
      ...('progress_step' in item && item.progress_step ? { progress_step: item.progress_step } : {}),
    } : {}),
    path: item.canonical_path ?? '',
    updated: item.updatedAt ?? '',
    ...(item.priority ? { priority: item.priority } : {}),
    object_id: item.id,
    fact_type_key: item.type,
    ...(item.canonical_path ? { canonical_path: item.canonical_path } : {}),
    read_status: item.read_status as ObjectItem['read_status'],
  };
}

function ActiveWorkCaseItemRow({ item }: { item: CognitionActiveWorkCaseItem }) {
  const { t, locale } = useI18n();
  const { openPanel } = usePanel();
  const title = getLocalizedObjectTitle(item, locale, item.id);
  const objectCard = toObjectCard(item);

  return (
    <li className="min-w-0">
      <ObjectCardFrame
        obj={objectCard}
        locale={locale}
        onOpen={() => openPanel({ type: 'object', title, objectType: 'workcase', objectId: item.id })}
        showNonActiveReason={false}
        displayStatus="progressing"
      >
        <WorkCaseProgressingContent
          goal={item.card.goal}
          lifecyclePosition={item.lifecycle_position}
          progressStep={item.progress_step ?? null}
          executionItemsProjectionValid={item.card.executionItemsProjectionValid ?? false}
          executionItems={item.card.executionItems ?? []}
          isBlocked={item.isBlocked}
          waitingOn={item.card.waiting_on}
          blockingSummary={item.card.blocking_summary}
          t={t}
        />
        <InboxItemReadNotes item={item} locale={locale} />
      </ObjectCardFrame>
    </li>
  );
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
        displayStatus={item.type === 'workcase' && item.inboxKind === 'blocked_resolution' ? 'blocked' : undefined}
      >
        <InboxCardContent item={item} t={t} locale={locale} />
        <InboxItemReadNotes item={item} locale={locale} />
      </ObjectCardFrame>
    </li>
  );
}

function ModuleIssuesNotice({ issues, t, unavailableKey = 'cognition.inbox.unavailable' }: { issues: CognitionIssue[]; t: Translate; unavailableKey?: LocaleKey }) {
  if (issues.length === 0) return null;
  return (
    <div role="status" className="mb-3 min-w-0 rounded-md border border-red-400/25 border-l-2 border-l-red-400 bg-red-500/5 px-2.5 py-2">
      <p className="ldvh-caption text-red-500 dark:text-red-300">{t(unavailableKey)}</p>
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

function RecentActivityReadNotes({ item, locale }: { item: CognitionRecentActivityItem; locale: string }) {
  const fieldIssues = item.field_issues ?? [];
  const unparsed = item.unparsed_structures ?? [];
  if (item.read_status === 'readable' && fieldIssues.length === 0 && unparsed.length === 0) return null;
  return (
    <div className="mt-1.5 grid min-w-0 gap-1">
      {item.read_status !== 'readable' && (
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

function RecentActivityRow({ item }: { item: CognitionRecentActivityItem }) {
  const { t, locale } = useI18n();
  const { openPanel } = usePanel();
  const title = getLocalizedObjectTitle(item, locale, item.id);
  const status = item.type === 'workcase' ? item.progress_group : item.status;
  const activityTone = item.activity === 'created'
    ? 'text-emerald-700/80 dark:text-emerald-300/80'
    : 'text-sky-700/80 dark:text-sky-300/80';

  return (
    <li className="min-w-0 py-3">
      <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
        <span className="ldvh-caption shrink-0 text-ldvh-text-secondary">{item.relativeTime}</span>
        <span className={`ldvh-caption shrink-0 ${activityTone}`}>{t(`cognition.recent.${item.activity}` as LocaleKey)}</span>
        <code className="ldvh-caption min-w-0 break-all text-ldvh-text-secondary/55">{item.id}</code>
        <PriorityIcon source={item} type={item.type} locale={locale} size="sm" />
        <span className="ml-auto flex shrink-0 items-center gap-1.5">
          {status && <StatusBadge status={status} statusLabel={getObjectStatusLocale(item.type, status, locale)} objectType={item.type} />}
          <CopyPathButton path={item.id} label={t('common.copyObjectId')} copiedLabel={t('common.copiedObjectId')} />
        </span>
      </div>
      <div className="mt-2 flex min-w-0 items-center gap-1.5">
        <ObjectTypeIcon type={item.type} size={15} className="shrink-0" style={{ color: item.typeColor }} />
        <h4 className="ldvh-card-title min-w-0 flex-1 whitespace-normal break-words">
          <button
            type="button"
            onClick={() => openPanel({ type: 'object', title, objectType: item.type, objectId: item.id })}
            className="text-left transition-colors hover:text-ldvh-accent focus-visible:outline-none focus-visible:text-ldvh-accent focus-visible:underline"
          >
            {title}
          </button>
        </h4>
      </div>
      <RecentActivityReadNotes item={item} locale={locale} />
    </li>
  );
}

function SparkHealthRow({ item }: { item: CognitionSparkHealthItem }) {
  const { t, locale } = useI18n();
  const { openPanel } = usePanel();
  const title = getLocalizedObjectTitle(item, locale, item.id);
  const fieldIssues = item.field_issues ?? [];
  const unparsed = item.unparsed_structures ?? [];
  const showReadNotes = item.read_status !== 'readable' || fieldIssues.length > 0 || unparsed.length > 0;
  return (
    <li className="min-w-0 py-3">
      <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
        <span className="ldvh-caption shrink-0 text-amber-700/85 dark:text-amber-300/85">
          {t('cognition.sparkHealth.silentDays', { days: String(item.silentDays) })}
        </span>
        <code className="ldvh-caption min-w-0 break-all text-ldvh-text-secondary/55">{item.id}</code>
        <PriorityIcon source={item} type="spark" locale={locale} size="sm" />
        <span className="ml-auto shrink-0">
          <CopyPathButton path={item.id} label={t('common.copyObjectId')} copiedLabel={t('common.copiedObjectId')} />
        </span>
      </div>
      <div className="mt-2 flex min-w-0 items-center gap-1.5">
        <ObjectTypeIcon type="spark" size={15} className="shrink-0" style={{ color: item.typeColor }} />
        <h4 className="ldvh-card-title min-w-0 flex-1 whitespace-normal break-words">
          <button
            type="button"
            onClick={() => openPanel({ type: 'object', title, objectType: 'spark', objectId: item.id })}
            className="text-left transition-colors hover:text-ldvh-accent focus-visible:outline-none focus-visible:text-ldvh-accent focus-visible:underline"
          >
            {title}
          </button>
        </h4>
      </div>
      {showReadNotes && <div className="mt-1.5 grid min-w-0 gap-1">
        {item.read_status !== 'readable' && (
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
      </div>}
    </li>
  );
}

function toggleOnKeyboard(event: KeyboardEvent<HTMLDivElement>, toggle: () => void) {
  if (event.key !== 'Enter' && event.key !== ' ') return;
  event.preventDefault();
  toggle();
}

export default function CognitionCenter() {
  const [data, setData] = useState<CognitionData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [inboxExpanded, setInboxExpanded] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [activeExpanded, setActiveExpanded] = useState(true);
  const [showAllActive, setShowAllActive] = useState(false);
  const [recentWindow, setRecentWindow] = useState<CognitionRecentActivityWindow>('1d');
  const [recentExpanded, setRecentExpanded] = useState(true);
  const [showAllRecent, setShowAllRecent] = useState(false);
  const [recentLoading, setRecentLoading] = useState(false);
  const [recentError, setRecentError] = useState<string | null>(null);
  const [sparkHealthExpanded, setSparkHealthExpanded] = useState(true);
  const [showAllSilentSpark, setShowAllSilentSpark] = useState(false);
  const [commitHotspotsExpanded, setCommitHotspotsExpanded] = useState(true);
  const [expandedHotspotKey, setExpandedHotspotKey] = useState<string | null>(null);
  const [commitHotspotStatusFilter, setCommitHotspotStatusFilter] = useState<CommitHotspotStatusFilter>('progressing');
  const { t, locale } = useI18n();

  // 首次进入才阻塞整页；切换近期窗口保留当前内容，只在本模块内更新快照。
  useEffect(() => {
    let cancelled = false;
    const hasCurrentData = data !== null;
    setError(null);
    setRecentError(null);
    if (hasCurrentData) setRecentLoading(true);
    fetchCognition(locale, recentWindow)
      .then((next) => {
        if (!cancelled) {
          setData(next);
          setRecentLoading(false);
        }
      })
      .catch((e: Error) => {
        if (!cancelled) {
          setRecentLoading(false);
          if (hasCurrentData) setRecentError(e.message);
          else setError(e.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [locale, recentWindow]);

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

  const inboxIssues = (data.issues ?? []).filter((issue) => issue.section === 'inbox');
  const items = data.inbox.items;
  const truncated = !showAll && items.length > INBOX_FIRST_SCREEN_LIMIT;
  const visibleItems = truncated ? items.slice(0, INBOX_FIRST_SCREEN_LIMIT) : items;
  const activeWorkCaseIssues = (data.issues ?? []).filter((issue) => issue.section === 'activeWorkCases');
  const activeWorkCaseItems = data.activeWorkCases.items;
  const activeWorkCasesTruncated = !showAllActive && activeWorkCaseItems.length > ACTIVE_WORKCASE_FIRST_SCREEN_LIMIT;
  const visibleActiveWorkCases = activeWorkCasesTruncated
    ? activeWorkCaseItems.slice(0, ACTIVE_WORKCASE_FIRST_SCREEN_LIMIT)
    : activeWorkCaseItems;
  const recentIssues = (data.issues ?? []).filter((issue) => issue.section === 'recentActivity');
  const recentItems = data.recentActivity.items;
  const recentTruncated = !showAllRecent && recentItems.length > RECENT_ACTIVITY_FIRST_SCREEN_LIMIT;
  const visibleRecentItems = recentTruncated ? recentItems.slice(0, RECENT_ACTIVITY_FIRST_SCREEN_LIMIT) : recentItems;
  const sparkHealth = data.sparkHealth;
  const sparkHealthIssues = (data.issues ?? []).filter((issue) => issue.section === 'sparkHealth');
  const silentSparkItems = sparkHealth?.silentItems ?? [];
  const silentSparkTruncated = !showAllSilentSpark && silentSparkItems.length > SPARK_HEALTH_FIRST_SCREEN_LIMIT;
  const visibleSilentSparkItems = silentSparkTruncated ? silentSparkItems.slice(0, SPARK_HEALTH_FIRST_SCREEN_LIMIT) : silentSparkItems;
  const settledRatio = sparkHealth && sparkHealth.total > 0 ? (sparkHealth.terminalTotal / sparkHealth.total) * 100 : 0;
  const terminalDetail = sparkHealth
    ? (['routed', 'implemented', 'discarded'] as const)
      .filter((status) => sparkHealth.terminalByStatus[status] > 0)
      .map((status) => `${getObjectStatusLocale('spark', status, locale)} ${sparkHealth.terminalByStatus[status]}`)
      .join(' · ')
    : '';
  const openPriorityDetail = sparkHealth
    ? SPARK_PRIORITIES
      .filter((priority) => (sparkHealth.openByPriority[priority] ?? 0) > 0)
      .map((priority) => `${priority} × ${sparkHealth.openByPriority[priority]}`)
      .join(' / ')
    : '';
  const commitHotspots = data.commitHotspots;
  const commitHotspotIssues = (data.issues ?? []).filter((issue) => issue.section === 'commitHotspots');
  const filteredCommitHotspotClusters = !commitHotspots
    ? []
    : commitHotspotStatusFilter === 'all'
      ? commitHotspots.clusters
      : commitHotspots.clusters.filter((cluster) => getCommitHotspotStatusGroup(cluster.primary) === commitHotspotStatusFilter);
  const filteredCommitHotspotRelationTotal = filteredCommitHotspotClusters.reduce(
    (total, cluster) => total + cluster.relations.length,
    0,
  );

  return (
    <div className="flex min-h-full flex-col p-6">
      <PageHeader title={t('cognition.title')} subtitle={t('cognition.subtitle')} />

      {/* 模块一 待决定事项：全宽主面板，置顶（02 §3） */}
      <section className="rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
        <div
          role="button"
          tabIndex={0}
          aria-expanded={inboxExpanded}
          aria-controls="cognition-inbox-content"
          onClick={() => setInboxExpanded((expanded) => !expanded)}
          onKeyDown={(event) => toggleOnKeyboard(event, () => setInboxExpanded((expanded) => !expanded))}
          className={`-mx-1 flex min-w-0 cursor-pointer flex-wrap items-center gap-2 rounded-md px-1 transition-colors hover:bg-ldvh-bg/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50 ${inboxExpanded ? 'mb-4' : ''}`}
        >
          <Inbox size={16} className="shrink-0 text-ldvh-accent" aria-hidden="true" />
          <h3 className="ldvh-section-title min-w-0">{t('cognition.inbox.title')}</h3>
          {data.inbox.total > 0 && (
            <span className="ldvh-meta shrink-0 text-ldvh-text-secondary/70">{data.inbox.total}</span>
          )}
          <span className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
            <CopyPathButton
              path={buildModuleSummary(data, locale, t)}
              label={t('cognition.copyModuleSummary')}
              copiedLabel={t('cognition.copiedModuleSummary')}
            />
            <button
              type="button"
              aria-expanded={inboxExpanded}
              aria-controls="cognition-inbox-content"
              onClick={(event) => {
                event.stopPropagation();
                setInboxExpanded((expanded) => !expanded);
              }}
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

            {/* 截断时如实提示总数与未显示数量，不用分页掩盖待决规模 */}
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

      {/* 推进中事项：只收纳 progress_group=progressing 的 WorkCase，并复用对象列表进行中 Card。 */}
      <section className="mt-4 rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
        <div
          role="button"
          tabIndex={0}
          aria-expanded={activeExpanded}
          aria-controls="cognition-active-workcases-content"
          onClick={() => setActiveExpanded((expanded) => !expanded)}
          onKeyDown={(event) => toggleOnKeyboard(event, () => setActiveExpanded((expanded) => !expanded))}
          className={`-mx-1 flex min-w-0 cursor-pointer flex-wrap items-center gap-2 rounded-md px-1 transition-colors hover:bg-ldvh-bg/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50 ${activeExpanded ? 'mb-4' : ''}`}
        >
          <CirclePlay size={16} className="shrink-0 text-sky-500 dark:text-sky-400" aria-hidden="true" />
          <h3 className="ldvh-section-title min-w-0">{t('cognition.active.title')}</h3>
          {data.activeWorkCases.total > 0 && (
            <span className="ldvh-meta shrink-0 text-ldvh-text-secondary/70">{data.activeWorkCases.total}</span>
          )}
          <span className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
            <CopyPathButton
              path={buildActiveWorkCaseSummary(data, locale, t)}
              label={t('cognition.active.copyModuleSummary')}
              copiedLabel={t('cognition.active.copiedModuleSummary')}
            />
            <button
              type="button"
              aria-expanded={activeExpanded}
              aria-controls="cognition-active-workcases-content"
              onClick={(event) => {
                event.stopPropagation();
                setActiveExpanded((expanded) => !expanded);
              }}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-bg hover:text-ldvh-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50"
              title={t(activeExpanded ? 'cognition.active.collapseSection' : 'cognition.active.expandSection')}
            >
              {activeExpanded ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
              <span className="sr-only">{t(activeExpanded ? 'cognition.active.collapseSection' : 'cognition.active.expandSection')}</span>
            </button>
          </span>
        </div>

        {activeExpanded && (
          <div id="cognition-active-workcases-content">
            <ModuleIssuesNotice issues={activeWorkCaseIssues} t={t} unavailableKey="cognition.active.unavailable" />
            {activeWorkCaseItems.length === 0 ? (
              activeWorkCaseIssues.length === 0 && <p className="ldvh-body-muted">{t('cognition.active.empty')}</p>
            ) : (
              <ul className="ldvh-section-grid min-w-0">
                {visibleActiveWorkCases.map((item) => (
                  <ActiveWorkCaseItemRow key={item.id} item={item} />
                ))}
              </ul>
            )}
            {activeWorkCaseItems.length > ACTIVE_WORKCASE_FIRST_SCREEN_LIMIT && (
              <div className="mt-3 flex min-w-0 flex-wrap items-center justify-between gap-2">
                <p className="ldvh-caption min-w-0">
                  {activeWorkCasesTruncated
                    ? t('cognition.active.truncated', {
                      total: String(data.activeWorkCases.total),
                      shown: String(visibleActiveWorkCases.length),
                      hidden: String(activeWorkCaseItems.length - visibleActiveWorkCases.length),
                    })
                    : null}
                </p>
                <button
                  type="button"
                  onClick={() => setShowAllActive((previous) => !previous)}
                  className="ldvh-caption inline-flex h-8 shrink-0 items-center rounded-md border border-ldvh-border px-3 text-ldvh-text-secondary transition-colors hover:border-ldvh-accent/50 hover:text-ldvh-accent"
                >
                  {activeWorkCasesTruncated ? t('cognition.active.showAll') : t('cognition.active.collapse')}
                </button>
              </div>
            )}
          </div>
        )}
      </section>

      <div className="mt-4 ldvh-panel-grid items-start">
        {/* 模块二 近期动态：以当前对象的 created_at / updated_at 为明确事件，不把提交列表搬到聚焦页。 */}
        <section className="rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
        <div
          role="button"
          tabIndex={0}
          aria-expanded={recentExpanded}
          aria-controls="cognition-recent-activity-content"
          onClick={() => setRecentExpanded((expanded) => !expanded)}
          onKeyDown={(event) => toggleOnKeyboard(event, () => setRecentExpanded((expanded) => !expanded))}
          className={`-mx-1 flex min-w-0 cursor-pointer flex-wrap items-center gap-2 rounded-md px-1 transition-colors hover:bg-ldvh-bg/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50 ${recentExpanded ? 'mb-4' : ''}`}
        >
          <History size={16} className="shrink-0 text-ldvh-accent" aria-hidden="true" />
          <h3 className="ldvh-section-title min-w-0">{t('cognition.recent.title')}</h3>
          {data.recentActivity.total > 0 && (
            <span className="ldvh-meta shrink-0 text-ldvh-text-secondary/70">{data.recentActivity.total}</span>
          )}
          <span className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
            <CopyPathButton
              path={buildRecentActivitySummary(data, locale, t)}
              label={t('cognition.recent.copyModuleSummary')}
              copiedLabel={t('cognition.recent.copiedModuleSummary')}
            />
            <button
              type="button"
              aria-expanded={recentExpanded}
              aria-controls="cognition-recent-activity-content"
              onClick={(event) => {
                event.stopPropagation();
                setRecentExpanded((expanded) => !expanded);
              }}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-bg hover:text-ldvh-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50"
              title={t(recentExpanded ? 'cognition.recent.collapseSection' : 'cognition.recent.expandSection')}
            >
              {recentExpanded ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
              <span className="sr-only">{t(recentExpanded ? 'cognition.recent.collapseSection' : 'cognition.recent.expandSection')}</span>
            </button>
          </span>
        </div>

        {recentExpanded && (
          <div id="cognition-recent-activity-content">
            <div className="mb-3 flex min-w-0 flex-wrap items-center gap-1.5" aria-label={t('cognition.recent.windowLabel')}>
              {RECENT_ACTIVITY_WINDOWS.map((window) => (
                <button
                  key={window}
                  type="button"
                  aria-pressed={recentWindow === window}
                  onClick={() => {
                    setRecentWindow(window);
                    setShowAllRecent(false);
                  }}
                  className={`ldvh-caption inline-flex h-8 items-center rounded-md border px-2.5 transition-colors ${
                    recentWindow === window
                      ? 'border-ldvh-accent/45 bg-ldvh-accent/10 text-ldvh-accent'
                      : 'border-ldvh-border text-ldvh-text-secondary hover:border-ldvh-accent/40 hover:text-ldvh-accent'
                  }`}
                >
                  {t(`cognition.recent.window.${window}` as LocaleKey)}
                </button>
              ))}
              {recentLoading && <span role="status" className="ldvh-caption text-ldvh-text-secondary/70">{t('cognition.recent.loading')}</span>}
            </div>
            {recentError && <p role="status" className="mb-3 ldvh-caption text-red-400">{recentError}</p>}
            <ModuleIssuesNotice issues={recentIssues} t={t} />
            {recentItems.length === 0 ? (
              recentIssues.length === 0 && <p className="ldvh-body-muted">{t('cognition.recent.empty')}</p>
            ) : (
              <ul className="divide-y divide-ldvh-border/70">
                {visibleRecentItems.map((item) => (
                  <RecentActivityRow key={`${item.activity}-${item.id}-${item.occurredAt}`} item={item} />
                ))}
              </ul>
            )}
            {recentItems.length > RECENT_ACTIVITY_FIRST_SCREEN_LIMIT && (
              <div className="mt-3 flex min-w-0 flex-wrap items-center justify-between gap-2">
                <p className="ldvh-caption min-w-0">
                  {recentTruncated
                    ? t('cognition.recent.truncated', {
                      total: String(data.recentActivity.total),
                      shown: String(visibleRecentItems.length),
                      hidden: String(recentItems.length - visibleRecentItems.length),
                    })
                    : null}
                </p>
                <button
                  type="button"
                  onClick={() => setShowAllRecent((previous) => !previous)}
                  className="ldvh-caption inline-flex h-8 shrink-0 items-center rounded-md border border-ldvh-border px-3 text-ldvh-text-secondary transition-colors hover:border-ldvh-accent/50 hover:text-ldvh-accent"
                >
                  {recentTruncated ? t('cognition.recent.showAll') : t('cognition.recent.collapse')}
                </button>
              </div>
            )}
          </div>
        )}
        </section>

        {/* 模块四 Spark 池健康：只读呈现当前 open / terminal 与静默派生，不生成分流建议。 */}
        <section className="rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
        <div
          role="button"
          tabIndex={0}
          aria-expanded={sparkHealthExpanded}
          aria-controls="cognition-spark-health-content"
          onClick={() => setSparkHealthExpanded((expanded) => !expanded)}
          onKeyDown={(event) => toggleOnKeyboard(event, () => setSparkHealthExpanded((expanded) => !expanded))}
          className={`-mx-1 flex min-w-0 cursor-pointer flex-wrap items-center gap-2 rounded-md px-1 transition-colors hover:bg-ldvh-bg/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50 ${sparkHealthExpanded ? 'mb-4' : ''}`}
        >
          <HeartPulse size={16} className="shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          <h3 className="ldvh-section-title min-w-0">{t('cognition.sparkHealth.title')}</h3>
          {sparkHealth && sparkHealth.silentCount > 0 && (
            <span className="ldvh-caption shrink-0 text-ldvh-text-secondary/55">
              {t('cognition.sparkHealth.silentSummary', {
                count: String(sparkHealth.silentCount),
                days: String(sparkHealth.silentThresholdDays),
              })}
            </span>
          )}
          <span className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
            {sparkHealth && (
              <CopyPathButton
                path={buildSparkHealthSummary(data, locale, t)}
                label={t('cognition.sparkHealth.copyModuleSummary')}
                copiedLabel={t('cognition.sparkHealth.copiedModuleSummary')}
              />
            )}
            <button
              type="button"
              aria-expanded={sparkHealthExpanded}
              aria-controls="cognition-spark-health-content"
              onClick={(event) => {
                event.stopPropagation();
                setSparkHealthExpanded((expanded) => !expanded);
              }}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-bg hover:text-ldvh-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50"
              title={t(sparkHealthExpanded ? 'cognition.sparkHealth.collapseSection' : 'cognition.sparkHealth.expandSection')}
            >
              {sparkHealthExpanded ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
              <span className="sr-only">{t(sparkHealthExpanded ? 'cognition.sparkHealth.collapseSection' : 'cognition.sparkHealth.expandSection')}</span>
            </button>
          </span>
        </div>

        {sparkHealthExpanded && (
          <div id="cognition-spark-health-content">
            <ModuleIssuesNotice issues={sparkHealthIssues} t={t} unavailableKey="cognition.sparkHealth.unavailable" />
            {sparkHealth && sparkHealth.total > 0 && (
              <div className="border-y border-ldvh-border/70 py-4">
                <div className="flex h-7 w-full overflow-hidden rounded-md bg-rose-500/80">
                  {sparkHealth.terminalTotal > 0 && (
                    <div
                      className="flex shrink-0 items-center justify-center bg-emerald-500/85 text-sm font-semibold text-white"
                      style={{ width: `${settledRatio}%` }}
                    >
                      {sparkHealth.terminalTotal}
                    </div>
                  )}
                  <div className="flex min-w-0 flex-1 items-center justify-center text-sm font-semibold text-white">
                    {sparkHealth.openTotal}
                  </div>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-center">
                  <p className="ldvh-caption min-w-0 break-words text-ldvh-text-secondary">
                    {t('cognition.sparkHealth.settled', { count: String(sparkHealth.terminalTotal) })}
                    {terminalDetail ? `（${terminalDetail}）` : ''}
                  </p>
                  <p className="ldvh-caption min-w-0 break-words text-ldvh-text-secondary">
                    {t('cognition.sparkHealth.pending', { count: String(sparkHealth.openTotal) })}
                    {openPriorityDetail ? `（${openPriorityDetail}）` : ''}
                  </p>
                </div>
              </div>
            )}

            {sparkHealth && silentSparkItems.length === 0 ? (
              sparkHealthIssues.length === 0 && <p className="ldvh-body-muted">{t('cognition.sparkHealth.empty')}</p>
            ) : (
              <ul className="divide-y divide-ldvh-border/70">
                {visibleSilentSparkItems.map((item) => <SparkHealthRow key={item.id} item={item} />)}
              </ul>
            )}

            {sparkHealth && silentSparkItems.length > 0 && (
              <>
                {silentSparkItems.length > SPARK_HEALTH_FIRST_SCREEN_LIMIT && (
                  <button
                    type="button"
                    onClick={() => setShowAllSilentSpark((previous) => !previous)}
                    className="mt-3 ldvh-caption inline-flex h-8 items-center rounded-md text-ldvh-text-secondary transition-colors hover:text-ldvh-accent focus-visible:outline-none focus-visible:underline"
                  >
                    {silentSparkTruncated
                      ? t('cognition.sparkHealth.showRemaining', { count: String(silentSparkItems.length - visibleSilentSparkItems.length) })
                      : t('cognition.sparkHealth.collapseList')}
                  </button>
                )}
              </>
            )}
          </div>
        )}
        </section>
      </div>

      {/* 模块三：以精确 Git 回指为热点中心，仅展开一跳正式关系；不推断语义关联或重要性。 */}
      <section className="mt-4 rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
        <div
          role="button"
          tabIndex={0}
          aria-expanded={commitHotspotsExpanded}
          aria-controls="cognition-commit-hotspots-content"
          onClick={() => setCommitHotspotsExpanded((expanded) => !expanded)}
          onKeyDown={(event) => toggleOnKeyboard(event, () => setCommitHotspotsExpanded((expanded) => !expanded))}
          className={`-mx-1 flex min-w-0 cursor-pointer flex-wrap items-center gap-2 rounded-md px-1 transition-colors hover:bg-ldvh-bg/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50 ${commitHotspotsExpanded ? 'mb-4' : ''}`}
        >
          <GitFork size={16} className="shrink-0 text-ldvh-accent" aria-hidden="true" />
          <h3 className="ldvh-section-title min-w-0">{t('cognition.commitHotspots.title')}</h3>
          <span className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
            {commitHotspots && (
              <CopyPathButton
                path={buildCommitHotspotSummary(data, locale, t)}
                label={t('cognition.commitHotspots.copyModuleSummary')}
                copiedLabel={t('cognition.commitHotspots.copiedModuleSummary')}
              />
            )}
            <button
              type="button"
              aria-expanded={commitHotspotsExpanded}
              aria-controls="cognition-commit-hotspots-content"
              onClick={(event) => {
                event.stopPropagation();
                setCommitHotspotsExpanded((expanded) => !expanded);
              }}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-bg hover:text-ldvh-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50"
              title={t(commitHotspotsExpanded ? 'cognition.commitHotspots.collapseSection' : 'cognition.commitHotspots.expandSection')}
            >
              {commitHotspotsExpanded ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
              <span className="sr-only">{t(commitHotspotsExpanded ? 'cognition.commitHotspots.collapseSection' : 'cognition.commitHotspots.expandSection')}</span>
            </button>
          </span>
        </div>

        {commitHotspotsExpanded && (
          <div id="cognition-commit-hotspots-content">
            <ModuleIssuesNotice issues={commitHotspotIssues} t={t} unavailableKey="cognition.commitHotspots.unavailable" />
            {commitHotspots && (
              commitHotspots.hotspotTotal === 0 ? (
                commitHotspotIssues.length === 0 && <p className="ldvh-body-muted">{t('cognition.commitHotspots.empty')}</p>
              ) : (
                <div className="flex min-w-0 flex-col gap-3">
                  <div
                    className="flex min-w-0 flex-wrap items-center gap-1.5"
                    role="group"
                    aria-label={t('cognition.commitHotspots.statusFilterLabel')}
                  >
                    <span className="ldvh-caption mr-0.5 text-ldvh-text-secondary/75">
                      {t('cognition.commitHotspots.statusFilterLabel')}
                    </span>
                    {COMMIT_HOTSPOT_STATUS_FILTERS.map((filter) => (
                      <button
                        key={filter}
                        type="button"
                        aria-pressed={commitHotspotStatusFilter === filter}
                        onClick={() => {
                          setCommitHotspotStatusFilter(filter);
                          setExpandedHotspotKey(null);
                        }}
                        className={`ldvh-caption inline-flex h-8 items-center rounded-md border px-2.5 transition-colors ${
                          commitHotspotStatusFilter === filter
                            ? 'border-ldvh-accent/45 bg-ldvh-accent/10 text-ldvh-accent'
                            : 'border-ldvh-border text-ldvh-text-secondary hover:border-ldvh-accent/40 hover:text-ldvh-accent'
                        }`}
                      >
                        {t(`cognition.commitHotspots.statusFilter.${filter}` as LocaleKey)}
                      </button>
                    ))}
                  </div>
                  <CommitHotspotLegend
                    totalCommits={commitHotspots.totalCommits}
                    hotspotTotal={filteredCommitHotspotClusters.length}
                    relationTotal={filteredCommitHotspotRelationTotal}
                    relationKeys={[...new Set(filteredCommitHotspotClusters.flatMap((cluster) => (
                      cluster.relations.map((relation) => relation.relationKey)
                    )))]}
                  />
                  {filteredCommitHotspotClusters.length === 0 ? (
                    <p className="ldvh-body-muted">{t('cognition.commitHotspots.filterEmpty')}</p>
                  ) : (
                    <div className="ldvh-hotspot-grid min-w-0 items-start">
                      {filteredCommitHotspotClusters.map((cluster, index) => (
                        <CommitHotspotCluster
                          key={`${cluster.primary.type}:${cluster.primary.id}`}
                          cluster={cluster}
                          index={index}
                          canExpand={cluster.relations.length > 0}
                          expanded={expandedHotspotKey === `${cluster.primary.type}:${cluster.primary.id}`}
                          onExpandedChange={(expanded) => setExpandedHotspotKey(
                            expanded ? `${cluster.primary.type}:${cluster.primary.id}` : null,
                          )}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        )}
      </section>
    </div>
  );
}
