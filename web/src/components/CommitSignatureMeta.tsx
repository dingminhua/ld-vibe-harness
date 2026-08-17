import * as React from 'react';
import type { CommitSignature } from '@/utils/api';
import { normalizeSignature } from '../../shared/signature';

/** 值是否实际为空（空字符串或字面量 "null"/"undefined"）。 */
function isBlank(value: string): boolean {
  return !value || value === 'null' || value === 'undefined';
}

/** Compactly display the optional product/runtime signature identity. */
export default function CommitSignatureMeta({
  signature,
}: {
  signature?: CommitSignature;
}) {
  const { modelName, productName, agentRuntimeName: runtimeName } = normalizeSignature(signature ?? {});
  const environment = productName && runtimeName
    ? `${productName}(${runtimeName})`
    : productName || runtimeName;
  const values = [modelName, environment].filter((v) => !isBlank(v));
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
