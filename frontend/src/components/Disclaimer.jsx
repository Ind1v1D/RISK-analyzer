import { useI18n } from '../i18n/I18nContext.jsx'

/**
 * Persistent, visible disclaimer — rendered in the app footer on every screen.
 */
export default function Disclaimer() {
  const { t } = useI18n()
  return <footer className="disclaimer">{t('disclaimer.text')}</footer>
}
