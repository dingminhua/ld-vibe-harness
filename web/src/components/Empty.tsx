import { cn } from '@/lib/utils'
import { useI18n } from '@/i18n/context'

export default function Empty() {
  const { t } = useI18n()
  return (
    <div className={cn('flex h-full items-center justify-center')}>{t('common.empty')}</div>
  )
}
