import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface EvidenceBlockProps {
  value: string;
  /** 是否在结构化卡片内部（减少嵌套样式） */
  embedded?: boolean;
}

export default function EvidenceBlock({ value, embedded = false }: EvidenceBlockProps) {

  // 嵌入模式：不额外包裹边框和背景，因为外层已有容器
  if (embedded) {
    return (
      <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-li:my-0.5 prose-ul:my-1 prose-pre:my-2">
        <Markdown
          remarkPlugins={[remarkGfm]}
          components={{
            code: ({ className, children, ...props }) => {
              const text = String(children);
              const isCommand = /^(python3?|npx|npm|yarn|pip|cargo|go\s+(?:run|test|build))\s/.test(text);
              const isPath = /^(docs\/|specs\/|src\/|tools\/|web\/|config\/|\.\/|\/)/.test(text);

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

              if (!className) {
                return (
                  <code className="rounded bg-ldvh-border/50 px-1 py-0.5 font-mono text-xs" {...props}>
                    {children}
                  </code>
                );
              }

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
            h2: ({ children, ...props }) => (
              <h2 className="text-sm font-semibold text-ldvh-text-primary mt-3 mb-1 first:mt-0" {...props}>
                {children}
              </h2>
            ),
            h3: ({ children, ...props }) => (
              <h3 className="text-sm font-medium text-ldvh-text-primary mt-2 mb-1" {...props}>
                {children}
              </h3>
            ),
          }}
        >
          {value}
        </Markdown>
      </div>
    );
  }

  // 独立模式：带边框和背景
  return (
    <div className="rounded-lg border border-ldvh-accent/20 bg-ldvh-accent/5 p-3">
      <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-li:my-0.5 prose-ul:my-1 prose-pre:my-2">
        <Markdown
          remarkPlugins={[remarkGfm]}
          components={{
            code: ({ className, children, ...props }) => {
              const text = String(children);
              const isCommand = /^(python3?|npx|npm|yarn|pip|cargo|go\s+(?:run|test|build))\s/.test(text);
              const isPath = /^(docs\/|specs\/|src\/|tools\/|web\/|config\/|\.\/|\/)/.test(text);

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

              if (!className) {
                return (
                  <code className="rounded bg-ldvh-border/50 px-1 py-0.5 font-mono text-xs" {...props}>
                    {children}
                  </code>
                );
              }

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
            h2: ({ children, ...props }) => (
              <h2 className="text-sm font-semibold text-ldvh-text-primary mt-3 mb-1 first:mt-0" {...props}>
                {children}
              </h2>
            ),
            h3: ({ children, ...props }) => (
              <h3 className="text-sm font-medium text-ldvh-text-primary mt-2 mb-1" {...props}>
                {children}
              </h3>
            ),
          }}
        >
          {value}
        </Markdown>
      </div>
    </div>
  );
}
