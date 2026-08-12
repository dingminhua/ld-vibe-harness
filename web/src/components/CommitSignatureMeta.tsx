import type { CommitSignature } from '@/utils/api';

/** Compactly display the optional product/runtime signature identity. */
export default function CommitSignatureMeta({
  signature,
}: {
  signature?: CommitSignature;
}) {
  const productName = signature?.productName?.trim() ?? '';
  const runtimeName = signature?.agentRuntimeName?.trim() ?? '';
  if (!productName && !runtimeName) return null;
  const identity = productName && runtimeName
    ? `${productName}(${runtimeName})`
    : productName || runtimeName;

  return (
    <span className="inline-flex h-4 shrink-0 items-center leading-4">
      <span className="inline-flex h-4 shrink-0 items-center px-1 leading-4 text-ldvh-text-secondary/70" aria-hidden="true">·</span>
      <span className="inline-flex h-4 shrink-0 items-center leading-4">{identity}</span>
    </span>
  );
}
