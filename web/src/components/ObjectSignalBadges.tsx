import {
  getObjectSignals,
  getSignalDotClassName,
  getSignalClassName,
  getSignalFieldLabel,
  getSignalText,
  type ObjectSignalSource,
  type SignalObjectType,
} from '@/utils/objectSignals';

export default function ObjectSignalBadges({
  source,
  type,
  locale,
  className = '',
}: {
  source: ObjectSignalSource;
  type?: SignalObjectType;
  locale: string;
  className?: string;
}) {
  const signals = getObjectSignals(source, type);
  if (signals.length === 0) return null;

  return (
    <div className={`flex min-w-0 flex-wrap gap-1.5 ${className}`}>
      {signals.map(({ field, value }) => {
        const fieldLabel = getSignalFieldLabel(field, locale);
        const valueLabel = getSignalText(field, value, locale);
        const dotClassName = getSignalDotClassName(field, value);
        return (
          <span
            key={`${field}-${value}`}
            className={`ldvh-caption inline-flex max-w-full items-center gap-1 rounded-md border px-1.5 py-0.5 font-sans ${getSignalClassName(field, value)}`}
            title={fieldLabel && valueLabel ? `${fieldLabel}: ${valueLabel}` : undefined}
          >
            {dotClassName && <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotClassName}`} />}
            <span className="truncate">{valueLabel}</span>
          </span>
        );
      })}
    </div>
  );
}
