import { useState, type ReactNode } from "react";
import SummaryText from "@/components/SummaryText";
import { useI18n } from "@/i18n/context";
import {
  getFieldLabel,
  getFieldValueLabel,
  getStatusLocale,
} from "@/i18n/locales";
import type { WorkCaseDetailData } from "@/utils/api";
import { projectCurrentWorkCaseDetail } from "@/shared/workcaseDetailProjection";
import { FactAssociationsSection } from "@/pages/object-detail/FactAssociationsSection";
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

  return (
    <div className="mb-6 flex flex-col gap-5">
      {detail.responsibility && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseResponsibility")}
          locale={locale}
        >
          <TextField fieldKey="goal" value={obj.goal} locale={locale} />
          <TextField fieldKey="scope" value={obj.scope} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {detail.currentSnapshot && (
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
          <TextField fieldKey="summary" value={obj.summary} locale={locale} />
          <TextField
            fieldKey="resume_from"
            value={obj.resume_from}
            locale={locale}
          />
          <TextField
            fieldKey="waiting_on"
            value={obj.waiting_on}
            locale={locale}
          />
          <TextField
            fieldKey="blocking_summary"
            value={obj.blocking_summary}
            locale={locale}
            tone="warning"
          />
        </WorkCaseReadingNode>
      )}

      {criteria.length > 0 && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseSuccessCriteria")}
          locale={locale}
        >
          <SuccessCriteria
            definitions={criteria}
            results={criterionResults}
            locale={locale}
          />
        </WorkCaseReadingNode>
      )}

      {detail.planAndItems && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcasePlanAndItems")}
          locale={locale}
        >
          <NumberField
            fieldKey="plan_version"
            value={obj.plan_version}
            locale={locale}
          />
          {workItems.length > 0 && (
            <WorkItemList items={workItems} locale={locale} />
          )}
        </WorkCaseReadingNode>
      )}

      {creationReviews.length > 0 && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseCreationReviews")}
          note={t("objectDetail.workcaseCreationReviewsBoundary")}
          locale={locale}
        >
          <ReviewList reviews={creationReviews} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {executionApproval && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseExecutionApproval")}
          note={t("objectDetail.workcaseExecutionApprovalBoundary")}
          locale={locale}
        >
          <ExecutionApproval approval={executionApproval} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {detail.resultAndValidation && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseResultAndValidation")}
          locale={locale}
        >
          <NumberField
            fieldKey="result_version"
            value={obj.result_version}
            locale={locale}
          />
          <TextField
            fieldKey="result_summary"
            value={obj.result_summary}
            locale={locale}
          />
          <TextField
            fieldKey="validation_summary"
            value={obj.validation_summary}
            locale={locale}
          />
        </WorkCaseReadingNode>
      )}

      {detail.controllerCheck && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseControllerCheck")}
          note={t("objectDetail.workcaseControllerCheckBoundary")}
          locale={locale}
        >
          <TextField
            fieldKey="controller_check_summary"
            value={obj.controller_check_summary}
            locale={locale}
          />
        </WorkCaseReadingNode>
      )}

      {resultReviews.length > 0 && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseResultReviews")}
          note={t("objectDetail.workcaseResultReviewsBoundary")}
          locale={locale}
        >
          <ReviewList reviews={resultReviews} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {closureProposal && (
        <WorkCaseReadingNode
          title={t("objectDetail.workcaseClosureProposal")}
          note={t("objectDetail.workcaseClosureProposalBoundary")}
          locale={locale}
        >
          <ClosureProposal proposal={closureProposal} locale={locale} />
        </WorkCaseReadingNode>
      )}

      {detail.terminalDisposition && (
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
          <TextField
            fieldKey="disposition_summary"
            value={obj.disposition_summary}
            locale={locale}
          />
          {terminalResiduals.length > 0 && (
            <TerminalResidualList items={terminalResiduals} locale={locale} />
          )}
          {terminalSuggestions.length > 0 && (
            <SparkSuggestionList items={terminalSuggestions} locale={locale} />
          )}
        </WorkCaseReadingNode>
      )}

      <FactAssociationsSection
        obj={obj}
        locale={locale}
        title={t("objectDetail.workcaseRelations")}
        showRelationKey
      />

      {urls.length > 0 && (
        <RelatedContentSection
          entries={[["urls", urls]]}
          locale={locale}
          title={t("objectDetail.workcaseUrls")}
        />
      )}
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
  locale,
}: {
  proposal: Record<string, unknown>;
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
      <TextField
        fieldKey="proposed_disposition_summary"
        value={proposal.proposed_disposition_summary}
        locale={locale}
      />
      {decisions.length > 0 && (
        <ResidualDecisionList decisions={decisions} locale={locale} />
      )}
      {suggestions.length > 0 && (
        <SparkSuggestionList items={suggestions} locale={locale} />
      )}
    </>
  );
}

function ResidualDecisionList({
  decisions,
  locale,
}: {
  decisions: Array<Record<string, unknown>>;
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

function RouteTarget({
  target,
  locale,
}: {
  target: Record<string, unknown>;
  locale: string;
}) {
  return (
    <dl className="grid min-w-0 gap-x-3 gap-y-1.5 sm:grid-cols-[9rem_1fr]">
      {[
        "governed_project_id",
        "fact_type_key",
        "object_id",
        "content_fingerprint",
      ].map((fieldKey) => (
        <RouteTargetField
          key={fieldKey}
          fieldKey={fieldKey}
          value={target[fieldKey]}
          locale={locale}
        />
      ))}
    </dl>
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
