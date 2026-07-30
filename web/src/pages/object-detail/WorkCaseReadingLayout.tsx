import { useEffect, useState, type KeyboardEvent, type ReactNode } from "react";
import {
  Activity,
  ArrowRight,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  CircleAlert,
  Circle,
  CircleCheck,
  CircleDot,
  CircleHelp,
  Info,
  CircleMinus,
  CirclePlay,
  CircleX,
  ClipboardList,
  Clock3,
  ScanLine,
  Target,
} from "lucide-react";
import SummaryText from "@/components/SummaryText";
import CopyPathButton from "@/components/CopyPathButton";
import { ObjectTypeIcon } from "@/components/SemanticIcon";
import WorkCaseProgressTrack from "@/components/WorkCaseProgressTrack";
import { useI18n } from "@/i18n/context";
import {
  getFieldLabel,
  getFieldValueLabel,
  getStatusLocale,
} from "@/i18n/locales";
import {
  fetchObjectDetail,
  type ObjectDetail,
  type WorkCaseDetailData,
} from "@/utils/api";
import { getFactReadMeta, isReadableFact } from "@/utils/factReadMeta";
import { usePanel } from "@/utils/panelContext";
import { CATEGORY_COLORS } from "@/utils/categoryColors";
import { formatDateTime } from "@/utils/dateFormat";
import { projectCurrentWorkCaseDetail } from "@/shared/workcaseDetailProjection";
import {
  FactAssociationsSection,
} from "@/pages/object-detail/FactAssociationsSection";
import { getCurrentProjectId } from "@/pages/object-detail/model";
import {
  fieldIssue,
  type FieldPresentationIssue,
} from "@/pages/object-detail/fieldIssues";
import { FieldProblem } from "@/pages/object-detail/FactReadingLayouts";
import {
  DetailInlineField,
  ReadingNodeSection,
  RelatedContentSection,
  getReadingNodeNextState,
  type ReadingNodeState,
} from "@/pages/ObjectDetail";

const WORKCASE_DETAIL_SEMANTIC_ICON_SIZE = 14;
const WORKCASE_DETAIL_SEMANTIC_SURFACE_PADDING = "px-3.5 pb-2 pt-3";

/**
 * WorkCase detail has one current reading structure.  Field presence decides
 * whether a node exists; status, phase, card progress groups, and list DTOs do
 * not switch, hide, or reorder this structure.
 */
export function WorkCaseReadingLayout({
  obj,
  locale,
}: {
  obj: WorkCaseDetailData;
  locale: string;
}) {
  const { t } = useI18n();
  const detail = projectCurrentWorkCaseDetail(obj);
  const {
    criteria,
    criterionResults,
    workItems,
    creationReviews,
    executionAuthorization,
    executionApproval,
    resultReviews,
    closureProposal,
    terminalResiduals,
    terminalSuggestions,
    urls,
  } = detail;

  // §5.3/§7.1：字段缺失或类型不符在对应节点内就地标明，节点不因整组字段缺席而消失。
  const issueFor = (field: string) => fieldIssue(obj, field);
  const responsibilityVisible =
    detail.responsibility || Boolean(issueFor("goal") || issueFor("scope"));
  const snapshotVisible =
    detail.currentSnapshot ||
    Boolean(
      issueFor("phase") ||
        issueFor("summary") ||
        issueFor("resume_from") ||
        issueFor("waiting_on") ||
        issueFor("blocking_summary"),
    );
  const criteriaVisible =
    criteria.length > 0 ||
    Boolean(
      issueFor("success_criterion_definitions") ||
        issueFor("success_criterion_results"),
    );
  const planVisible =
    detail.planAndItems ||
    Boolean(issueFor("plan_version") || issueFor("work_items"));
  const creationReviewsVisible =
    creationReviews.length > 0 || Boolean(issueFor("creation_reviews"));
  const authorizationVisible =
    Boolean(executionAuthorization) || Boolean(issueFor("execution_authorization"));
  const approvalVisible =
    Boolean(executionApproval) || Boolean(issueFor("execution_approval"));
  const resultVisible =
    detail.resultAndValidation ||
    Boolean(
      issueFor("result_version") ||
        issueFor("result_summary") ||
        issueFor("validation_summary"),
    );
  const controllerCheckVisible =
    detail.controllerCheck || Boolean(issueFor("controller_check_summary"));
  const resultReviewsVisible =
    resultReviews.length > 0 || Boolean(issueFor("result_reviews"));
  const closureProposalVisible =
    Boolean(closureProposal) || Boolean(issueFor("closure_proposal"));
  const terminalVisible =
    detail.terminalDisposition ||
    Boolean(
      issueFor("closure_outcome") ||
        issueFor("disposition_summary") ||
        issueFor("residual_responsibilities") ||
        issueFor("spark_suggestions"),
    );
  const terminalSummaryOnly =
    terminalResiduals.length === 0 &&
    terminalSuggestions.length === 0 &&
    !Boolean(
      issueFor("closure_outcome") ||
        issueFor("disposition_summary") ||
        issueFor("residual_responsibilities") ||
        issueFor("spark_suggestions"),
    );
  const relationsIssue = issueFor("relations");
  const urlsIssue = issueFor("urls");
  const currentProjectId = getCurrentProjectId(obj);

  return (
    <div className="mb-6 flex flex-col gap-5">
      {snapshotVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseCurrentSnapshot")}
          locale={locale}
          contentVariant="semantic"
        >
          <FieldIssueRow fieldKey="phase" issue={issueFor("phase")} locale={locale} />
          <WorkCaseProgressTrack phase={obj.phase} className="mt-0" />
          <SnapshotProseField fieldKey="summary" value={obj.summary} locale={locale} />
          <FieldIssueRow fieldKey="summary" issue={issueFor("summary")} locale={locale} />
          <SnapshotProseField
            fieldKey="resume_from"
            value={obj.resume_from}
            locale={locale}
          />
          <FieldIssueRow fieldKey="resume_from" issue={issueFor("resume_from")} locale={locale} />
          <SnapshotProseField
            fieldKey="waiting_on"
            value={obj.waiting_on}
            locale={locale}
          />
          <FieldIssueRow fieldKey="waiting_on" issue={issueFor("waiting_on")} locale={locale} />
          <SnapshotProseField
            fieldKey="blocking_summary"
            value={obj.blocking_summary}
            locale={locale}
          />
          <FieldIssueRow fieldKey="blocking_summary" issue={issueFor("blocking_summary")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {responsibilityVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseResponsibility")}
          locale={locale}
          contentVariant="semantic"
        >
          <ResponsibilityField
            fieldKey="goal"
            value={obj.goal}
            locale={locale}
            tone="goal"
          />
          <FieldIssueRow fieldKey="goal" issue={issueFor("goal")} locale={locale} />
          <ResponsibilityField
            fieldKey="scope"
            value={obj.scope}
            locale={locale}
            tone="scope"
          />
          <FieldIssueRow fieldKey="scope" issue={issueFor("scope")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {criteriaVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseSuccessCriteria")}
          locale={locale}
          headerMeta={criteria.length > 0 ? (
            <span className="ldvh-meta-muted shrink-0">
              {t("objectDetail.workcaseCriteriaCount", { count: String(criteria.length) })}
            </span>
          ) : undefined}
          contentVariant="semantic"
        >
          {criteria.length > 0 && (
            <SuccessCriteria
              definitions={criteria}
              results={criterionResults}
              locale={locale}
            />
          )}
          <FieldIssueRow fieldKey="success_criterion_definitions" issue={issueFor("success_criterion_definitions")} locale={locale} />
          <FieldIssueRow fieldKey="success_criterion_results" issue={issueFor("success_criterion_results")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {planVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcasePlanAndItems")}
          locale={locale}
          headerMeta={<PlanVersionMeta value={obj.plan_version} locale={locale} />}
          contentVariant="semantic"
        >
          <FieldIssueRow fieldKey="plan_version" issue={issueFor("plan_version")} locale={locale} />
          {workItems.length > 0 && (
            <WorkItemList items={workItems} locale={locale} />
          )}
          <FieldIssueRow fieldKey="work_items" issue={issueFor("work_items")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {creationReviewsVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseCreationReviews")}
          note={t("objectDetail.workcaseCreationReviewsBoundary")}
          locale={locale}
          contentVariant="semantic"
        >
          {creationReviews.length > 0 && (
            <ReviewList reviews={creationReviews} locale={locale} />
          )}
          <FieldIssueRow fieldKey="creation_reviews" issue={issueFor("creation_reviews")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {authorizationVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseExecutionAuthorization")}
          note={t("objectDetail.workcaseExecutionAuthorizationBoundary")}
          locale={locale}
          contentVariant="semantic"
        >
          {executionAuthorization && (
            <ExecutionAuthorization authorization={executionAuthorization} locale={locale} />
          )}
          <FieldIssueRow fieldKey="execution_authorization" issue={issueFor("execution_authorization")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {approvalVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseExecutionApproval")}
          note={t("objectDetail.workcaseExecutionApprovalBoundary")}
          locale={locale}
          contentVariant="semantic"
        >
          {executionApproval && (
            <ExecutionApproval approval={executionApproval} locale={locale} />
          )}
          <FieldIssueRow fieldKey="execution_approval" issue={issueFor("execution_approval")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {resultVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseResultAndValidation")}
          locale={locale}
          headerMeta={<ResultVersionMeta value={obj.result_version} locale={locale} />}
          contentVariant="semantic"
        >
          <FieldIssueRow fieldKey="result_version" issue={issueFor("result_version")} locale={locale} />
          <ProseField
            fieldKey="result_summary"
            value={obj.result_summary}
            locale={locale}
            variant="result"
          />
          <FieldIssueRow fieldKey="result_summary" issue={issueFor("result_summary")} locale={locale} />
          <ProseField
            fieldKey="validation_summary"
            value={obj.validation_summary}
            locale={locale}
            variant="validation"
          />
          <FieldIssueRow fieldKey="validation_summary" issue={issueFor("validation_summary")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {controllerCheckVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseControllerCheck")}
          note={t("objectDetail.workcaseControllerCheckBoundary")}
          locale={locale}
          contentVariant="semantic"
        >
          <ProseField
            fieldKey="controller_check_summary"
            value={obj.controller_check_summary}
            locale={locale}
            showLabel={false}
            variant="controller"
          />
          <FieldIssueRow fieldKey="controller_check_summary" issue={issueFor("controller_check_summary")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {resultReviewsVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseResultReviews")}
          note={t("objectDetail.workcaseResultReviewsBoundary")}
          locale={locale}
          contentVariant="semantic"
        >
          {resultReviews.length > 0 && (
            <ReviewList reviews={resultReviews} locale={locale} />
          )}
          <FieldIssueRow fieldKey="result_reviews" issue={issueFor("result_reviews")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {closureProposalVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseClosureProposal")}
          note={t("objectDetail.workcaseClosureProposalBoundary")}
          locale={locale}
          headerMeta={closureProposal ? (
            <ProposalOutcomeMeta value={closureProposal.proposed_outcome} locale={locale} />
          ) : undefined}
          contentVariant="semantic"
        >
          {closureProposal && (
            <ClosureProposal
              proposal={closureProposal}
              currentProjectId={currentProjectId}
              locale={locale}
            />
          )}
          <FieldIssueRow fieldKey="closure_proposal" issue={issueFor("closure_proposal")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {terminalVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseTerminalDisposition")}
          note={t("objectDetail.workcaseTerminalDispositionBoundary")}
          locale={locale}
          contentVariant="semantic"
        >
          <ClosureOutcomeSummary
            outcomeFieldKey="closure_outcome"
            outcome={obj.closure_outcome}
            summaryFieldKey="disposition_summary"
            summary={obj.disposition_summary}
            locale={locale}
            compact={terminalSummaryOnly}
          />
          <FieldIssueRow fieldKey="closure_outcome" issue={issueFor("closure_outcome")} locale={locale} />
          <FieldIssueRow fieldKey="disposition_summary" issue={issueFor("disposition_summary")} locale={locale} />
          {terminalResiduals.length > 0 && (
            <TerminalResidualList items={terminalResiduals} locale={locale} />
          )}
          <FieldIssueRow fieldKey="residual_responsibilities" issue={issueFor("residual_responsibilities")} locale={locale} />
          {terminalSuggestions.length > 0 && (
            <SparkSuggestionList items={terminalSuggestions} locale={locale} />
          )}
          <FieldIssueRow fieldKey="spark_suggestions" issue={issueFor("spark_suggestions")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {relationsIssue ? (
        <WorkCaseReadingNode
          title={getFieldLabel("fact_associations", locale)}
          locale={locale}
        >
          <FieldIssueRow fieldKey="relations" issue={relationsIssue} locale={locale} />
        </WorkCaseReadingNode>
      ) : (
        <FactAssociationsSection
          obj={obj}
          locale={locale}
        />
      )}

      {urls.length > 0 ? (
        <RelatedContentSection
          entries={[["urls", urls]]}
          locale={locale}
          title={t("objectDetail.workcaseUrls")}
        />
      ) : urlsIssue ? (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseUrls")}
          locale={locale}
        >
          <FieldIssueRow fieldKey="urls" issue={urlsIssue} locale={locale} />
        </WorkCaseReadingNode>
      ) : null}
    </div>
  );
}

function WorkCaseReadingNode({
  title,
  note,
  locale,
  headerMeta,
  contentVariant = "rows",
  children,
}: {
  title: string;
  note?: string;
  locale: string;
  headerMeta?: ReactNode;
  contentVariant?: "rows" | "semantic";
  children: ReactNode;
}) {
  const [state, setState] = useState<ReadingNodeState>("expanded");
  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      headerMeta={headerMeta}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className={contentVariant === "semantic" ? "grid gap-3" : "ldvh-study-node-content"}>
        {note && <ReadingBoundaryNote value={note} />}
        <div className={contentVariant === "semantic" ? "grid gap-3" : "divide-y divide-ldvh-border/60"}>
          {children}
        </div>
      </div>
    </ReadingNodeSection>
  );
}

function ReadingBoundaryNote({ value }: { value: string }) {
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-md bg-ldvh-border/20 px-3 py-2.5 text-ldvh-text-secondary/80">
      <Info size={14} strokeWidth={2} className="shrink-0" aria-hidden="true" />
      <p className="ldvh-caption min-w-0 flex-1">{value}</p>
    </div>
  );
}

function PlanVersionMeta({ value, locale }: { value: unknown; locale: string }) {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return (
    <span className="ldvh-meta-muted inline-flex shrink-0 items-center gap-1.5 font-normal">
      <span>{getFieldLabel("plan_version", locale)}</span>
      <span className="font-mono tabular-nums text-ldvh-text-secondary">{value}</span>
    </span>
  );
}

function ResultVersionMeta({ value, locale }: { value: unknown; locale: string }) {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return (
    <span className="ldvh-meta-muted inline-flex shrink-0 items-center gap-1.5 font-normal">
      <span>{getFieldLabel("result_version", locale)}</span>
      <span className="font-mono tabular-nums text-ldvh-text-secondary">{value}</span>
    </span>
  );
}

function ProposalOutcomeMeta({ value, locale }: { value: unknown; locale: string }) {
  const outcome = detailString(value);
  if (!outcome) return null;
  return (
    <span className="ldvh-meta shrink-0 font-normal text-amber-700/75 dark:text-amber-200/75">
      {getFieldValueLabel("proposed_outcome", outcome, locale)}
    </span>
  );
}

function ResponsibilityField({
  fieldKey,
  value,
  locale,
  tone,
}: {
  fieldKey: "goal" | "scope";
  value: unknown;
  locale: string;
  tone: "goal" | "scope";
}) {
  const [expanded, setExpanded] = useState(tone !== "scope");
  if (typeof value !== "string" || !value.trim()) return null;
  const Icon = tone === "goal" ? Target : ScanLine;
  const surfaceClass = tone === "goal"
    ? "border-violet-400/35 bg-violet-500/[0.055]"
    : "border-cyan-500/30 bg-cyan-500/[0.045]";
  const headingClass = tone === "goal"
    ? "text-violet-700/85 dark:text-violet-200/85"
    : "text-cyan-700/85 dark:text-cyan-200/85";
  const bodyClass = tone === "goal"
    ? "!text-violet-950/65 dark:!text-violet-100/75"
    : "!text-cyan-950/65 dark:!text-cyan-100/75";

  return (
    <section className={`min-w-0 rounded-lg border ${WORKCASE_DETAIL_SEMANTIC_SURFACE_PADDING} ${surfaceClass}`}>
      {tone === "scope" ? (
        <button
          type="button"
          aria-expanded={expanded}
          onClick={() => setExpanded((current) => !current)}
          className={`flex w-full min-w-0 items-center justify-between gap-3 text-left ${headingClass}`}
        >
          <span className="flex min-w-0 items-center gap-2">
            <Icon size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
            <span className="ldvh-detail-semantic-title min-w-0 text-current">
              {getFieldLabel(fieldKey, locale)}
            </span>
          </span>
          {expanded ? (
            <ChevronUp size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} className="shrink-0 text-current/70" aria-hidden="true" />
          ) : (
            <ChevronDown size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} className="shrink-0 text-current/70" aria-hidden="true" />
          )}
        </button>
      ) : (
        <div className={`flex min-w-0 items-center gap-2 ${headingClass}`}>
          <Icon size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
          <span className="ldvh-detail-semantic-title min-w-0 text-current">
            {getFieldLabel(fieldKey, locale)}
          </span>
        </div>
      )}
      {expanded && (
        <div className="mt-2 min-w-0">
          <SummaryText
            value={value}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className={`ldvh-detail-semantic-body ${bodyClass}`}
          />
        </div>
      )}
    </section>
  );
}

function SnapshotProseField({
  fieldKey,
  value,
  locale,
}: {
  fieldKey: "summary" | "resume_from" | "waiting_on" | "blocking_summary";
  value: unknown;
  locale: string;
}) {
  if (typeof value !== "string" || !value.trim()) return null;
  const styles = {
    summary: {
      Icon: Activity,
      surface: "border-sky-400/30 bg-sky-500/[0.045]",
      heading: "text-sky-700/85 dark:text-sky-200/85",
      body: "!text-sky-950/65 dark:!text-sky-100/75",
    },
    resume_from: {
      Icon: ArrowRight,
      surface: "border-emerald-400/30 bg-emerald-500/[0.045]",
      heading: "text-emerald-700/85 dark:text-emerald-200/85",
      body: "!text-emerald-950/65 dark:!text-emerald-100/75",
    },
    waiting_on: {
      Icon: Clock3,
      surface: "border-amber-400/35 bg-amber-500/[0.055]",
      heading: "text-amber-700/85 dark:text-amber-200/85",
      body: "!text-amber-950/65 dark:!text-amber-100/75",
    },
    blocking_summary: {
      Icon: CircleAlert,
      surface: "border-rose-400/35 bg-rose-500/[0.055]",
      heading: "text-rose-700/85 dark:text-rose-200/85",
      body: "!text-rose-950/65 dark:!text-rose-100/75",
    },
  }[fieldKey];
  const { Icon } = styles;

  return (
    <section className={`min-w-0 rounded-lg border ${WORKCASE_DETAIL_SEMANTIC_SURFACE_PADDING} ${styles.surface}`}>
      <div className={`flex min-w-0 items-center gap-2 ${styles.heading}`}>
        <Icon size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        <span className="ldvh-detail-semantic-title min-w-0 text-current">
          {getFieldLabel(fieldKey, locale)}
        </span>
      </div>
      <div className="mt-2 min-w-0">
        <SummaryText
          value={value}
          collapseThreshold={Number.MAX_SAFE_INTEGER}
          className={`ldvh-detail-semantic-body ${styles.body}`}
        />
      </div>
    </section>
  );
}

function FieldIssueRow({
  fieldKey,
  issue,
  locale,
  label,
}: {
  fieldKey: string;
  issue?: FieldPresentationIssue;
  locale: string;
  label?: string;
}) {
  if (!issue) return null;
  return (
    <DetailInlineField
      label={label ?? getFieldLabel(fieldKey, locale)}
      value={<FieldProblem issue={issue} />}
    />
  );
}

/**
 * Narrative fields read as prose like the other fact readers: a small caption
 * keeps the field identity and the Markdown body renders below, without the
 * structured label column. Single-field nodes omit the redundant caption.
 */
function ProseField({
  fieldKey,
  value,
  locale,
  tone = "default",
  label,
  showLabel = true,
  variant = "plain",
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
  tone?: "default" | "warning";
  label?: string;
  showLabel?: boolean;
  variant?: "plain" | "result" | "validation" | "controller";
}) {
  const [semanticExpanded, setSemanticExpanded] = useState(variant !== "validation");
  if (typeof value !== "string" || !value.trim()) return null;
  if (variant !== "plain") {
    const styles = {
      result: {
        Icon: CircleCheck,
        surface: "border-emerald-400/30 bg-emerald-500/[0.055]",
        heading: "text-emerald-700/85 dark:text-emerald-200/85",
        body: "!text-emerald-950/72 dark:!text-emerald-100/78",
      },
      validation: {
        Icon: ScanLine,
        surface: "border-sky-400/30 bg-sky-500/[0.05]",
        heading: "text-sky-700/85 dark:text-sky-200/85",
        body: "!text-sky-950/72 dark:!text-sky-100/78",
      },
      controller: {
        Icon: Activity,
        surface: "border-cyan-400/30 bg-cyan-500/[0.045]",
        heading: "text-cyan-700/85 dark:text-cyan-200/85",
        body: "!text-cyan-950/72 dark:!text-cyan-100/78",
      },
    }[variant];
    const { Icon } = styles;
    const collapsible = variant === "validation" && showLabel;
    return (
      <section className={`min-w-0 rounded-lg border ${semanticExpanded ? WORKCASE_DETAIL_SEMANTIC_SURFACE_PADDING : "px-3.5 py-3"} ${styles.surface}`}>
        {showLabel && (collapsible ? (
          <button
            type="button"
            aria-expanded={semanticExpanded}
            onClick={() => setSemanticExpanded((current) => !current)}
            className={`flex w-full min-w-0 items-center justify-between gap-3 text-left ${styles.heading}`}
          >
            <span className="flex min-w-0 items-center gap-2">
              <Icon size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
              <span className="ldvh-detail-semantic-title min-w-0 text-current">
                {label ?? getFieldLabel(fieldKey, locale)}
              </span>
            </span>
            {semanticExpanded ? (
              <ChevronUp size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0 text-current/70" aria-hidden="true" />
            ) : (
              <ChevronDown size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0 text-current/70" aria-hidden="true" />
            )}
          </button>
        ) : (
          <div className={`flex min-w-0 items-center gap-2 ${styles.heading}`}>
            <Icon size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
            <span className="ldvh-detail-semantic-title min-w-0 text-current">
              {label ?? getFieldLabel(fieldKey, locale)}
            </span>
          </div>
        ))}
        {semanticExpanded && (
          <div className={showLabel ? "mt-2 min-w-0" : "min-w-0"}>
            <SummaryText
              value={value}
              collapseThreshold={Number.MAX_SAFE_INTEGER}
              className={`ldvh-detail-semantic-body ${styles.body}`}
            />
          </div>
        )}
      </section>
    );
  }
  const body = (
    <div
      className={
        tone === "warning"
          ? "rounded-md border border-amber-500/25 bg-amber-500/5 px-3 py-2"
          : ""
      }
    >
      <SummaryText
        value={value}
        collapseThreshold={Number.MAX_SAFE_INTEGER}
      />
    </div>
  );
  return (
    <div className="py-3 first:pt-0 last:pb-0">
      {showLabel && (
        <div className="ldvh-caption-strong mb-1.5 flex items-center gap-2 text-ldvh-text-secondary">
          <span
            className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-text-secondary/45"
            aria-hidden="true"
          />
          <span>{label ?? getFieldLabel(fieldKey, locale)}</span>
        </div>
      )}
      {body}
    </div>
  );
}

function TextField({
  fieldKey,
  value,
  locale,
  tone = "default",
  label,
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
  tone?: "default" | "warning";
  label?: string;
}) {
  if (typeof value !== "string" || !value.trim()) return null;
  return (
    <DetailInlineField
      label={label ?? getFieldLabel(fieldKey, locale)}
      value={
        <div
          className={
            tone === "warning"
              ? "rounded-md border border-amber-500/25 bg-amber-500/5 px-3 py-2"
              : ""
          }
        >
          <SummaryText
            value={value}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
          />
        </div>
      }
    />
  );
}

function SuccessCriteria({
  definitions,
  results,
  locale,
}: {
  definitions: Array<Record<string, unknown>>;
  results: Array<Record<string, unknown>>;
  locale: string;
}) {
  const { t } = useI18n();
  const resultById = new Map(
    results.map((result) => [detailString(result.criterion_id), result]),
  );

  return (
    <ul className="grid min-w-0 gap-3">
      {definitions.map((definition, index) => {
        const criterionId = detailString(definition.criterion_id);
        const result = resultById.get(criterionId);
        return (
          <CriterionObject
            key={criterionId || String(index)}
            criterionId={criterionId}
            statement={detailString(definition.statement)}
            result={result}
            resultLabel={t("objectDetail.workcaseCriterionResultSummary")}
            locale={locale}
          />
        );
      })}
    </ul>
  );
}

function CriterionObject({
  criterionId,
  statement,
  result,
  resultLabel,
  locale,
}: {
  criterionId: string;
  statement: string;
  result?: Record<string, unknown>;
  resultLabel: string;
  locale: string;
}) {
  return (
    <li className="min-w-0 overflow-hidden rounded-lg border border-blue-400/30 bg-blue-500/[0.03]">
      <div className="flex min-w-0 items-center gap-2 border-b border-blue-400/20 px-3.5 py-2.5">
        <CircleDot
          size={16}
          strokeWidth={2}
          className="shrink-0 text-blue-500/80 dark:text-blue-300/80"
          aria-hidden="true"
        />
        <span className="ldvh-meta min-w-0 flex-1 break-all text-blue-700/70 dark:text-blue-200/70">
          {criterionId}
        </span>
        {result && <CriterionOutcomeChip value={result.outcome} locale={locale} />}
      </div>
      <div className="min-w-0 px-3.5 py-3">
        {statement.trim() && (
          <div className="rounded-md border border-blue-400/15 bg-blue-500/[0.025] px-3 py-2 dark:bg-blue-400/[0.035]">
            <SummaryText
              value={statement}
              collapseThreshold={Number.MAX_SAFE_INTEGER}
              className="ldvh-detail-semantic-body font-medium !text-blue-900/75 dark:!text-blue-100/80"
            />
          </div>
        )}
        {result && typeof result.summary === "string" && result.summary.trim() && (
          <CriterionResultSummary
            outcome={result.outcome}
            value={result.summary}
            label={resultLabel}
          />
        )}
      </div>
    </li>
  );
}

function criterionOutcomeStyle(value: unknown) {
  if (value === "satisfied") {
    return {
      Icon: CircleCheck,
      chip: "border-emerald-400/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
      heading: "text-emerald-700/80 dark:text-emerald-200/80",
      hover: "hover:bg-emerald-500/[0.07]",
      summary: "bg-emerald-500/[0.045] text-emerald-900/75 dark:bg-emerald-400/[0.06] dark:text-emerald-100/80",
    };
  }
  if (value === "not_satisfied") {
    return {
      Icon: CircleX,
      chip: "border-rose-400/30 bg-rose-500/10 text-rose-700 dark:text-rose-200",
      heading: "text-rose-700/80 dark:text-rose-200/80",
      hover: "hover:bg-rose-500/[0.07]",
      summary: "bg-rose-500/[0.045] text-rose-900/75 dark:bg-rose-400/[0.06] dark:text-rose-100/80",
    };
  }
  if (value === "not_verified") {
    return {
      Icon: CircleHelp,
      chip: "border-amber-400/30 bg-amber-500/10 text-amber-700 dark:text-amber-200",
      heading: "text-amber-700/80 dark:text-amber-200/80",
      hover: "hover:bg-amber-500/[0.07]",
      summary: "bg-amber-500/[0.045] text-amber-900/75 dark:bg-amber-400/[0.06] dark:text-amber-100/80",
    };
  }
  return {
    Icon: CircleDot,
    chip: "border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary",
    heading: "text-ldvh-text-secondary",
    hover: "hover:bg-ldvh-bg/70",
    summary: "bg-ldvh-bg/45 text-ldvh-text-secondary",
  };
}

function CriterionOutcomeChip({ value, locale }: { value: unknown; locale: string }) {
  if (typeof value !== "string" || !value.trim()) return null;
  const styles = criterionOutcomeStyle(value);
  const { Icon } = styles;
  return (
    <span
      title={value}
      className={`ldvh-chip inline-flex shrink-0 items-center gap-1.5 rounded-md border px-2 py-0.5 ${styles.chip}`}
    >
      <Icon size={13} strokeWidth={2} aria-hidden="true" />
      {getFieldValueLabel("outcome", value, locale)}
    </span>
  );
}

function CriterionResultSummary({
  outcome,
  value,
  label,
}: {
  outcome: unknown;
  value: string;
  label: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const styles = criterionOutcomeStyle(outcome);
  return (
    <div className="mt-2">
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
        className={`group -ml-1.5 inline-flex min-w-0 items-center gap-1.5 rounded px-1.5 py-1 text-left transition-colors ${styles.heading} ${styles.hover}`}
      >
        <span className="ldvh-caption-strong min-w-0 !text-current">{label}</span>
        {expanded ? (
          <ChevronUp size={12} strokeWidth={1.8} className="shrink-0 opacity-65 transition-opacity group-hover:opacity-90" aria-hidden="true" />
        ) : (
          <ChevronDown size={12} strokeWidth={1.8} className="shrink-0 opacity-65 transition-opacity group-hover:opacity-90" aria-hidden="true" />
        )}
      </button>
      {expanded && (
        <div className={`mt-1 min-w-0 rounded-md px-3 py-2 ${styles.summary}`}>
          <SummaryText
            value={value}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className="ldvh-card-decision-body !text-current"
          />
        </div>
      )}
    </div>
  );
}

function WorkItemList({
  items,
  locale,
}: {
  items: Array<Record<string, unknown>>;
  locale: string;
}) {
  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <ul className="grid min-w-0 gap-3">
        {items.map((item) => (
          <WorkItem
            key={detailString(item.item_id)}
            item={item}
            locale={locale}
          />
        ))}
      </ul>
    </div>
  );
}

function WorkItem({
  item,
  locale,
}: {
  item: Record<string, unknown>;
  locale: string;
}) {
  const itemId = detailString(item.item_id);
  const hasAuxiliaryFields =
    detailStrings(item.template_keys).length > 0 ||
    [
      item.template_deviation_summary,
      item.current_summary,
      item.resume_from,
      item.blocking_summary,
    ].some((value) => typeof value === "string" && Boolean(value.trim()));
  return (
    <li className="min-w-0 overflow-hidden rounded-lg border border-cyan-400/30 bg-cyan-500/[0.03]">
      <div className="flex min-w-0 flex-wrap items-center gap-2 border-b border-cyan-400/20 px-3.5 py-2.5">
        <ObjectTypeIcon
          type="workcase"
          size={16}
          className="shrink-0"
          style={{ color: CATEGORY_COLORS.workcase }}
        />
        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-3 gap-y-1.5">
          <span className="ldvh-meta min-w-0 break-all text-cyan-700/75 dark:text-cyan-200/75">
            {itemId}
          </span>
        </div>
        <WorkItemStatusChip value={item.status} locale={locale} />
      </div>
      <div className="min-w-0 px-3.5 py-3">
        {typeof item.goal === "string" && item.goal.trim() && (
          <div className="rounded-md border border-cyan-400/15 bg-cyan-500/[0.025] px-3 py-2 dark:bg-cyan-400/[0.035]">
            <SummaryText
              value={item.goal}
              collapseThreshold={Number.MAX_SAFE_INTEGER}
              className="ldvh-detail-semantic-body font-medium !text-cyan-800/95 dark:!text-cyan-100/85"
            />
          </div>
        )}
        <WorkItemTextBlock
          fieldKey="expected_result"
          value={item.expected_result}
          locale={locale}
          variant="expectation"
        />
        <WorkItemTextBlock
          fieldKey="approach_summary"
          value={item.approach_summary}
          locale={locale}
          variant="boundary"
        />
        <WorkItemTextBlock
          fieldKey="work_item_result_summary"
          value={item.result_summary}
          locale={locale}
          variant="result"
        />
        {hasAuxiliaryFields && (
          <div className="mt-3 divide-y divide-ldvh-border/45 border-t border-cyan-400/15 pt-1">
          <InlineStringArrayField
            fieldKey="template_keys"
            value={item.template_keys}
            locale={locale}
          />
          <TextField
            fieldKey="template_deviation_summary"
            value={item.template_deviation_summary}
            locale={locale}
          />
          <TextField
            fieldKey="current_summary"
            value={item.current_summary}
            locale={locale}
          />
          <TextField
            fieldKey="resume_from"
            value={item.resume_from}
            locale={locale}
          />
          <TextField
            fieldKey="work_item_blocking_summary"
            value={item.blocking_summary}
            locale={locale}
            tone="warning"
          />
          </div>
        )}
      </div>
    </li>
  );
}

function workItemStatusStyle(value: unknown) {
  if (value === "completed") {
    return {
      Icon: CircleCheck,
      className: "border-emerald-400/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
    };
  }
  if (value === "in_progress") {
    return {
      Icon: CirclePlay,
      className: "border-sky-400/30 bg-sky-500/10 text-sky-700 dark:text-sky-200",
    };
  }
  if (value === "blocked") {
    return {
      Icon: CircleAlert,
      className: "border-rose-400/30 bg-rose-500/10 text-rose-700 dark:text-rose-200",
    };
  }
  if (value === "cancelled") {
    return {
      Icon: CircleMinus,
      className: "border-zinc-400/30 bg-zinc-500/10 text-zinc-600 dark:text-zinc-300",
    };
  }
  return {
    Icon: Circle,
    className: "border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary",
  };
}

function WorkItemStatusChip({ value, locale }: { value: unknown; locale: string }) {
  if (typeof value !== "string" || !value.trim()) return null;
  const styles = workItemStatusStyle(value);
  const { Icon } = styles;
  return (
    <span
      title={value}
      className={`ldvh-chip inline-flex shrink-0 items-center gap-1.5 rounded-md border px-2 py-0.5 ${styles.className}`}
    >
      <Icon size={13} strokeWidth={2} aria-hidden="true" />
      {getStatusLocale(value, locale)}
    </span>
  );
}

function WorkItemDetailBlock({
  fieldKey,
  locale,
  variant,
  children,
}: {
  fieldKey: string;
  locale: string;
  variant: "expectation" | "boundary" | "result";
  children: ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);
  const styles = {
    expectation: {
      heading: "text-sky-700/85 dark:text-sky-200/85",
      hover: "hover:bg-sky-500/[0.07]",
      surface: "bg-sky-500/[0.045] dark:bg-sky-400/[0.06]",
    },
    boundary: {
      heading: "text-slate-500/85 dark:text-slate-300/80",
      hover: "hover:bg-slate-500/[0.07]",
      surface: "bg-slate-500/[0.045] dark:bg-slate-400/[0.06]",
    },
    result: {
      heading: "text-emerald-700/85 dark:text-emerald-200/85",
      hover: "hover:bg-emerald-500/[0.07]",
      surface: "bg-emerald-500/[0.045] dark:bg-emerald-400/[0.06]",
    },
  }[variant];
  return (
    <div className="mt-2">
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
        className={`group -ml-1.5 inline-flex min-w-0 items-center gap-1.5 rounded px-1.5 py-1 text-left transition-colors ${styles.heading} ${styles.hover}`}
      >
        <span className="ldvh-caption-strong min-w-0 !text-current">
          {getFieldLabel(fieldKey, locale)}
        </span>
        {expanded ? (
          <ChevronUp size={12} strokeWidth={1.8} className="shrink-0 opacity-65 transition-opacity group-hover:opacity-90" aria-hidden="true" />
        ) : (
          <ChevronDown size={12} strokeWidth={1.8} className="shrink-0 opacity-65 transition-opacity group-hover:opacity-90" aria-hidden="true" />
        )}
      </button>
      {expanded && (
        <div className={`mt-1 min-w-0 rounded-md px-3 py-2 ${styles.surface}`}>
          {children}
        </div>
      )}
    </div>
  );
}

function WorkItemTextBlock({
  fieldKey,
  value,
  locale,
  variant,
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
  variant: "expectation" | "boundary" | "result";
}) {
  if (typeof value !== "string" || !value.trim()) return null;
  return (
    <WorkItemDetailBlock fieldKey={fieldKey} locale={locale} variant={variant}>
      <SummaryText
        value={value}
        collapseThreshold={Number.MAX_SAFE_INTEGER}
        className={`ldvh-card-decision-body ${
          variant === "result"
            ? "!text-emerald-950/65 dark:!text-emerald-100/75"
            : variant === "boundary"
              ? "!text-slate-600/80 dark:!text-slate-300/75"
              : "!text-sky-950/65 dark:!text-sky-100/75"
        }`}
      />
    </WorkItemDetailBlock>
  );
}

function ReviewList({
  reviews,
  locale,
}: {
  reviews: Array<Record<string, unknown>>;
  locale: string;
}) {
  const { t } = useI18n();
  return (
    <ul className="grid min-w-0 gap-3">
      {reviews.map((review, index) => {
        const reviewer = detailString(review.reviewer);
        const reviewedAt = detailString(review.reviewed_at);
        const subjectVersion = detailNumber(review.subject_version);
        const conclusion = detailString(review.conclusion);
        const feedback = detailStrings(review.feedback);
        return (
          <li
            key={`${reviewer}-${reviewedAt}-${subjectVersion ?? "version"}-${index}`}
            className="min-w-0 overflow-hidden rounded-lg border border-sky-400/25 bg-sky-500/[0.025]"
          >
            <div className="flex min-w-0 items-start gap-2 border-b border-sky-400/20 px-3.5 py-2.5">
              <Activity size={16} strokeWidth={2} className="shrink-0 text-sky-600 dark:text-sky-300" aria-hidden="true" />
              <div className="min-w-0 flex-1">
                <div className="ldvh-meta break-all text-sky-800/75 dark:text-sky-100/75">
                  {getFieldValueLabel("reviewer", reviewer, locale)}
                </div>
                {(subjectVersion !== undefined || reviewedAt) && (
                  <div className="mt-0.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5 text-ldvh-text-secondary/70">
                    {subjectVersion !== undefined && (
                      <span className="ldvh-meta-muted inline-flex items-center gap-1">
                        <span>{getFieldLabel("subject_version", locale)}</span>
                        <span className="font-mono tabular-nums">{subjectVersion}</span>
                      </span>
                    )}
                    {subjectVersion !== undefined && reviewedAt && <span className="ldvh-meta-muted" aria-hidden="true">·</span>}
                    {reviewedAt && (
                      <span className="ldvh-meta-muted inline-flex items-center gap-1">
                        <span>{getFieldLabel("reviewed_at", locale)}</span>
                        <time dateTime={reviewedAt} className="font-mono tabular-nums">{formatDateTime(reviewedAt)}</time>
                      </span>
                    )}
                  </div>
                )}
              </div>
              <ReviewConclusionChip value={conclusion} locale={locale} />
            </div>
            <div className="grid min-w-0 gap-3 px-3.5 py-3">
              <ReviewProseBlock
                label={t("objectDetail.workcaseReviewScope")}
                value={review.scope}
                variant="scope"
              />
              {feedback.length > 0 && (
                <ReviewFeedbackBlock items={feedback} locale={locale} />
              )}
              <ReviewProseBlock
                label={getFieldLabel("controller_resolution", locale)}
                value={review.controller_resolution}
                variant="resolution"
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function reviewConclusionStyle(value: string) {
  if (value === "pass") {
    return {
      Icon: CircleCheck,
      className: "border-emerald-400/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
    };
  }
  if (value === "pass_with_followups") {
    return {
      Icon: CircleAlert,
      className: "border-amber-400/30 bg-amber-500/10 text-amber-700 dark:text-amber-200",
    };
  }
  if (value === "changes_required") {
    return {
      Icon: CircleX,
      className: "border-rose-400/30 bg-rose-500/10 text-rose-700 dark:text-rose-200",
    };
  }
  return {
    Icon: CircleMinus,
    className: "border-orange-400/30 bg-orange-500/10 text-orange-700 dark:text-orange-200",
  };
}

function ReviewConclusionChip({ value, locale }: { value: string; locale: string }) {
  if (!value) return null;
  const styles = reviewConclusionStyle(value);
  const { Icon } = styles;
  return (
    <span
      title={value}
      className={`ldvh-chip inline-flex shrink-0 items-center gap-1.5 rounded-md border px-2 py-0.5 ${styles.className}`}
    >
      <Icon size={13} strokeWidth={2} aria-hidden="true" />
      {getFieldValueLabel("conclusion", value, locale)}
    </span>
  );
}

function ReviewProseBlock({
  label,
  value,
  variant,
}: {
  label: string;
  value: unknown;
  variant: "scope" | "resolution";
}) {
  const [expanded, setExpanded] = useState(variant === "resolution");
  if (typeof value !== "string" || !value.trim()) return null;
  const resolution = variant === "resolution";
  const styles = resolution
    ? {
        surface: "border-cyan-400/25 bg-cyan-500/[0.05]",
        heading: "text-cyan-700/85 dark:text-cyan-200/85",
        body: "!text-cyan-900/75 dark:!text-cyan-100/80",
      }
    : {
        surface: "border-slate-300/70 bg-slate-100/55 dark:border-slate-700/70 dark:bg-slate-800/25",
        heading: "text-slate-500/85 dark:text-slate-300/80",
        body: "!text-slate-600/80 dark:!text-slate-300/75",
      };
  return (
    <section className={`min-w-0 rounded-md border px-3 ${expanded ? "pb-1.5 pt-2.5" : "py-2.5"} ${styles.surface}`}>
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
        className={`flex w-full min-w-0 items-center justify-between gap-3 text-left ${styles.heading}`}
      >
        <span className="ldvh-card-decision-title min-w-0 text-current">{label}</span>
        {expanded ? (
          <ChevronUp size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        ) : (
          <ChevronDown size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        )}
      </button>
      {expanded && (
        <div className="mt-2 min-w-0">
          <SummaryText
            value={value}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className={`ldvh-card-decision-body ${styles.body}`}
          />
        </div>
      )}
    </section>
  );
}

function ReviewFeedbackBlock({ items, locale }: { items: string[]; locale: string }) {
  const [expanded, setExpanded] = useState(true);
  return (
    <section className={`min-w-0 rounded-md border border-amber-400/25 bg-amber-500/[0.045] px-3 ${expanded ? "pb-1.5 pt-2.5" : "py-2.5"}`}>
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
        className="flex w-full min-w-0 items-center justify-between gap-3 text-left text-amber-700/85 dark:text-amber-200/85"
      >
        <span className="ldvh-card-decision-title min-w-0 text-current">
          {getFieldLabel("feedback", locale)}
        </span>
        {expanded ? (
          <ChevronUp size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        ) : (
          <ChevronDown size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        )}
      </button>
      {expanded && (
        <ul className="mt-2 grid min-w-0 gap-1.5">
          {items.map((item, index) => (
            <li key={`${index}-${item}`} className="flex min-w-0 items-start gap-2">
              <span
                aria-hidden="true"
                className="mt-2 h-1 w-1 shrink-0 rounded-full bg-amber-500/70 dark:bg-amber-400/70"
              />
              <SummaryText
                value={item}
                collapseThreshold={Number.MAX_SAFE_INTEGER}
                className="ldvh-card-decision-body min-w-0 flex-1 !text-amber-900/75 [&_p]:my-0 dark:!text-amber-100/80"
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function ExecutionApproval({
  approval,
  locale,
}: {
  approval: Record<string, unknown>;
  locale: string;
}) {
  const { t } = useI18n();
  const subjectVersion = detailNumber(approval.subject_version);
  const approvedAt = detailString(approval.approved_at);
  const summary = detailString(approval.summary);
  const baselineFingerprint = detailString(approval.baseline_fingerprint);
  const sourceRefs = detailStrings(approval.source_refs);
  return (
    <section className="min-w-0 rounded-lg border border-violet-400/30 bg-violet-500/[0.05] px-3.5 py-3">
      <div className="flex min-w-0 items-center gap-2 text-violet-700/85 dark:text-violet-200/85">
        <CircleCheck size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        <span className="ldvh-detail-semantic-title min-w-0 text-current">
          {t("objectDetail.workcaseApprovalSummary")}
        </span>
      </div>
      {summary && (
        <div className="mt-2 min-w-0">
          <SummaryText
            value={summary}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className="ldvh-detail-semantic-body !text-violet-950/72 dark:!text-violet-100/78"
          />
        </div>
      )}
      {(subjectVersion !== undefined || approvedAt || baselineFingerprint || sourceRefs.length > 0) && (
        <div className="mt-3 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-2 border-t border-violet-400/20 pt-2.5 text-violet-900/60 dark:text-violet-100/60">
          {subjectVersion !== undefined && (
            <span className="ldvh-meta-muted inline-flex items-center gap-1.5 text-current">
              <span>{getFieldLabel("subject_version", locale)}</span>
              <span className="font-mono tabular-nums">{subjectVersion}</span>
            </span>
          )}
          {approvedAt && (
            <time dateTime={approvedAt} className="ldvh-meta-muted font-mono tabular-nums text-current">
              {formatDateTime(approvedAt)}
            </time>
          )}
          {baselineFingerprint && (
            <span className="ldvh-meta-muted inline-flex min-w-0 items-center gap-1.5 text-current">
              <span>{getFieldLabel("baseline_fingerprint", locale)}</span>
              <span className="min-w-0 break-all font-mono">{baselineFingerprint}</span>
            </span>
          )}
          {sourceRefs.length > 0 && <StringChips items={sourceRefs} />}
        </div>
      )}
    </section>
  );
}

function ExecutionAuthorization({
  authorization,
  locale,
}: {
  authorization: Record<string, unknown>;
  locale: string;
}) {
  const { t } = useI18n();
  const actions = Array.isArray(authorization.authorized_actions)
    ? authorization.authorized_actions.filter((value): value is Record<string, unknown> => Boolean(value) && typeof value === "object" && !Array.isArray(value))
    : [];
  const fields = [
    "action_ceiling",
    "allowed_adjustments",
    "verification_and_rollback",
    "out_of_bounds_handling",
  ] as const;
  return (
    <div className="grid min-w-0 gap-3">
      <section className="min-w-0 rounded-lg border border-amber-400/25 bg-amber-500/[0.025] px-3.5 py-3">
        <h3 className="ldvh-detail-semantic-title text-amber-800/85 dark:text-amber-100/85">
          {getFieldLabel("authorized_actions", locale)}
        </h3>
        {actions.length > 0 ? (
          <ul className="mt-2 grid min-w-0 gap-2">
            {actions.map((action, index) => (
              <li key={`${detailString(action.action_id)}-${index}`} className="min-w-0 rounded-md border border-amber-400/20 bg-amber-500/[0.025] px-3 py-2.5">
                {[
                  "action_id",
                  "summary",
                  "target_scope",
                  "effect_scope",
                  "risk_summary",
                  "rollback_summary",
                ].map((key) => (
                  <AuthorizationValue key={key} fieldKey={key} value={action[key]} locale={locale} />
                ))}
                <AuthorizationList fieldKey="rule_refs" value={action.rule_refs} locale={locale} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="ldvh-caption mt-1.5 text-red-400">{t("objectDetail.workcaseGateFieldMissingOrMalformed")}</p>
        )}
      </section>
      <section className="grid min-w-0 gap-2 rounded-lg border border-slate-300/50 bg-slate-500/[0.025] px-3.5 py-3 dark:border-slate-600/50">
        {fields.map((key) => (
          <AuthorizationValue key={key} fieldKey={key} value={authorization[key]} locale={locale} />
        ))}
        <AuthorizationList fieldKey="prohibited_actions" value={authorization.prohibited_actions} locale={locale} />
        <AuthorizationList fieldKey="human_prerequisites" value={authorization.human_prerequisites} locale={locale} optional />
      </section>
    </div>
  );
}

function AuthorizationValue({ fieldKey, value, locale }: { fieldKey: string; value: unknown; locale: string }) {
  const { t } = useI18n();
  const text = detailString(value);
  return (
    <div className="min-w-0 py-1">
      <p className="ldvh-meta text-ldvh-text-secondary/70">{getFieldLabel(fieldKey, locale)}</p>
      {text ? (
        <SummaryText value={text} collapseThreshold={Number.MAX_SAFE_INTEGER} className="ldvh-detail-semantic-body mt-1 !text-ldvh-text-secondary" />
      ) : (
        <p className="ldvh-caption mt-1 text-red-400">{t("objectDetail.workcaseGateFieldMissingOrMalformed")}</p>
      )}
    </div>
  );
}

function AuthorizationList({ fieldKey, value, locale, optional = false }: { fieldKey: string; value: unknown; locale: string; optional?: boolean }) {
  const { t } = useI18n();
  const items = detailStrings(value);
  if (optional && value === undefined) return null;
  return (
    <div className="min-w-0 py-1">
      <p className="ldvh-meta text-ldvh-text-secondary/70">{getFieldLabel(fieldKey, locale)}</p>
      {items.length > 0 ? <div className="mt-1"><StringChips items={items} /></div> : (
        <p className="ldvh-caption mt-1 text-red-400">{t("objectDetail.workcaseGateFieldMissingOrMalformed")}</p>
      )}
    </div>
  );
}

function InlineStringArrayField({
  fieldKey,
  value,
  locale,
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
}) {
  const items = detailStrings(value);
  if (items.length === 0) return null;
  return (
    <DetailInlineField
      label={getFieldLabel(fieldKey, locale)}
      value={<StringChips items={items} />}
    />
  );
}

function ClosureProposal({
  proposal,
  currentProjectId,
  locale,
}: {
  proposal: Record<string, unknown>;
  currentProjectId?: string;
  locale: string;
}) {
  const decisions = detailRecords(proposal.residual_decisions);
  const suggestions = detailRecords(proposal.spark_suggestions);
  const summaryOnly = decisions.length === 0 && suggestions.length === 0;
  return (
    <>
      <ClosureOutcomeSummary
        outcomeFieldKey="proposed_outcome"
        outcome={proposal.proposed_outcome}
        summaryFieldKey="proposed_disposition_summary"
        summary={proposal.proposed_disposition_summary}
        locale={locale}
        compact={summaryOnly}
      />
      {decisions.length > 0 && (
        <ResidualDecisionList
          decisions={decisions}
          currentProjectId={currentProjectId}
          locale={locale}
        />
      )}
      {suggestions.length > 0 && (
        <SparkSuggestionList items={suggestions} locale={locale} />
      )}
    </>
  );
}

function closureOutcomeStyle(value: string) {
  if (value === "completed") {
    return {
      Icon: CircleCheck,
      surface: "border-emerald-400/30 bg-emerald-500/[0.055]",
      heading: "text-emerald-700/85 dark:text-emerald-200/85",
      body: "!text-emerald-950/72 dark:!text-emerald-100/78",
    };
  }
  if (value === "partial") {
    return {
      Icon: CircleDot,
      surface: "border-amber-400/30 bg-amber-500/[0.055]",
      heading: "text-amber-700/85 dark:text-amber-200/85",
      body: "!text-amber-950/72 dark:!text-amber-100/78",
    };
  }
  if (value === "not-achieved") {
    return {
      Icon: CircleX,
      surface: "border-rose-400/30 bg-rose-500/[0.055]",
      heading: "text-rose-700/85 dark:text-rose-200/85",
      body: "!text-rose-950/72 dark:!text-rose-100/78",
    };
  }
  return {
    Icon: CircleMinus,
    surface: "border-slate-400/30 bg-slate-500/[0.05]",
    heading: "text-slate-700/85 dark:text-slate-200/85",
    body: "!text-slate-900/72 dark:!text-slate-100/78",
  };
}

function ClosureOutcomeSummary({
  outcomeFieldKey,
  outcome,
  summaryFieldKey,
  summary,
  locale,
  compact = false,
}: {
  outcomeFieldKey: "proposed_outcome" | "closure_outcome";
  outcome: unknown;
  summaryFieldKey: "proposed_disposition_summary" | "disposition_summary";
  summary: unknown;
  locale: string;
  compact?: boolean;
}) {
  const outcomeValue = detailString(outcome);
  const summaryValue = detailString(summary);
  if (!outcomeValue && !summaryValue) return null;
  const terminalStyles = closureOutcomeStyle(outcomeValue);
  const proposal = outcomeFieldKey === "proposed_outcome";
  const styles = proposal
    ? {
        Icon: ClipboardList,
        surface: "border-amber-400/30 bg-amber-500/[0.055]",
        heading: "text-amber-700/80 dark:text-amber-200/80",
        body: "!text-amber-900/75 dark:!text-amber-100/80",
      }
    : terminalStyles;
  const { Icon } = styles;

  if (compact) {
    return (
      <section className={`min-w-0 rounded-lg border ${WORKCASE_DETAIL_SEMANTIC_SURFACE_PADDING} ${styles.surface}`}>
        {summaryValue && (
          <div className="min-w-0">
            <SummaryText
              value={summaryValue}
              collapseThreshold={Number.MAX_SAFE_INTEGER}
              className={`ldvh-detail-semantic-body ${styles.body}`}
            />
          </div>
        )}
      </section>
    );
  }

  return (
    <section className={`min-w-0 rounded-lg border ${WORKCASE_DETAIL_SEMANTIC_SURFACE_PADDING} ${styles.surface}`}>
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        <div className={`flex min-w-0 flex-1 items-center gap-2 ${styles.heading}`}>
          <Icon size={WORKCASE_DETAIL_SEMANTIC_ICON_SIZE} strokeWidth={2} className="shrink-0" aria-hidden="true" />
          <span className="ldvh-detail-semantic-title min-w-0 text-current">
            {getFieldLabel(summaryFieldKey, locale)}
          </span>
        </div>
      </div>
      {summaryValue && (
        <div className="mt-2 min-w-0">
          <SummaryText
            value={summaryValue}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className={`ldvh-detail-semantic-body ${styles.body}`}
          />
        </div>
      )}
    </section>
  );
}

function ResidualDecisionList({
  decisions,
  currentProjectId,
  locale,
}: {
  decisions: Array<Record<string, unknown>>;
  currentProjectId?: string;
  locale: string;
}) {
  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">
        {getFieldLabel("residual_decisions", locale)}
      </div>
      <ul className="grid min-w-0 gap-3">
        {decisions.map((decision) => (
          <li
            key={detailString(decision.residual_id)}
            className="min-w-0 overflow-hidden rounded-lg border border-ldvh-border bg-ldvh-bg/45"
          >
            <div className="flex min-w-0 flex-wrap items-center gap-2 border-b border-ldvh-border/60 px-3.5 py-2.5">
              <span className="ldvh-meta min-w-0 flex-1 break-all text-ldvh-text-secondary/80">
                {detailString(decision.residual_id)}
              </span>
              <ResidualDispositionChip value={decision.proposed_disposition} locale={locale} />
            </div>
            <div className="grid min-w-0 gap-3 px-3.5 py-3">
              {typeof decision.summary === "string" && decision.summary.trim() && (
                <SummaryText
                  value={decision.summary}
                  collapseThreshold={Number.MAX_SAFE_INTEGER}
                  className="ldvh-detail-semantic-body !text-ldvh-text-primary/90"
                />
              )}
              {detailRecord(decision.route_target) && (
                <div className="min-w-0">
                  <div className="ldvh-caption-strong mb-1.5 text-ldvh-text-secondary/75">
                    {getFieldLabel("route_target", locale)}
                  </div>
                    <RouteTarget
                      target={detailRecord(decision.route_target)!}
                      currentProjectId={currentProjectId}
                      locale={locale}
                    />
                </div>
              )}
              {detailString(decision.spark_suggestion_id) && (
                <span className="ldvh-meta-muted inline-flex min-w-0 items-center gap-2">
                  <ObjectTypeIcon type="spark" size={13} className="shrink-0" style={{ color: CATEGORY_COLORS.spark }} />
                  <span>{detailString(decision.spark_suggestion_id)}</span>
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ResidualDispositionChip({ value, locale }: { value: unknown; locale: string }) {
  const disposition = detailString(value);
  if (!disposition) return null;
  const styles = disposition === "route_existing"
    ? { Icon: ArrowRight, className: "border-emerald-400/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200" }
    : disposition === "suggest_spark"
      ? { Icon: CircleDot, className: "border-amber-400/30 bg-amber-500/10 text-amber-700 dark:text-amber-200" }
      : { Icon: CircleMinus, className: "border-cyan-400/30 bg-cyan-500/10 text-cyan-700 dark:text-cyan-200" };
  const { Icon } = styles;
  return (
    <span title={disposition} className={`ldvh-chip inline-flex shrink-0 items-center gap-1.5 rounded-md border px-2 py-0.5 ${styles.className}`}>
      <Icon size={13} strokeWidth={2} aria-hidden="true" />
      {getFieldValueLabel("proposed_disposition", disposition, locale)}
    </span>
  );
}

/**
 * The proposed route target reads like a formal relation: same-project targets
 * resolve the current title on demand and open in the reading panel; the
 * project identity and content fingerprint stay as secondary location facts.
 */
function RouteTarget({
  target,
  currentProjectId,
  locale,
}: {
  target: Record<string, unknown>;
  currentProjectId?: string;
  locale: string;
}) {
  const projectId = detailString(target.governed_project_id);
  const factTypeKey = detailString(target.fact_type_key);
  const objectId = detailString(target.object_id);
  const fingerprint = detailString(target.content_fingerprint);
  const resolvable =
    projectId.length > 0 &&
    factTypeKey.length > 0 &&
    objectId.length > 0 &&
    projectId === currentProjectId;

  return (
    <div className="min-w-0 rounded-md border border-ldvh-border/60 bg-ldvh-bg/40 py-1">
      {resolvable ? (
        <ResolvedRouteTargetRow
          factTypeKey={factTypeKey}
          objectId={objectId}
          locale={locale}
        />
      ) : (
        <UnresolvedRouteTargetRow factTypeKey={factTypeKey} objectId={objectId} />
      )}
      {(projectId || fingerprint) && (
        <dl className="mx-1.5 grid min-w-0 gap-x-3 gap-y-1 border-t border-ldvh-border/45 px-1.5 pt-1.5 sm:grid-cols-[9rem_1fr]">
          <RouteTargetField
            fieldKey="governed_project_id"
            value={projectId}
            locale={locale}
          />
          <RouteTargetField
            fieldKey="content_fingerprint"
            value={fingerprint}
            locale={locale}
          />
        </dl>
      )}
    </div>
  );
}

function ResolvedRouteTargetRow({
  factTypeKey,
  objectId,
  locale,
}: {
  factTypeKey: string;
  objectId: string;
  locale: string;
}) {
  const { t } = useI18n();
  const { isOpen: panelOpen, content: panelContent, openPanel } = usePanel();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    fetchObjectDetail(factTypeKey, objectId)
      .then((value) => {
        if (!cancelled) setDetail(value);
      })
      .catch(() => {
        if (!cancelled) setDetail(null);
      });
    return () => {
      cancelled = true;
    };
  }, [factTypeKey, objectId]);

  const readMeta = getFactReadMeta(detail?.data);
  const source = (detail?.data ?? {}) as {
    title?: unknown;
    title_en?: unknown;
    title_zh?: unknown;
  };
  const localized = locale === "en" ? source.title_en : source.title_zh;
  const title =
    detail && isReadableFact(readMeta)
      ? typeof localized === "string" && localized.trim()
        ? localized
        : typeof source.title === "string" && source.title.trim()
          ? source.title
          : "—"
      : "—";
  const canonicalPath = isReadableFact(readMeta) ? readMeta.canonicalPath : undefined;
  const typeColor = CATEGORY_COLORS[factTypeKey] || CATEGORY_COLORS.other;
  const isCurrentPanelOpen = Boolean(
    panelOpen &&
      panelContent?.type === "object" &&
      panelContent.objectType === factTypeKey &&
      panelContent.objectId === objectId,
  );
  const PanelIcon = isCurrentPanelOpen ? ChevronLeft : ChevronRight;
  const openLabel = t("objectDetail.openReadingPanel");
  const open = () =>
    openPanel({ type: "object", title, objectType: factTypeKey, objectId });
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    open();
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={open}
      onKeyDown={onKeyDown}
      title={openLabel}
      className="group flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-1.5 py-2 text-left transition-colors hover:bg-ldvh-border/25 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ldvh-accent/50"
    >
      <ObjectTypeIcon
        type={factTypeKey}
        size={13}
        className="shrink-0"
        style={{ color: typeColor }}
      />
      <span className="ldvh-meta-primary min-w-0 flex-1 truncate group-hover:text-ldvh-accent">
        {title}
      </span>
      <span className="ldvh-meta-muted shrink-0">{objectId}</span>
      <CopyPathButton path={canonicalPath} />
      <PanelIcon
        size={16}
        className="shrink-0 text-ldvh-text-secondary/70 transition-colors group-hover:text-ldvh-accent"
        aria-hidden="true"
      />
    </div>
  );
}

/** Cross-project or incomplete targets keep their known stable identity without guessing a title. */
function UnresolvedRouteTargetRow({
  factTypeKey,
  objectId,
}: {
  factTypeKey: string;
  objectId: string;
}) {
  const typeColor = factTypeKey
    ? CATEGORY_COLORS[factTypeKey] || CATEGORY_COLORS.other
    : CATEGORY_COLORS.other;
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-md px-1.5 py-2">
      {factTypeKey && (
        <ObjectTypeIcon
          type={factTypeKey}
          size={13}
          className="shrink-0"
          style={{ color: typeColor }}
        />
      )}
      <span className="ldvh-meta-primary min-w-0 flex-1 truncate">
        {objectId || "—"}
      </span>
    </div>
  );
}

function RouteTargetField({
  fieldKey,
  value,
  locale,
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
}) {
  if (typeof value !== "string" || !value.trim()) return null;
  return (
    <>
      <dt className="ldvh-caption-strong text-ldvh-text-secondary">
        {getFieldLabel(fieldKey, locale)}
      </dt>
      <dd className="ldvh-meta-primary min-w-0 break-all font-mono">{value}</dd>
    </>
  );
}

function TerminalResidualList({
  items,
  locale,
}: {
  items: Array<Record<string, unknown>>;
  locale: string;
}) {
  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">
        {getFieldLabel("residual_responsibilities", locale)}
      </div>
      <ul className="grid min-w-0 gap-2">
        {items.map((item) => (
          <li
            key={detailString(item.residual_id)}
            className="min-w-0 overflow-hidden rounded-lg border border-cyan-400/25 bg-cyan-500/[0.035]"
          >
            <div className="flex min-w-0 items-center gap-2 border-b border-cyan-400/20 px-3.5 py-2.5 text-cyan-700/85 dark:text-cyan-200/85">
              <CircleMinus size={16} strokeWidth={2} className="shrink-0" aria-hidden="true" />
              <span className="ldvh-meta min-w-0 flex-1 break-all text-current/75">
                {detailString(item.residual_id)}
              </span>
            </div>
            <div className="min-w-0 px-3.5 py-3">
              {typeof item.summary === "string" && item.summary.trim() && (
                <SummaryText
                  value={item.summary}
                  collapseThreshold={Number.MAX_SAFE_INTEGER}
                  className="ldvh-detail-semantic-body !text-cyan-950/72 dark:!text-cyan-100/78"
                />
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SparkSuggestionList({
  items,
  locale,
}: {
  items: Array<Record<string, unknown>>;
  locale: string;
}) {
  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">
        {getFieldLabel("spark_suggestions", locale)}
      </div>
      <ul className="grid min-w-0 gap-2">
        {items.map((item) => (
          <li
            key={detailString(item.suggestion_id)}
            className="min-w-0 overflow-hidden rounded-lg border border-amber-400/25 bg-amber-500/[0.03]"
          >
            <div className="flex min-w-0 flex-wrap items-center gap-2 border-b border-amber-400/20 px-3.5 py-2.5">
              <ObjectTypeIcon type="spark" size={16} className="shrink-0" style={{ color: CATEGORY_COLORS.spark }} />
              <span className="ldvh-meta min-w-0 flex-1 break-all text-amber-800/75 dark:text-amber-100/75">
                {detailString(item.suggestion_id)}
              </span>
              {detailString(item.suggestion_kind) && (
                <span className="ldvh-chip shrink-0 rounded-md border border-amber-400/30 bg-amber-500/10 px-2 py-0.5 text-amber-700 dark:text-amber-200">
                  {getFieldValueLabel("suggestion_kind", detailString(item.suggestion_kind), locale)}
                </span>
              )}
            </div>
            <div className="grid min-w-0 gap-3 px-3.5 py-3">
              {typeof item.summary === "string" && item.summary.trim() && (
                <SummaryText
                  value={item.summary}
                  collapseThreshold={Number.MAX_SAFE_INTEGER}
                  className="ldvh-detail-semantic-body font-medium !text-amber-950/72 dark:!text-amber-100/78"
                />
              )}
              <SuggestionDetail fieldKey="restriction_reason" value={item.restriction_reason} locale={locale} variant="restriction" />
              <SuggestionDetail fieldKey="impact_summary" value={item.impact_summary} locale={locale} variant="plain" />
              <SuggestionDetail fieldKey="resume_condition" value={item.resume_condition} locale={locale} variant="resume" />
              <SuggestionDetail fieldKey="follow_up_summary" value={item.follow_up_summary} locale={locale} variant="plain" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SuggestionDetail({
  fieldKey,
  value,
  locale,
  variant,
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
  variant: "plain" | "restriction" | "resume";
}) {
  if (typeof value !== "string" || !value.trim()) return null;
  const className = variant === "restriction"
    ? "rounded-md border border-rose-400/25 bg-rose-500/[0.04] px-3 py-2.5"
    : variant === "resume"
      ? "rounded-md border border-emerald-400/25 bg-emerald-500/[0.04] px-3 py-2.5"
      : "min-w-0";
  const headingClass = variant === "restriction"
    ? "text-rose-700/85 dark:text-rose-200/85"
    : variant === "resume"
      ? "text-emerald-700/85 dark:text-emerald-200/85"
      : "text-ldvh-text-secondary/75";
  const bodyClass = variant === "restriction"
    ? "!text-rose-950/72 dark:!text-rose-100/78"
    : variant === "resume"
      ? "!text-emerald-950/72 dark:!text-emerald-100/78"
      : "!text-ldvh-text-secondary/85";
  return (
    <div className={className}>
      <div className={`ldvh-card-decision-title mb-1.5 ${headingClass}`}>
        {getFieldLabel(fieldKey, locale)}
      </div>
      <SummaryText value={value} collapseThreshold={Number.MAX_SAFE_INTEGER} className={`ldvh-card-decision-body ${bodyClass}`} />
    </div>
  );
}

function StringChips({ items }: { items: string[] }) {
  return (
    <div className="flex min-w-0 flex-wrap gap-1.5">
      {items.map((item) => (
        <span
          key={item}
          className="ldvh-chip max-w-full break-all rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-0.5 text-ldvh-text-primary"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function detailRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function detailRecords(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value) || !value.every((item) => detailRecord(item)))
    return [];
  return value as Array<Record<string, unknown>>;
}

function detailString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function detailStrings(value: unknown): string[] {
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string"))
    return [];
  return value as string[];
}

function detailNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
