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
    var el = document.querySelector('[data-gov-singleconsent-api-url]')
    return el
      ? // @ts-ignore
        el.dataset.govSingleconsentApiUrl.replace(/\/?$/, '/')
      : 'https://consent-api-bgzqvpmbyq-nw.a.run.app/api/v1/consent/'
  }
}
