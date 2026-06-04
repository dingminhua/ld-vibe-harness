import { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, AlertTriangle, FileWarning } from 'lucide-react';
import { fetchValidation, type ValidationData, type ValidationIssue } from '@/utils/api';
import { useI18n } from '@/i18n/context';

export default function Validate() {
  const [data, setData] = useState<ValidationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { t } = useI18n();

  useEffect(() => {
    fetchValidation()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="text-ldvh-text-secondary">{t('common.loadFailed')}</p>
          <p className="font-mono text-xs text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  // Group issues by path
  const issuesByFile = data.issues.reduce<Record<string, ValidationIssue[]>>((acc, issue) => {
    const file = issue.path;
    if (!acc[file]) acc[file] = [];
    acc[file].push(issue);
    return acc;
  }, {});

  return (
    <div className="p-6">
      <h1 className="mb-6 text-xl font-semibold text-ldvh-text-primary">{t('validate.title')}</h1>

      {/* Summary card */}
      <div className="mb-6 grid grid-cols-3 gap-3">
        <div className="flex items-center gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <FileWarning size={20} className="text-ldvh-text-secondary" />
          <div>
            <p className="font-mono text-2xl font-semibold text-ldvh-text-primary">{data.summary.files}</p>
            <p className="text-xs text-ldvh-text-secondary">{t('validate.filesChecked')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <AlertCircle size={20} className="text-red-400" />
          <div>
            <p className="font-mono text-2xl font-semibold text-red-400">{data.summary.errors}</p>
            <p className="text-xs text-ldvh-text-secondary">{t('validate.errors')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <AlertTriangle size={20} className="text-yellow-400" />
          <div>
            <p className="font-mono text-2xl font-semibold text-yellow-400">{data.summary.warnings}</p>
            <p className="text-xs text-ldvh-text-secondary">{t('validate.warnings')}</p>
          </div>
        </div>
      </div>

      {/* Issues list */}
      {data.issues.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16">
          <CheckCircle size={40} className="mb-3 text-green-400" />
          <p className="text-ldvh-text-primary">{t('validate.allPassed')}</p>
          <p className="text-sm text-ldvh-text-secondary">{t('validate.noIssues')}</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {Object.entries(issuesByFile).map(([file, issues]) => (
            <div
              key={file}
              className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4"
            >
              <h3 className="mb-3 font-mono text-sm text-ldvh-text-primary">{file}</h3>
              <ul className="flex flex-col gap-2">
                {issues.map((issue, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 rounded-md bg-ldvh-bg px-3 py-2"
                  >
                    {issue.level === 'error' ? (
                      <AlertCircle size={14} className="mt-0.5 flex-shrink-0 text-red-400" />
                    ) : (
                      <AlertTriangle size={14} className="mt-0.5 flex-shrink-0 text-yellow-400" />
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-medium text-ldvh-text-primary">
                          {issue.code}
                        </span>
                        <span className={`font-mono text-xs ${issue.level === 'error' ? 'text-red-400' : 'text-yellow-400'}`}>
                          {issue.level === 'error' ? t('validate.error') : t('validate.warning')}
                        </span>
                        {issue.field && (
                          <span className="font-mono text-xs text-ldvh-text-secondary">
                            → {issue.field}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-ldvh-text-secondary">{issue.message}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
