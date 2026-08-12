import * as React from 'react';
import type { CommitSignature } from '@/utils/api';

/** Compactly display the optional product/runtime signature identity. */
export default function CommitSignatureMeta({
  signature,
}: {
  signature?: CommitSignature;
}) {
  const modelName = signature?.modelName?.trim() ?? '';
  const productName = signature?.productName?.trim() ?? '';
  const runtimeName = signature?.agentRuntimeName?.trim() ?? '';
  const environment = productName && runtimeName
    ? `${productName}(${runtimeName})`
    : productName || runtimeName;
  const values = [modelName, environment].filter(Boolean);
  if (values.length === 0) return null;

  return (
    <span className="inline-flex h-4 shrink-0 items-center leading-4">
      {values.map((value) => (
        <span key={value} className="inline-flex h-4 shrink-0 items-center leading-4">
          <span className="inline-flex h-4 shrink-0 items-center px-1 leading-4 text-ldvh-text-secondary/70" aria-hidden="true">·</span>
          {value}
        </span>
      ))}
    </span>
  );
}
