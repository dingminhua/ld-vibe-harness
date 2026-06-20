import { WORKPLAN_DEFAULT_LIST_STATUS } from '@/utils/workplanStatus';

const DEFAULT_ACTIVE_TYPES = new Set(['workarea', 'adr', 'pitfall', 'study']);

export const ALL_STATUS_PARAM = 'all';

export function getDefaultListStatus(type: string): string | null {
  if (type === 'spark') return 'pending';
  if (type === 'workplan') return WORKPLAN_DEFAULT_LIST_STATUS;
  return DEFAULT_ACTIVE_TYPES.has(type) ? 'active' : null;
}

export function getEffectiveListStatus(type: string, statusParam: string | null): string | null {
  if (statusParam === ALL_STATUS_PARAM) return null;
  if (statusParam) return statusParam;
  return getDefaultListStatus(type);
}

export function writeListStatusParam(type: string, params: URLSearchParams, status: string | null) {
  const defaultStatus = getDefaultListStatus(type);

  if (status === null) {
    if (defaultStatus) {
      params.set('status', ALL_STATUS_PARAM);
    } else {
      params.delete('status');
    }
    return;
  }

  if (status === defaultStatus) {
    params.delete('status');
    return;
  }

  params.set('status', status);
}
