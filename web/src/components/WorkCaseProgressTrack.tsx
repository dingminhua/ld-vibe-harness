import { useI18n } from '@/i18n/context';
import {
  WORKCASE_PROGRESS_STEP_ORDER,
  getWorkCaseProgressProjection,
  type WorkCaseProgressStep,
} from '@/shared/workcaseStatus';

interface WorkCaseProgressTrackProps {
  phase?: unknown;
  step?: WorkCaseProgressStep | null;
  showUnavailable?: boolean;
  className?: string;
}

/**
 * Shared Human-facing WorkCase progress track. Card may pass its projected step;
 * detail derives the same deterministic position from the exact phase.
 */
export default function WorkCaseProgressTrack({
  phase,
  step,
  showUnavailable = false,
  className = 'mt-2.5',
}: WorkCaseProgressTrackProps) {
  const { t } = useI18n();
  const projection = typeof phase === 'string'
    ? getWorkCaseProgressProjection(phase)
    : null;
  const planRevising = phase === 'plan_revising';
  const resolvedStep = step === undefined
    ? projection?.progressStep ?? null
    : step;
  const currentStep = resolvedStep
    ? WORKCASE_PROGRESS_STEP_ORDER.indexOf(resolvedStep)
    : -1;
  const applies = planRevising
    || projection?.progressGroup === 'progressing'
    || currentStep >= 0
    || showUnavailable;

  if (!applies) return null;

  const stepLabels = [
    t('objectList.workcaseStageExecute'),
    t('objectList.workcaseStageSelfCheck'),
    t('objectList.workcaseStageResultReview'),
    t('objectList.workcaseStageSynthesis'),
  ];
  const currentStepLabel = planRevising
    ? t('objectList.workcasePlanRevising')
    : currentStep >= 0
      ? stepLabels[currentStep]
      : t('objectList.workcaseStageUnavailable');

  if (planRevising) {
    return (
      <div className={`${className} ldvh-card-decision-body flex min-w-0 items-center gap-2 text-sky-500 dark:text-sky-400`}>
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" aria-hidden="true" />
        <span className="min-w-0 break-words">{currentStepLabel}</span>
        <span className="ldvh-meta-muted">{t('objectList.workcaseOutsideProgressTrack')}</span>
      </div>
    );
  }

  return (
    <>
      {currentStep < 0 && (
        <p role="status" className={`${className} ldvh-card-decision-body text-red-400`}>
          {currentStepLabel}
        </p>
      )}
      <ol
        className={`${className} grid min-w-0 grid-cols-4`}
        aria-label={`${t('objectList.workcaseDynamicStages')}：${currentStepLabel}`}
      >
        {WORKCASE_PROGRESS_STEP_ORDER.map((trackStep, index) => {
          const isCurrent = index === currentStep;
          return (
            <li
              key={trackStep}
              aria-current={isCurrent ? 'step' : undefined}
              className="relative flex min-w-0 flex-col items-center px-1 text-center"
            >
              {index > 0 && (
                <span className="absolute left-0 right-1/2 top-2.5 z-0 h-px bg-ldvh-border" aria-hidden="true" />
              )}
              {index < WORKCASE_PROGRESS_STEP_ORDER.length - 1 && (
                <span className="absolute left-1/2 right-0 top-2.5 z-0 h-px bg-ldvh-border" aria-hidden="true" />
              )}
              <span className={`ldvh-meta relative z-10 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border bg-ldvh-bg ${
                isCurrent
                  ? 'border-sky-400/60 bg-sky-100 font-semibold text-sky-600 ring-2 ring-sky-500/10 dark:bg-sky-950 dark:text-sky-300'
                  : 'border-ldvh-border text-ldvh-text-secondary'
              }`}>
                {index + 1}
              </span>
              <div className="mt-1.5 min-w-0">
                <div className={`ldvh-card-decision-body break-words leading-4 ${
                  isCurrent ? 'font-medium text-sky-400' : 'text-ldvh-text-secondary/80'
                }`}>
                  {stepLabels[index]}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </>
  );
}
