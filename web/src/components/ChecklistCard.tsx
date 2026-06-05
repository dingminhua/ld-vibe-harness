import { useState } from 'react';
import { CheckSquare, Square } from 'lucide-react';
import { useI18n } from '@/i18n/context';

interface ChecklistCardProps {
  value: string;
}

interface ChecklistItem {
  checked: boolean;
  text: string;
}

function parseChecklist(value: string): ChecklistItem[] {
  const lines = value.split('\n');
  const items: ChecklistItem[] = [];
  for (const line of lines) {
    const m = line.match(/^\s*- \[([ xX])\]\s*(.*)/);
    if (m) {
      items.push({ checked: m[1].toLowerCase() === 'x', text: m[2] });
    }
  }
  return items;
}

export default function ChecklistCard({ value }: ChecklistCardProps) {
  const { t } = useI18n();
  const items = parseChecklist(value);
  const doneCount = items.filter(i => i.checked).length;
  const totalCount = items.length;

  if (items.length === 0) {
    // Fallback: no checklist items found, render as plain text
    return <span className="text-sm text-ldvh-text-primary">{value}</span>;
  }

  const ratio = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  return (
    <div className="flex flex-col gap-2">
      {/* Progress header */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-ldvh-accent">
          {doneCount}/{totalCount}
        </span>
        <div className="h-1.5 flex-1 rounded-full bg-ldvh-border overflow-hidden">
          <div
            className="h-full rounded-full bg-ldvh-accent transition-all"
            style={{ width: `${ratio}%` }}
          />
        </div>
        <span className="text-[10px] text-ldvh-text-secondary">{ratio}%</span>
      </div>

      {/* Checklist items */}
      <div className="flex flex-col gap-1">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-2">
            {item.checked ? (
              <CheckSquare size={14} className="mt-0.5 shrink-0 text-ldvh-text-secondary" />
            ) : (
              <Square size={14} className="mt-0.5 shrink-0 text-ldvh-accent" />
            )}
            <span
              className={`text-sm leading-5 ${
                item.checked
                  ? 'text-ldvh-text-secondary line-through opacity-60'
                  : 'text-ldvh-text-primary'
              }`}
            >
              {item.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
