import type { ReactNode } from 'react';
import SummaryText from '@/components/SummaryText';

/**
 * WorkCase 成功标准在列表 Card 与详情页共用同一块面、字号、色阶与节奏。
 * 详情页可以追加结果信息，但不得改变标准正文的阅读层级。
 */
export const WORKCASE_CRITERIA_SURFACE_CLASS =
  'min-w-0 rounded-md border border-blue-400/20 border-l-2 border-l-blue-400/80 bg-blue-500/[0.025] px-3 py-2.5 dark:bg-blue-950/20';

export interface WorkCaseCriterionListItem {
  key: string;
  statement: string;
  details?: ReactNode;
}

export function WorkCaseCriteriaList({
  items,
  className = '',
  textSize = 'card',
}: {
  items: WorkCaseCriterionListItem[];
  className?: string;
  textSize?: 'card' | 'detail';
}) {
  const detailText = textSize === 'detail';
  return (
    <ul className={`${className} grid min-w-0 gap-1.5`.trim()}>
      {items.map((item) => (
        <li key={item.key} className="flex min-w-0 items-start gap-2.5">
          <span
            aria-hidden="true"
            className={`${detailText ? 'mt-[0.5625rem]' : 'mt-[0.5rem]'} h-1 w-1 shrink-0 rounded-full bg-blue-400/65 dark:bg-blue-400/75`}
          />
          <div className="ldvh-caption min-w-0 flex-1 break-words [&_p]:my-0">
            {item.statement.trim() && (
              <SummaryText
                value={item.statement}
                collapseThreshold={Number.MAX_SAFE_INTEGER}
                className={`${detailText ? 'ldvh-detail-semantic-body' : 'ldvh-card-decision-body'} text-blue-950/65 dark:text-blue-100/75`}
              />
            )}
            {item.details}
          </div>
        </li>
      ))}
    </ul>
  );
}
