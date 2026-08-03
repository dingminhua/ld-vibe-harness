import { Fragment } from 'react';
import type { CommitSignature } from '@/utils/api';

/** Compact display of the human-readable fields from an optional commit signature. */
export default function CommitSignatureMeta({
  signature,
}: {
  signature?: CommitSignature;
}) {
  const values = [signature?.agentId, signature?.hostEnvironment].filter(
    (value): value is string => Boolean(value?.trim()),
  );
  if (values.length === 0) return null;

  return (
    <>
      {values.map((value) => (
        <Fragment key={value}>
          <span className="px-1 text-ldvh-text-secondary/70" aria-hidden="true">·</span>
          <span>{value}</span>
        </Fragment>
      ))}
    </>
  );
}
