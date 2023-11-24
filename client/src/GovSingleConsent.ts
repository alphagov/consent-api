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

  constructor(consentsUpdateCallback: ConsentsUpdateCallback) {
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
      */

    this._consentsUpdateCallback = consentsUpdateCallback

    this.validateCallback()

    this.config = new GovConsentConfig()
    this.hideUIDParameter()

    // get the current uid from the cookie or the URL if it exists
    this.updateUID(this.config.uidFromUrl || this.config.uidFromCookie)
    if (this.uid) {
      var getConsentsUrl = this.config.getApiUrl().concat(this.uid)

      try {
        request(
          getConsentsUrl,
          { timeout: 1000 },
          ({ status: consents }: { status: Consents }) => {
            this.setConsents(consents)
            this._consentsUpdateCallback(
              consents,
              this.areCookiesPreferencesSet(),
              null
            )
          }
        )
      } catch (error) {
        this.setConsents(GovSingleConsent.REJECT_ALL)
        this._consentsUpdateCallback(
          GovSingleConsent.REJECT_ALL,
          this.areCookiesPreferencesSet(),
          error
        )
      }
    }
  }

  setStatus(status, statusSetCallback, onErrorCallback): void {
    if (!status) {
      throw new Error('status is required in GovSingleConsent.setStatus()')
    }

    var url = this.config.getApiUrl().concat(this.uid || '')

    const callback = (response) => {
      // get the current uid from the API if we don't already have one
      this.updateUID(response.uid)
      if (statusSetCallback) {
        statusSetCallback()
      }
    }

    try {
      request(
        url,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'status='.concat(JSON.stringify(status)),
        },
        callback
      )
    } catch (error) {
      if (onErrorCallback) {
        onErrorCallback(error)
      } else {
        throw error
      }
    }
  }

  areCookiesPreferencesSet(): boolean {
    const value = getCookie(this.config.PREFERENCES_SET_COOKIE_NAME, null)
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
      this.config.getApiUrl().replace('/consent/', '/origins/'),
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
            this.config.UID_KEY,
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
      throw new Error('_consentsUpdateCallback must be a function')
    }
  }

  private setUIDCookie(uid: string): void {
    const cookieName = this.config.UID_KEY
    const lifetime = this.config.COOKIE_LIFETIME
    setCookie(cookieName, uid, lifetime)
  }

  private setConsents(consents: Consents): void {
    this.setConsentsCookie(consents)
    this.setPreferencesSetCookie(true)
  }

  private setConsentsCookie(consents: Consents): void {
    const consentsCookieName = this.config.CONSENTS_COOKIE_NAME
    const value = JSON.stringify(consents)
    const lifetime = this.config.COOKIE_LIFETIME
    setCookie(consentsCookieName, value, lifetime)
  }

  private setPreferencesSetCookie(value: boolean): void {
    const cookieName = this.config.PREFERENCES_SET_COOKIE_NAME
    const lifetime = this.config.COOKIE_LIFETIME
    setCookie(cookieName, value.toString(), lifetime)
  }

  private hideUIDParameter(): void {
    history.replaceState(
      null,
      null,
      removeUrlParameter(location.href, this.config.UID_KEY)
    )
  }
}
