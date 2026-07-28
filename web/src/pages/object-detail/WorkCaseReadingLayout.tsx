import { useEffect, useState, type KeyboardEvent, type ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
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
      {responsibilityVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseResponsibility")}
          locale={locale}
        >
          <ProseField fieldKey="goal" value={obj.goal} locale={locale} />
          <FieldIssueRow fieldKey="goal" issue={issueFor("goal")} locale={locale} />
          <ProseField fieldKey="scope" value={obj.scope} locale={locale} />
          <FieldIssueRow fieldKey="scope" issue={issueFor("scope")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {snapshotVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseCurrentSnapshot")}
          locale={locale}
        >
          <EnumField
            fieldKey="phase"
            value={obj.phase}
            locale={locale}
            statusValue
          />
          <FieldIssueRow fieldKey="phase" issue={issueFor("phase")} locale={locale} />
          <ProseField fieldKey="summary" value={obj.summary} locale={locale} />
          <FieldIssueRow fieldKey="summary" issue={issueFor("summary")} locale={locale} />
          <ProseField
            fieldKey="resume_from"
            value={obj.resume_from}
            locale={locale}
          />
          <FieldIssueRow fieldKey="resume_from" issue={issueFor("resume_from")} locale={locale} />
          <ProseField
            fieldKey="waiting_on"
            value={obj.waiting_on}
            locale={locale}
          />
          <FieldIssueRow fieldKey="waiting_on" issue={issueFor("waiting_on")} locale={locale} />
          <ProseField
            fieldKey="blocking_summary"
            value={obj.blocking_summary}
            locale={locale}
            tone="warning"
          />
          <FieldIssueRow fieldKey="blocking_summary" issue={issueFor("blocking_summary")} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {criteriaVisible && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseSuccessCriteria")}
          locale={locale}
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
        >
          <NumberField
            fieldKey="plan_version"
            value={obj.plan_version}
            locale={locale}
          />
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
  children,
}: {
  title: string;
  note?: string;
  locale: string;
  children: ReactNode;
}) {
  const [state, setState] = useState<ReadingNodeState>("expanded");
  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className="ldvh-study-node-content">
        {note && (
          <p className="ldvh-caption mb-2 border-b border-ldvh-border/60 pb-2 text-ldvh-text-secondary">
            {note}
          </p>
        )}
        <div className="divide-y divide-ldvh-border/60">{children}</div>
      </div>
    </ReadingNodeSection>
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
      value={<span className="ldvh-meta-primary font-mono">{value}</span>}
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
            className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg/55 px-3 py-3"
          >
            <div className="divide-y divide-ldvh-border/45">
              <MonoField
                fieldKey="criterion_id"
                value={criterionId}
                locale={locale}
              />
              <TextField
                fieldKey="statement"
                value={definition.statement}
                locale={locale}
              />
              {result && (
                <EnumField
                  fieldKey="outcome"
                  value={result.outcome}
                  locale={locale}
                />
              )}
              {result && (
                <TextField
                  fieldKey="summary"
                  value={result.summary}
                  locale={locale}
                />
              )}
            </div>
          </li>
        );
      })}
    </ul>
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
      <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">
        {getFieldLabel("work_items", locale)}
      </div>
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
  return (
    <li className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg/55 px-3 py-3">
      <div className="divide-y divide-ldvh-border/45">
        <MonoField fieldKey="item_id" value={item.item_id} locale={locale} />
        <EnumField
          fieldKey="status"
          value={item.status}
          locale={locale}
          statusValue
        />
        <TextField fieldKey="goal" value={item.goal} locale={locale} />
        <TextField
          fieldKey="expected_result"
          value={item.expected_result}
          locale={locale}
        />
        <InlineStringArrayField
          fieldKey="depends_on"
          value={item.depends_on}
          locale={locale}
        />
        <TextField
          fieldKey="approach_summary"
          value={item.approach_summary}
          locale={locale}
        />
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
        <TextField
          fieldKey="work_item_result_summary"
          value={item.result_summary}
          locale={locale}
        />
      </div>
    </li>
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
        <time dateTime={value} className="ldvh-meta-primary">
          {value}
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
