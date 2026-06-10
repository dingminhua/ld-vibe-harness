import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

interface MarkdownPreviewProps {
  content: string;
  className?: string;
}

export default function MarkdownPreview({ content, className }: MarkdownPreviewProps) {
  return (
    <div
      className={cn(
        'prose prose-sm max-w-none overflow-x-auto dark:prose-invert',
        'prose-headings:scroll-mt-4 prose-headings:text-ldvh-text-primary prose-h1:text-xl prose-h2:text-lg prose-h3:text-base',
        'prose-p:leading-7 prose-p:text-ldvh-text-primary prose-li:my-1 prose-li:text-ldvh-text-primary',
        'prose-a:text-ldvh-accent prose-a:no-underline hover:prose-a:underline',
        'prose-strong:text-ldvh-text-primary prose-code:rounded prose-code:bg-ldvh-border/40 prose-code:px-1 prose-code:py-0.5 prose-code:text-ldvh-accent',
        'prose-pre:rounded-md prose-pre:border prose-pre:border-ldvh-border prose-pre:bg-ldvh-panel prose-pre:p-3',
        'prose-blockquote:border-ldvh-accent/50 prose-blockquote:text-ldvh-text-secondary',
        'prose-table:w-max prose-table:min-w-full prose-table:text-sm',
        'prose-th:whitespace-nowrap prose-th:border prose-th:border-ldvh-border prose-th:bg-ldvh-panel prose-th:px-2 prose-th:py-1 prose-th:text-ldvh-text-primary',
        'prose-td:border prose-td:border-ldvh-border prose-td:px-2 prose-td:py-1 prose-td:align-top prose-td:text-ldvh-text-primary',
        className,
      )}
    >
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </div>
  );
}
