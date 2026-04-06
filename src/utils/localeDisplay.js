/**
 * HTML `lang` and `Intl` locale tags for each `SUPPORTED_LOCALES` code.
 */

const HTML_LANG = {
  'zh-CN': 'zh-Hans',
  en: 'en',
  ko: 'ko',
  ja: 'ja',
  hi: 'hi',
  fil: 'fil',
  vi: 'vi',
}

const DATE_LOCALE = {
  'zh-CN': 'zh-CN',
  en: 'en-CA',
  ko: 'ko-CA',
  ja: 'ja-CA',
  hi: 'hi-IN',
  fil: 'fil-PH',
  vi: 'vi-VN',
}

export function localeToHtmlLang(code) {
  return HTML_LANG[code] || code.split('-')[0] || 'en'
}

export function localeToDateLocale(code) {
  return DATE_LOCALE[code] || 'en-CA'
}
