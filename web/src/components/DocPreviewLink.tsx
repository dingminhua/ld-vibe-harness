import { FileText, ExternalLink } from 'lucide-react';

interface DocPreviewLinkProps {
  docs: string[];
}

export default function DocPreviewLink({ docs }: DocPreviewLinkProps) {

  if (docs.length === 0) return null;

  const handleClick = (docPath: string) => {
    // Emit custom event for right panel consumption
    const event = new CustomEvent('ldvh:doc-preview', {
      detail: { path: docPath },
      bubbles: true,
    });
    document.dispatchEvent(event);

    // External links open in new tab
    if (docPath.startsWith('http')) {
      window.open(docPath, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className="flex flex-col gap-1.5">
      {docs.map((doc, i) => {
        const isExternal = doc.startsWith('http');
        return (
          <button
            key={i}
            onClick={() => handleClick(doc)}
            className="flex w-full items-center gap-2 rounded-lg border border-ldvh-border bg-ldvh-bg px-3 py-2 text-left text-sm transition-colors hover:bg-ldvh-border/30"
          >
            {isExternal ? (
              <ExternalLink size={13} className="shrink-0 text-ldvh-accent" />
            ) : (
              <FileText size={13} className="shrink-0 text-ldvh-accent" />
            )}
            <span className="min-w-0 flex-1 truncate text-ldvh-text-primary font-mono text-xs">
              {doc}
            </span>
            {isExternal && (
              <span className="shrink-0 text-[10px] text-ldvh-text-secondary">↗</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
