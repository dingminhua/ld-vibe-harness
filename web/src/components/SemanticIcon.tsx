import type { ComponentType } from 'react';
import {
  FileText,
  BookOpenText,
  ClipboardList,
  Focus,
  GitCommit,
  Github,
  FileSignature,
  Lightbulb,
  Link2,
  Pencil,
  Workflow,
  type LucideIcon,
  type LucideProps,
} from 'lucide-react';

type SemanticIconComponent = ComponentType<LucideProps>;

function GitHubSilhouetteIcon({ size = 16, className, ...props }: LucideProps) {
  return <Github size={size} strokeWidth={0} fill="currentColor" className={className} {...props} />;
}

function MemoPencilIcon({ size = 16, className, ...props }: LucideProps) {
  const iconSize = Math.max(10, Number(size) - 2);
  return <Pencil size={iconSize} className={className} {...props} />;
}

export const OBJECT_TYPE_ICONS: Record<string, SemanticIconComponent> = {
  workarea: Focus,
  workplan: ClipboardList,
  adr: FileSignature,
  pitfall: Lightbulb,
  memo: MemoPencilIcon,
  study: BookOpenText,
  change: GitCommit,
  changelog: GitHubSilhouetteIcon,
};

export const COLLECTION_ICONS: Record<string, LucideIcon> = {
  workarea: Focus,
  workplan: ClipboardList,
  plan: ClipboardList,
  properties: FileText,
  docs: FileText,
  related: Link2,
  progress: Workflow,
};

type SemanticIconProps = Omit<LucideProps, 'ref'> & {
  type?: string | null;
};

export function ObjectTypeIcon({ type, size = 14, ...props }: SemanticIconProps) {
  const Icon = type ? (OBJECT_TYPE_ICONS[type] ?? Link2) : Link2;
  return <Icon size={size} aria-hidden="true" {...props} />;
}

export function CollectionTitleIcon({ type, size = 14, ...props }: SemanticIconProps) {
  const Icon = type ? (COLLECTION_ICONS[type] ?? Link2) : Link2;
  return <Icon size={size} aria-hidden="true" {...props} />;
}
