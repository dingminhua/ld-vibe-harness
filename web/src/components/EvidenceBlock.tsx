import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface EvidenceBlockProps {
  value: string;
}

export default function EvidenceBlock({ value }: EvidenceBlockProps) {

  return (
    <div className="rounded-lg border border-ldvh-accent/20 bg-ldvh-accent/5 p-3">
      <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-li:my-0.5 prose-ul:my-1 prose-pre:my-2">
        <Markdown
          remarkPlugins={[remarkGfm]}
          components={{
            code: ({ className, children, ...props }) => {
              const text = String(children);
              const isCommand = /^(python3?|npx|npm|yarn|pip|cargo|go\s+(?:run|test|build))\s/.test(text);
              const isPath = /^(specs\/|src\/|tools\/|web\/|config\/|\.\/|\/)/.test(text);

              if (isCommand || isPath) {
                return (
                  <code
                    className="rounded bg-ldvh-accent/15 px-1.5 py-0.5 font-mono text-xs text-ldvh-accent"
                    {...props}
                  >
                    {children}
                  </code>
                );
              }

              // Inline code default
              if (!className) {
                return (
                  <code className="rounded bg-ldvh-border/50 px-1 py-0.5 font-mono text-xs" {...props}>
                    {children}
                  </code>
                );
              }

              // Fenced code block
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
            pre: ({ children, ...props }) => (
              <pre
                className="rounded-lg border border-ldvh-accent/20 bg-ldvh-accent/5 p-3 overflow-x-auto"
                {...props}
              >
                {children}
              </pre>
            ),
          }}
        >
          {value}
        </Markdown>
      </div>
    </div>
  );
}
