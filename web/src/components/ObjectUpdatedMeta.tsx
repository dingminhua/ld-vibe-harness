import CommitSignatureMeta from '@/components/CommitSignatureMeta';
import { formatDateTime } from '@/utils/dateFormat';
import { getLatestFactChangeSignature } from '@/utils/factChangeLog';

/**
 * The single update-attribution presentation used by fact cards and headers.
 * The attribution is deliberately derived from the latest complete
 * change_log signature, never inferred from other fact fields.
 */
export default function ObjectUpdatedMeta({
  source,
  updatedAt,
}: {
  source: { change_log?: unknown };
  updatedAt?: string;
}) {
  const updated = formatDateTime(updatedAt);
  const signature = getLatestFactChangeSignature(source.change_log);

  return (
    <span className="ldvh-meta-muted inline-flex min-w-0 items-center truncate leading-4 align-middle text-ldvh-text-secondary">
      <span className="shrink-0 leading-4">{updated}</span>
      {signature && <CommitSignatureMeta signature={signature} />}
    </span>
  );
}
