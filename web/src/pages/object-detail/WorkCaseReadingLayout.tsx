import { useEffect, useState, type KeyboardEvent, type ReactNode } from "react";
import {
  Activity,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Circle,
  CircleCheck,
  CircleDot,
  CircleHelp,
  CircleMinus,
  CirclePlay,
  CircleX,
  Clock3,
  ListChecks,
  ScanLine,
  Target,
} from "lucide-react";
import SummaryText from "@/components/SummaryText";
import CopyPathButton from "@/components/CopyPathButton";
import { ObjectTypeIcon } from "@/components/SemanticIcon";
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
          <SnapshotPhaseField value={obj.phase} locale={locale} />
          <FieldIssueRow fieldKey="phase" issue={issueFor("phase")} locale={locale} />
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
        >
          {creationReviews.length > 0 && (
            <ReviewList reviews={creationReviews} locale={locale} />
          )}
          <FieldIssueRow fieldKey="creation_reviews" issue={issueFor("creation_reviews")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {approvalVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseExecutionApproval")}
          note={t("objectDetail.workcaseExecutionApprovalBoundary")}
          locale={locale}
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
        >
          <NumberField
            fieldKey="result_version"
            value={obj.result_version}
            locale={locale}
          />
          <FieldIssueRow fieldKey="result_version" issue={issueFor("result_version")} locale={locale} />
          <ProseField
            fieldKey="result_summary"
            value={obj.result_summary}
            locale={locale}
          />
          <FieldIssueRow fieldKey="result_summary" issue={issueFor("result_summary")} locale={locale} />
          <ProseField
            fieldKey="validation_summary"
            value={obj.validation_summary}
            locale={locale}
          />
          <FieldIssueRow fieldKey="validation_summary" issue={issueFor("validation_summary")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {controllerCheckVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseControllerCheck")}
          note={t("objectDetail.workcaseControllerCheckBoundary")}
          locale={locale}
        >
          <ProseField
            fieldKey="controller_check_summary"
            value={obj.controller_check_summary}
            locale={locale}
            showLabel={false}
          />
          <FieldIssueRow fieldKey="controller_check_summary" issue={issueFor("controller_check_summary")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {resultReviewsVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseResultReviews")}
          note={t("objectDetail.workcaseResultReviewsBoundary")}
          locale={locale}
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
        >
          <EnumField
            fieldKey="closure_outcome"
            value={obj.closure_outcome}
            locale={locale}
          />
          <FieldIssueRow fieldKey="closure_outcome" issue={issueFor("closure_outcome")} locale={locale} />
          <ProseField
            fieldKey="disposition_summary"
            value={obj.disposition_summary}
            locale={locale}
          />
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
          title={t("objectDetail.workcaseRelations")}
          locale={locale}
        >
          <FieldIssueRow fieldKey="relations" issue={relationsIssue} locale={locale} />
        </WorkCaseReadingNode>
      ) : (
        <FactAssociationsSection
          obj={obj}
          locale={locale}
          title={t("objectDetail.workcaseRelations")}
          showRelationKey
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
        {note && (
          <p className="ldvh-caption mb-2 border-b border-ldvh-border/60 pb-2 text-ldvh-text-secondary">
            {note}
          </p>
        )}
        <div className={contentVariant === "semantic" ? "grid gap-3" : "divide-y divide-ldvh-border/60"}>
          {children}
        </div>
      </div>
    </ReadingNodeSection>
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
  if (typeof value !== "string" || !value.trim()) return null;
  const Icon = tone === "goal" ? Target : ScanLine;
  const surfaceClass = tone === "goal"
    ? "border-violet-400/35 bg-violet-500/[0.055]"
    : "border-cyan-500/30 bg-cyan-500/[0.045]";
  const headingClass = tone === "goal"
    ? "text-violet-700 dark:text-violet-300"
    : "text-cyan-700 dark:text-cyan-300";
  const bodyClass = tone === "goal"
    ? "text-violet-950/85 dark:text-violet-100/85"
    : "text-cyan-950/85 dark:text-cyan-100/85";

  return (
    <section className={`min-w-0 rounded-lg border px-3.5 py-3 ${surfaceClass}`}>
      <div className={`flex min-w-0 items-center gap-2 ${headingClass}`}>
        <Icon size={16} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        <span className="ldvh-card-title-prominent min-w-0 text-current">
          {getFieldLabel(fieldKey, locale)}
        </span>
      </div>
      <div className="mt-2 min-w-0">
        <SummaryText
          value={value}
          collapseThreshold={Number.MAX_SAFE_INTEGER}
          className={`ldvh-body ${bodyClass}`}
        />
      </div>
    </section>
  );
}

function SnapshotPhaseField({
  value,
  locale,
}: {
  value: unknown;
  locale: string;
}) {
  if (typeof value !== "string" || !value.trim()) return null;
  return (
    <section className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-violet-400/35 bg-violet-500/[0.055] px-3.5 py-2.5">
      <div className="flex min-w-0 items-center gap-2 text-violet-700 dark:text-violet-300">
        <CircleDot size={16} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        <span className="ldvh-card-title-prominent min-w-0 text-current">
          {getFieldLabel("phase", locale)}
        </span>
      </div>
      <span
        title={value}
        className="ldvh-chip inline-flex shrink-0 rounded-md border border-violet-400/30 bg-violet-500/10 px-2 py-0.5 text-violet-700 dark:text-violet-200"
      >
        {getStatusLocale(value, locale)}
      </span>
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
      heading: "text-sky-700 dark:text-sky-300",
      body: "text-sky-950/85 dark:text-sky-100/85",
    },
    resume_from: {
      Icon: ArrowRight,
      surface: "border-emerald-400/30 bg-emerald-500/[0.045]",
      heading: "text-emerald-700 dark:text-emerald-300",
      body: "text-emerald-950/85 dark:text-emerald-100/85",
    },
    waiting_on: {
      Icon: Clock3,
      surface: "border-amber-400/35 bg-amber-500/[0.055]",
      heading: "text-amber-700 dark:text-amber-300",
      body: "text-amber-950/85 dark:text-amber-100/85",
    },
    blocking_summary: {
      Icon: CircleAlert,
      surface: "border-rose-400/35 bg-rose-500/[0.055]",
      heading: "text-rose-700 dark:text-rose-300",
      body: "text-rose-950/85 dark:text-rose-100/85",
    },
  }[fieldKey];
  const { Icon } = styles;

  return (
    <section className={`min-w-0 rounded-lg border px-3.5 py-3 ${styles.surface}`}>
      <div className={`flex min-w-0 items-center gap-2 ${styles.heading}`}>
        <Icon size={16} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        <span className="ldvh-card-title-prominent min-w-0 text-current">
          {getFieldLabel(fieldKey, locale)}
        </span>
      </div>
      <div className="mt-2 min-w-0">
        <SummaryText
          value={value}
          collapseThreshold={Number.MAX_SAFE_INTEGER}
          className={`ldvh-body ${styles.body}`}
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
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
  tone?: "default" | "warning";
  label?: string;
  showLabel?: boolean;
}) {
  if (typeof value !== "string" || !value.trim()) return null;
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

function NumberField({
  fieldKey,
  value,
  locale,
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
}) {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return (
    <DetailInlineField
      label={getFieldLabel(fieldKey, locale)}
      value={
        <span className="ldvh-meta-primary inline-flex h-6 items-center font-mono tabular-nums">
          {value}
        </span>
      }
    />
  );
}

function MonoField({
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
    <DetailInlineField
      label={getFieldLabel(fieldKey, locale)}
      value={
        <span className="ldvh-meta-primary break-all font-mono">{value}</span>
      }
    />
  );
}

function EnumField({
  fieldKey,
  value,
  locale,
  statusValue = false,
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
  statusValue?: boolean;
}) {
  if (typeof value !== "string" || !value.trim()) return null;
  const label = statusValue
    ? getStatusLocale(value, locale)
    : getFieldValueLabel(fieldKey, value, locale);
  return (
    <DetailInlineField
      label={getFieldLabel(fieldKey, locale)}
      value={<ValueChip value={value} label={label} />}
    />
  );
}

function ValueChip({ value, label }: { value: string; label: string }) {
  return (
    <span
      title={value}
      className="ldvh-chip inline-flex rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-0.5 text-ldvh-text-primary"
    >
      {label}
    </span>
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
      {definitions.map((definition) => {
        const criterionId = detailString(definition.criterion_id);
        const result = resultById.get(criterionId);
        return (
          <li
            key={criterionId}
            className="min-w-0 overflow-hidden rounded-lg border border-blue-400/30 bg-blue-500/[0.035]"
          >
            <div className="flex min-w-0 flex-wrap items-center gap-2 border-b border-blue-400/20 px-3.5 py-2.5">
              <ListChecks size={16} strokeWidth={2} className="shrink-0 text-blue-600 dark:text-blue-300" aria-hidden="true" />
              <span className="ldvh-meta min-w-0 flex-1 break-all text-blue-700/75 dark:text-blue-200/75">
                {criterionId}
              </span>
              {result && <CriterionOutcomeChip value={result.outcome} locale={locale} />}
            </div>
            <div className="min-w-0 px-3.5 py-3">
              {typeof definition.statement === "string" && definition.statement.trim() && (
                <SummaryText
                  value={definition.statement}
                  collapseThreshold={Number.MAX_SAFE_INTEGER}
                  className="ldvh-body text-blue-950/90 dark:text-blue-100/90"
                />
              )}
              {result && typeof result.summary === "string" && result.summary.trim() && (
                <CriterionResultSummary
                  outcome={result.outcome}
                  value={result.summary}
                  label={t("objectDetail.workcaseCriterionResultSummary")}
                />
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function criterionOutcomeStyle(value: unknown) {
  if (value === "satisfied") {
    return {
      Icon: CircleCheck,
      chip: "border-emerald-400/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
      summary: "border-emerald-400/25 bg-emerald-500/[0.055] text-emerald-950/85 dark:text-emerald-100/85",
      heading: "text-emerald-700 dark:text-emerald-300",
    };
  }
  if (value === "not_satisfied") {
    return {
      Icon: CircleX,
      chip: "border-rose-400/30 bg-rose-500/10 text-rose-700 dark:text-rose-200",
      summary: "border-rose-400/25 bg-rose-500/[0.055] text-rose-950/85 dark:text-rose-100/85",
      heading: "text-rose-700 dark:text-rose-300",
    };
  }
  if (value === "not_verified") {
    return {
      Icon: CircleHelp,
      chip: "border-amber-400/30 bg-amber-500/10 text-amber-700 dark:text-amber-200",
      summary: "border-amber-400/25 bg-amber-500/[0.055] text-amber-950/85 dark:text-amber-100/85",
      heading: "text-amber-700 dark:text-amber-300",
    };
  }
  return {
    Icon: CircleDot,
    chip: "border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary",
    summary: "border-ldvh-border bg-ldvh-bg/60 text-ldvh-text-secondary",
    heading: "text-ldvh-text-secondary",
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
  const styles = criterionOutcomeStyle(outcome);
  const { Icon } = styles;
  return (
    <div className={`mt-3 rounded-md border px-3 py-2.5 ${styles.summary}`}>
      <div className={`ldvh-caption-strong mb-1.5 flex items-center gap-1.5 ${styles.heading}`}>
        <Icon size={13} strokeWidth={2} className="shrink-0" aria-hidden="true" />
        <span>{label}</span>
      </div>
      <SummaryText
        value={value}
        collapseThreshold={Number.MAX_SAFE_INTEGER}
        className="ldvh-body text-current"
      />
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
          <WorkItemDependencyMeta value={item.depends_on} locale={locale} />
        </div>
        <WorkItemStatusChip value={item.status} locale={locale} />
      </div>
      <div className="min-w-0 px-3.5 py-3">
        {typeof item.goal === "string" && item.goal.trim() && (
          <SummaryText
            value={item.goal}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className="ldvh-body font-medium text-cyan-950/80 dark:text-cyan-100/85"
          />
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
  if (variant === "boundary") {
    return (
      <div className="mt-3 px-0.5 pt-0.5">
        <div className="ldvh-caption-strong mb-1.5 text-ldvh-text-secondary/75">
          {getFieldLabel(fieldKey, locale)}
        </div>
        {children}
      </div>
    );
  }

  const result = variant === "result";
  return (
    <div
      className={`mt-3 rounded-md border px-3 py-2.5 ${
        result
          ? "border-emerald-400/30 bg-emerald-500/[0.06]"
          : "border-cyan-400/25 bg-cyan-500/[0.075]"
      }`}
    >
      <div
        className={`ldvh-caption-strong mb-1.5 flex items-center gap-1.5 ${
          result
            ? "text-emerald-700 dark:text-emerald-300"
            : "text-cyan-700 dark:text-cyan-300"
        }`}
      >
        {result && <CircleCheck size={13} strokeWidth={2} aria-hidden="true" />}
        {getFieldLabel(fieldKey, locale)}
      </div>
      {children}
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
        className={`ldvh-body ${
          variant === "result"
            ? "text-emerald-950/80 dark:text-emerald-100/85"
            : variant === "boundary"
              ? "text-ldvh-text-secondary/85"
              : "text-cyan-950/85 dark:text-cyan-100/85"
        }`}
      />
    </WorkItemDetailBlock>
  );
}

function WorkItemDependencyMeta({
  value,
  locale,
}: {
  value: unknown;
  locale: string;
}) {
  const items = detailStrings(value);
  if (items.length === 0) return null;
  return (
    <span className="inline-flex min-w-0 flex-wrap items-center gap-1.5 text-ldvh-text-secondary/70">
      <span className="ldvh-meta-muted shrink-0">{getFieldLabel("depends_on", locale)}</span>
      {items.map((item) => (
        <span
          key={item}
          className="ldvh-chip rounded-md border border-cyan-400/20 bg-ldvh-bg/65 px-1.5 py-0.5 font-mono text-cyan-700/70 dark:text-cyan-200/70"
        >
          {item}
        </span>
      ))}
    </span>
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
            className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg/55 px-3 py-3"
          >
            <div className="divide-y divide-ldvh-border/45">
              <TextValueField
                label={getFieldLabel("reviewer", locale)}
                value={reviewer}
              />
              <DateField
                fieldKey="reviewed_at"
                value={reviewedAt}
                locale={locale}
              />
              <NumberField
                fieldKey="subject_version"
                value={subjectVersion}
                locale={locale}
              />
              <TextValueField
                label={t("objectDetail.workcaseReviewScope")}
                value={review.scope}
              />
              <EnumField
                fieldKey="conclusion"
                value={conclusion}
                locale={locale}
              />
              {feedback.length > 0 && (
                <InlineStringArrayField
                  fieldKey="feedback"
                  value={feedback}
                  locale={locale}
                />
              )}
              <TextField
                fieldKey="controller_resolution"
                value={review.controller_resolution}
                locale={locale}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function TextValueField({ label, value }: { label: string; value: unknown }) {
  if (typeof value !== "string" || !value.trim()) return null;
  return (
    <DetailInlineField
      label={label}
      value={
        <SummaryText
          value={value}
          collapseThreshold={Number.MAX_SAFE_INTEGER}
        />
      }
    />
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
  return (
    <>
      <NumberField
        fieldKey="subject_version"
        value={approval.subject_version}
        locale={locale}
      />
      <DateField
        fieldKey="approved_at"
        value={approval.approved_at}
        locale={locale}
      />
      <TextField
        fieldKey="summary"
        value={approval.summary}
        locale={locale}
        label={t("objectDetail.workcaseApprovalSummary")}
      />
      <InlineStringArrayField
        fieldKey="source_refs"
        value={approval.source_refs}
        locale={locale}
      />
    </>
  );
}

function DateField({
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
    <DetailInlineField
      label={getFieldLabel(fieldKey, locale)}
      value={
        <time
          dateTime={value}
          className="ldvh-meta-primary inline-flex h-6 items-center font-mono tabular-nums"
        >
          {formatDateTime(value)}
        </time>
      }
    />
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
  return (
    <>
      <EnumField
        fieldKey="proposed_outcome"
        value={proposal.proposed_outcome}
        locale={locale}
      />
      <ProseField
        fieldKey="proposed_disposition_summary"
        value={proposal.proposed_disposition_summary}
        locale={locale}
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
            className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg/55 px-3 py-3"
          >
            <div className="divide-y divide-ldvh-border/45">
              <MonoField
                fieldKey="residual_id"
                value={decision.residual_id}
                locale={locale}
              />
              <EnumField
                fieldKey="proposed_disposition"
                value={decision.proposed_disposition}
                locale={locale}
              />
              <TextField
                fieldKey="summary"
                value={decision.summary}
                locale={locale}
              />
              {detailRecord(decision.route_target) && (
                <DetailInlineField
                  label={getFieldLabel("route_target", locale)}
                  value={
                    <RouteTarget
                      target={detailRecord(decision.route_target)!}
                      currentProjectId={currentProjectId}
                      locale={locale}
                    />
                  }
                />
              )}
              <MonoField
                fieldKey="spark_suggestion_id"
                value={decision.spark_suggestion_id}
                locale={locale}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
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
            className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg/55 px-3 py-3"
          >
            <div className="divide-y divide-ldvh-border/45">
              <MonoField
                fieldKey="residual_id"
                value={item.residual_id}
                locale={locale}
              />
              <TextField
                fieldKey="summary"
                value={item.summary}
                locale={locale}
              />
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
            className="rounded-md border border-ldvh-border bg-ldvh-bg/55 px-3 py-2.5"
          >
            <div className="divide-y divide-ldvh-border/45">
              <MonoField
                fieldKey="spark_suggestion_id"
                value={item.suggestion_id}
                locale={locale}
              />
              <EnumField
                fieldKey="suggestion_kind"
                value={item.suggestion_kind}
                locale={locale}
              />
              <TextField
                fieldKey="summary"
                value={item.summary}
                locale={locale}
              />
              <TextField
                fieldKey="restriction_reason"
                value={item.restriction_reason}
                locale={locale}
              />
              <TextField
                fieldKey="impact_summary"
                value={item.impact_summary}
                locale={locale}
              />
              <TextField
                fieldKey="resume_condition"
                value={item.resume_condition}
                locale={locale}
              />
              <TextField
                fieldKey="follow_up_summary"
                value={item.follow_up_summary}
                locale={locale}
              />
            </div>
          </li>
        ))}
      </ul>
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
