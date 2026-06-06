import { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useI18n } from '@/i18n/context';

interface SummaryTextProps {
  value: string;
}

const COLLAPSE_THRESHOLD = 150;

/** 按段落截断 Markdown 文本，避免破坏语法结构 */
function truncateByParagraph(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;

  const paragraphs = text.split(/\n\n+/);
  let result = '';
  for (const para of paragraphs) {
    if (result.length + para.length + 2 > maxChars && result.length > 0) {
      break;
    }
    result += (result ? '\n\n' : '') + para;
  }
  return result;
}

export default function SummaryText({ value }: SummaryTextProps) {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);

  const needsTruncation = value.length > COLLAPSE_THRESHOLD;
  const displayText = useMemo(
    () => expanded ? value : truncateByParagraph(value, COLLAPSE_THRESHOLD),
    [value, expanded]
  );

  return (
    <div>
      <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1.5 prose-p:leading-relaxed prose-li:my-0.5 prose-ul:my-1 prose-ol:my-1 prose-pre:my-2 prose-headings:mt-3 prose-headings:mb-1.5 prose-h2:text-base prose-h2:font-semibold prose-h3:text-sm prose-h3:font-medium prose-code:text-ldvh-accent">
        <Markdown remarkPlugins={[remarkGfm]}>
          {needsTruncation && !expanded ? displayText + '…' : value}
        </Markdown>
      </div>
      {needsTruncation && (
        <button
          onClick={() => setExpanded(v => !v)}
          className="mt-1.5 flex items-center gap-1 text-xs text-ldvh-accent transition-colors hover:text-ldvh-accent/80"
        >
          {expanded ? (
            <>
              <ChevronUp size={12} />
              {t('objectDetail.collapse')}
            </>
          ) : (
            <>
              <ChevronDown size={12} />
              {t('objectDetail.expand')}
            </>
          )}
        </button>
      )}
    </div>
  );
}
