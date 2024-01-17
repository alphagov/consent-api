import { GovConsentConfig } from './GovConsentConfig'
import ApiV1 from './ApiV1'
import {
  addUrlParameter,
  getOriginFromLink,
  isCrossOrigin,
  removeUrlParameter,
  request,
  setCookie,
  getCookie,
} from './utils'

type Consents = {
  essential: boolean
  usage: boolean
  campaigns: boolean
  settings: boolean
}

type ConsentsUpdateCallback = (
  consents: Consents,
  consentsPreferencesSet: boolean,
  error?: Error | null
) => void

interface CustomWindow extends Window {
  cachedConsentsCookie: Consents | null
}

declare const window: CustomWindow

export class GovSingleConsent {
  static ACCEPT_ALL: Consents = {
    essential: true,
    usage: true,
    campaigns: true,
    settings: true,
  }
  static REJECT_ALL: Consents = {
    essential: true,
    usage: false,
    campaigns: false,
    settings: false,
  }

  _consentsUpdateCallback: ConsentsUpdateCallback
  config: GovConsentConfig
  uid?: string | null
  cachedConsentsCookie: Consents | null = null
  urls: ApiV1

  constructor(baseUrl: string, consentsUpdateCallback: ConsentsUpdateCallback) {
    /**
      Initialises _GovConsent object by performing the following:
      1. Removes 'uid' from URL.
      2. Sets 'uid' attribute from cookie or URL.
      3. Fetches consent status from API if 'uid' exists.
      4. Notifies event listeners with API response.

      @arg baseUrl: string - the domain of where the single consent API is. Required.
      @arg consentsUpdateCallback: function(consents, consentsPreferencesSet, error) - callback when the consents are updated
      "consents": this is the consents object. It has the following properties: "essential", "usage", "campaigns", "settings". Each property is a boolean.
      "consentsPreferencesSet": true if the consents have been set for this user and this domain. Typically, only display the cookie banner if this is true.
      "error": if an error occurred, this is the error object. Otherwise, this is null.
      */

    this.validateConstructorArguments(baseUrl, consentsUpdateCallback)
    this._consentsUpdateCallback = consentsUpdateCallback
    this.config = new GovConsentConfig(baseUrl)
    this.urls = new ApiV1(this.config.baseUrl)
    window.cachedConsentsCookie = null
    this.hideUIDParameter()
    this.initialiseUIDandConsents()
  }

  validateConstructorArguments(
    baseUrl: string,
    consentsUpdateCallback: ConsentsUpdateCallback
  ) {
    if (!baseUrl) {
      throw new Error('Argument baseUrl is required')
    }
    if (typeof baseUrl !== 'string') {
      throw new Error('Argument baseUrl must be a string')
    }
    if (!consentsUpdateCallback) {
      throw new Error('Argument consentsUpdateCallback is required')
    }
    if (typeof consentsUpdateCallback !== 'function') {
      throw new Error('Argument consentsUpdateCallback must be a function')
    }
  }

  initialiseUIDandConsents() {
    const currentUID = this.getCurrentUID()
    if (this.isNewUID(currentUID)) {
      this.handleNewUID(currentUID)
    }

    if (this.uid) {
      this.fetchAndUpdateConsents()
    } else {
      this._consentsUpdateCallback(null, false, null)
    }
  }

  handleNewUID(newUID: string): void {
    this.uid = newUID
    this.updateLinksEventHandlers(newUID)
    this.setUIDCookie(newUID)
  }

  private isNewUID(currentUID: string | null): boolean {
    return currentUID && currentUID !== this.uid
  }

  fetchAndUpdateConsents() {
    const consentsUrl = this.urls.consents(this.uid)

    try {
      request(
        consentsUrl,
        { timeout: 1000 },
        ({ status: consents }: { status: Consents }) => {
          this.updateBrowserConsents(consents)
          this._consentsUpdateCallback(
            consents,
            GovSingleConsent.isConsentPreferencesSet(),
            null
          )
        }
      )
    } catch (error) {
      this.defaultToRejectAllConsents(error)
    }
  }

  getCurrentUID(): string | null | undefined {
    // Get the current uid from URL or from the cookie if it exists
    return this.config.uidFromUrl || this.config.uidFromCookie
  }

  setConsents(consents: Consents) {
    if (!consents) {
      throw new Error('consents is required in GovSingleConsent.setConsents()')
    }

    const successCallback = (response) => {
      if (this.isNewUID(response.uid)) {
        this.handleNewUID(response.uid)
      }
      this.updateBrowserConsents(consents)
      this._consentsUpdateCallback(
        consents,
        GovSingleConsent.isConsentPreferencesSet(),
        null
      )
    }

    const url = this.urls.consents(this.uid)
    try {
      request(
        url,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'status='.concat(JSON.stringify(consents)),
        },
        successCallback
      )
    } catch (error) {
      // The request failed. For security reasons, we assume the user has rejected all cookies.
      this.defaultToRejectAllConsents(error)
    }
  }

  private defaultToRejectAllConsents(error?: Error): void {
    this.updateBrowserConsents(GovSingleConsent.REJECT_ALL)
    this._consentsUpdateCallback(
      GovSingleConsent.REJECT_ALL,
      GovSingleConsent.isConsentPreferencesSet(),
      error
    )
  }

  static getConsents(): Consents | null {
    if (window.cachedConsentsCookie) {
      return window.cachedConsentsCookie
    }
    const cookieValue = getCookie(GovConsentConfig.CONSENTS_COOKIE_NAME, null)
    if (cookieValue) {
      return JSON.parse(cookieValue)
    }
    return null
  }

  static hasConsentedToEssential(): boolean {
    const consents = GovSingleConsent.getConsents()
    return consents?.essential
  }

  static hasConsentedToUsage(): boolean {
    const consents = GovSingleConsent.getConsents()
    return consents?.usage
  }

  static hasConsentedToCampaigns(): boolean {
    const consents = GovSingleConsent.getConsents()
    return consents?.campaigns
  }

  static hasConsentedToSettings(): boolean {
    const consents = GovSingleConsent.getConsents()
    return consents?.settings
  }

  static isConsentPreferencesSet(): boolean {
    const value = getCookie(GovConsentConfig.PREFERENCES_SET_COOKIE_NAME, null)
    return value === 'true'
  }

  private updateLinksEventHandlers(currentUID): void {
    request(
      this.urls.origins(),
      {},
      // Update links with UID
      (origins) => this.addUIDtoCrossOriginLinks(origins, currentUID)
    )
  }

  private addUIDtoCrossOriginLinks(origins, uid): void {
    /**
     * Adds uid URL parameter to consent sharing links.
     * Only links with known origins are updated.
     */

    const links = document.querySelectorAll('a[href]')
    Array.prototype.forEach.call(links, (link) => {
      if (
        isCrossOrigin(link) &&
        origins.indexOf(getOriginFromLink(link)) >= 0
      ) {
        link.addEventListener('click', (event) => {
          event.target.href = addUrlParameter(
            event.target.href,
            GovConsentConfig.UID_KEY,
            uid
          )
        })
      }
    })
  }

  private setUIDCookie(uid: string): void {
    setCookie({
      name: GovConsentConfig.UID_KEY,
      value: uid,
      lifetime: GovConsentConfig.COOKIE_LIFETIME,
    })
  }

  private updateBrowserConsents(consents: Consents): void {
    this.setConsentsCookie(consents)
    this.setPreferencesSetCookie(true)
    window.cachedConsentsCookie = consents
  }

  private setConsentsCookie(consents: Consents): void {
    setCookie({
      name: GovConsentConfig.CONSENTS_COOKIE_NAME,
      value: JSON.stringify(consents),
      lifetime: GovConsentConfig.COOKIE_LIFETIME,
    })
  }

  private setPreferencesSetCookie(value: boolean): void {
    setCookie({
      name: GovConsentConfig.PREFERENCES_SET_COOKIE_NAME,
      value: value.toString(),
      lifetime: GovConsentConfig.COOKIE_LIFETIME,
    })
  }

  private hideUIDParameter(): void {
    history.replaceState(
      null,
      null,
      removeUrlParameter(location.href, GovConsentConfig.UID_KEY)
    )
  }
}
