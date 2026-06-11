import {
  getObjectSignals,
  getSignalClassName,
  getSignalFieldLabel,
  getSignalText,
  type ObjectSignalSource,
} from '@/utils/objectSignals';

export default function ObjectSignalBadges({
  source,
  locale,
  className = '',
}: {
  source: ObjectSignalSource;
  locale: string;
  className?: string;
}) {
  const signals = getObjectSignals(source);
  if (signals.length === 0) return null;

  return (
    <div className={`flex min-w-0 flex-wrap gap-1.5 ${className}`}>
      {signals.map(({ field, value }) => {
        const fieldLabel = getSignalFieldLabel(field, locale);
        const valueLabel = getSignalText(field, value, locale);
        return (
          <span
            key={`${field}-${value}`}
            className={`ldvh-chip inline-flex max-w-full items-center rounded-md border px-2 py-0.5 font-sans ${getSignalClassName(field, value)}`}
            title={fieldLabel && valueLabel ? `${fieldLabel}: ${valueLabel}` : undefined}
          >
            <span className="truncate">{valueLabel}</span>
          </span>
        );
      })}
    </div>
  );
}
