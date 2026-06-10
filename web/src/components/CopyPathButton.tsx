import { useEffect, useRef, useState, type MouseEvent } from 'react';
import { Check, Copy } from 'lucide-react';
import { useI18n } from '@/i18n/context';

interface CopyPathButtonProps {
  path?: string;
  className?: string;
}

async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      // Fall through to the textarea fallback for constrained browser contexts.
    }
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
}

export default function CopyPathButton({ path, className = '' }: CopyPathButtonProps) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current !== null) window.clearTimeout(timeoutRef.current);
    };
  }, []);

  if (!path) return null;

  const label = copied ? t('common.copiedPath') : t('common.copyPath');

  const handleClick = async (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();

    await copyText(path);
    setCopied(true);
    if (timeoutRef.current !== null) window.clearTimeout(timeoutRef.current);
    timeoutRef.current = window.setTimeout(() => setCopied(false), 1200);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary transition-colors hover:border-ldvh-accent/40 hover:text-ldvh-accent ${className}`}
      title={label}
      aria-label={label}
    >
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );
}
