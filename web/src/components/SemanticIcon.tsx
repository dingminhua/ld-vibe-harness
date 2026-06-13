import {
  Bug,
  ClipboardCheck,
  ClipboardList,
  FileText,
  GitBranch,
  GitCommit,
  IdCard,
  Layers,
  Link2,
  ListTodo,
  ListTree,
  Shield,
  ShieldCheck,
  StickyNote,
  Workflow,
  type LucideIcon,
  type LucideProps,
} from 'lucide-react';

export const OBJECT_TYPE_ICONS: Record<string, LucideIcon> = {
  workarea: Layers,
  taskplan: ClipboardList,
  task: ListTodo,
  subtask: ListTree,
  adr: GitBranch,
  pitfall: Bug,
  memo: StickyNote,
  profile: IdCard,
  change: GitCommit,
  validate: Shield,
  gate: ShieldCheck,
  changelog: ClipboardCheck,
};

export const COLLECTION_ICONS: Record<string, LucideIcon> = {
  workarea: Layers,
  taskplan: ClipboardList,
  plan: ClipboardList,
  task: ListTodo,
  taskQueue: ListTodo,
  subtask: ListTree,
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
