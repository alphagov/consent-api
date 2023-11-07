import { findByKey, parseUrl } from './utils'

export class GovConsentConfig {
  uidKey = 'gov_singleconsent_uid'
  uidFromCookie: string
  uidFromUrl: string

  constructor() {
    this.uidFromCookie = findByKey(this.uidKey, document.cookie.split(';'))
    this.uidFromUrl = findByKey(this.uidKey, parseUrl(location.href).params)
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
