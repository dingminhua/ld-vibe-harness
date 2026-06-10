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
      <div className="ldvh-inline-markdown max-w-none">
        <Markdown remarkPlugins={[remarkGfm]}>
          {needsTruncation && !expanded ? displayText + '…' : value}
        </Markdown>
      </div>
      {needsTruncation && (
        <button
          onClick={() => setExpanded(v => !v)}
          className="ldvh-caption mt-1.5 flex items-center gap-1 text-ldvh-accent transition-colors hover:text-ldvh-accent/80"
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
