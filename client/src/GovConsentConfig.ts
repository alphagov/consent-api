import { findByKey, parseUrl } from './utils'

export const COOKIE_DAYS = 365

export class GovConsentConfig {
  UID_KEY = 'gov_singleconsent_uid'
  CONSENTS_COOKIE_NAME = 'cookies_policy'
  PREFERENCES_SET_COOKIE_NAME = 'cookies_preferences_set'
  COOKIE_LIFETIME = COOKIE_DAYS * 24 * 60 * 60
  uidFromCookie: string
  uidFromUrl: string

  constructor() {
    this.uidFromCookie = findByKey(this.UID_KEY, document.cookie.split(';'))
    this.uidFromUrl = findByKey(this.UID_KEY, parseUrl(location.href).params)
  }

  getApiUrl() {
    const el = document.querySelector('[data-gov-singleconsent-api-url]')
    // @ts-ignore
    const govSingleconsentApiUrl = el?.dataset?.govSingleconsentApiUrl
    if (!govSingleconsentApiUrl) {
      throw new Error('data-gov-singleconsent-api-url is required')
    }

    return govSingleconsentApiUrl.replace(/\/?$/, '/')
  }
}
