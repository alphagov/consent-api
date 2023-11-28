import { GovConsentConfig } from './GovConsentConfig'
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

  constructor(consentsUpdateCallback: ConsentsUpdateCallback, apiUrl: string) {
    /**
      Initialises _GovConsent object by performing the following:
      1. Removes 'uid' from URL.
      2. Sets 'uid' attribute from cookie or URL.
      3. Fetches consent status from API if 'uid' exists.
      4. Notifies event listeners with API response.

      @arg consentsUpdateCallback: function(consents, consentsPreferencesSet, error) - callback when the consents are updated
      "consents": this is the consents object. It has the following properties: "essential", "usage", "campaigns", "settings". Each property is a boolean.
      "consentsPreferencesSet": true if the consents have been set for this user and this domain. Typically, only display the cookie banner if this is true.
      "error": if an error occurred, this is the error object. Otherwise, this is null.

      @arg apiUrl: string - the url of the API. Required.
      */

    this._consentsUpdateCallback = consentsUpdateCallback

    this.validateCallback()

    this.config = new GovConsentConfig(apiUrl)
    this.hideUIDParameter()

    // get the current uid from the cookie or the URL if it exists
    this.updateUID(this.config.uidFromUrl || this.config.uidFromCookie)

    if (!this.uid) {
      this._consentsUpdateCallback(null, false, null)
    } else {
      var getConsentsUrl = this.config.apiUrl.concat(this.uid)

      try {
        request(
          getConsentsUrl,
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
        this.updateBrowserConsents(GovSingleConsent.REJECT_ALL)
        this._consentsUpdateCallback(
          GovSingleConsent.REJECT_ALL,
          GovSingleConsent.isConsentPreferencesSet(),
          error
        )
      }
    }
  }

  setConsents(consents: Consents): void {
    if (!consents) {
      throw new Error('consents is required in GovSingleConsent.setConsents()')
    }

    var url = this.config.apiUrl.concat(this.uid || '')

    const successCallback = (response) => {
      this.updateUID(response.uid)
      this.updateBrowserConsents(consents)
      this._consentsUpdateCallback(
        consents,
        GovSingleConsent.isConsentPreferencesSet(),
        null
      )
    }

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
      this.updateBrowserConsents(GovSingleConsent.REJECT_ALL)
      this._consentsUpdateCallback(
        GovSingleConsent.REJECT_ALL,
        GovSingleConsent.isConsentPreferencesSet(),
        error
      )
    }
  }

  static getConsents(): Consents | null {
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

  private updateUID(uid): void {
    /**
     * Sets the new UID, updates page links and sets the UID cookie.
     */

    if (!uid || uid === this.uid) {
      return
    }

    this.uid = uid

    // Get origins
    request(
      this.config.apiUrl.replace('/consent/', '/origins/'),
      {},
      // Update links with UID
      (origins) => this.addUIDtoCrossOriginLinks(origins, uid)
    )

    // Update UID cookie
    this.setUIDCookie(uid)
  }

  private addUIDtoCrossOriginLinks(origins, uid): void {
    /**
     * Adds uid URL parameter to consent sharing links.
     * Only links with known origins are updated.
     */

    var links = document.querySelectorAll('a[href]')
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

  private validateCallback(): void {
    if (!this._consentsUpdateCallback) {
      throw new Error('Argument consentsUpdateCallback is required')
    }

    if (typeof this._consentsUpdateCallback !== 'function') {
      throw new Error('Argument consentsUpdateCallback must be a function')
    }
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
