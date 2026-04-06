import { createI18n } from 'vue-i18n'
import en from '../locales/en.json'
import zhCN from '../locales/zh-CN.json'
import { localeToHtmlLang } from '../utils/localeDisplay.js'

export { localeToHtmlLang }

export const LOCALE_STORAGE_KEY = 'littlebuggy-locale'

/** Default UI language (first visit, no saved preference). */
export const DEFAULT_LOCALE = 'en'

/**
 * All languages shown in the UI. `en` + `zh-CN` have dedicated JSON; others use the English
 * bundle until `src/locales/<code>.json` is added and wired in `messages`.
 */
export const SUPPORTED_LOCALES = [
  { code: 'en', short: 'EN', native: 'English' },
  { code: 'zh-CN', short: '中文', native: '中文' },
  { code: 'ko', short: 'KO', native: '한국어' },
  { code: 'ja', short: 'JA', native: '日本語' },
  { code: 'hi', short: 'HI', native: 'हिन्दी' },
  { code: 'fil', short: 'TL', native: 'Filipino' },
  { code: 'vi', short: 'VI', native: 'Tiếng Việt' },
]

const supportedCodes = new Set(SUPPORTED_LOCALES.map((o) => o.code))

function readStoredLocale() {
  if (typeof localStorage === 'undefined') return DEFAULT_LOCALE
  const v = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (v && supportedCodes.has(v)) return v
  return DEFAULT_LOCALE
}

export const i18n = createI18n({
  legacy: false,
  locale: readStoredLocale(),
  fallbackLocale: {
    'zh-CN': ['en'],
    en: ['zh-CN'],
    ko: ['en'],
    ja: ['en'],
    hi: ['en'],
    fil: ['en'],
    vi: ['en'],
  },
  messages: {
    en,
    'zh-CN': zhCN,
    ko: en,
    ja: en,
    hi: en,
    fil: en,
    vi: en,
  },
  globalInjection: true,
})

export function persistLocale(code) {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(LOCALE_STORAGE_KEY, code)
}
