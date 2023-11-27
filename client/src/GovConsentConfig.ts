import { findByKey, parseUrl } from './utils'

export const COOKIE_DAYS = 365

export class GovConsentConfig {
  static UID_KEY = 'gov_singleconsent_uid'
  static CONSENTS_COOKIE_NAME = 'cookies_policy'
  static PREFERENCES_SET_COOKIE_NAME = 'cookies_preferences_set'
  static COOKIE_LIFETIME = COOKIE_DAYS * 24 * 60 * 60
  uidFromCookie: string
  uidFromUrl: string
  apiUrl: string

  constructor(apiUrl?: string) {
    this.uidFromCookie = findByKey(
      GovConsentConfig.UID_KEY,
      document.cookie.split(';')
    )
    this.uidFromUrl = findByKey(
      GovConsentConfig.UID_KEY,
      parseUrl(location.href).params
    )

    this.apiUrl = apiUrl || this.getApiUrlFromHtml()
  }

  getApiUrlFromHtml() {
    const el = document.querySelector('[data-gov-singleconsent-api-url]')
    // @ts-ignore
    const govSingleconsentApiUrl = el?.dataset?.govSingleconsentApiUrl
    if (!govSingleconsentApiUrl) {
      throw new Error(
        'Could not find data-gov-singleconsent-api-url in the html document. Either pass the url to the constructor or add the data attribute to the html document'
      )
    }

    return govSingleconsentApiUrl.replace(/\/?$/, '/')
  }
}
