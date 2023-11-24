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

type ConsentsUpdatedCallback = (consents: Consents) => void
type ConsentsRevokedCallback = (error: Error, consents: Consents) => void

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

  _consentsUpdatedCallback: ConsentsUpdatedCallback
  _consentsRevokedCallback: ConsentsRevokedCallback

  config: GovConsentConfig

  uid?: string | null

  constructor(
    consentsUpdatedCallback: ConsentsUpdatedCallback,
    consentsRevokedCallback: ConsentsRevokedCallback
  ) {
    /**
      Initialises _GovConsent object by performing the following:
      1. Removes 'uid' from URL.
      2. Sets 'uid' attribute from cookie or URL.
      3. Fetches consent status from API if 'uid' exists.
      4. Notifies event listeners with API response.

      @arg updateConsentsCallback: function(status) - callback when the consents cookie is updated - status is passed
      @arg revokeConsentsCallback: function(error, status) - callback when the consents cookie is revoked - error and revoked status is passed
      */

    this._consentsUpdatedCallback = consentsUpdatedCallback
    this._consentsRevokedCallback = consentsRevokedCallback

    this.validateCallbacks()

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
            this.setConsentsCookie(consents)
            this._consentsUpdatedCallback(consents)
          }
        )
      } catch (error) {
        this.setConsentsCookie(GovSingleConsent.REJECT_ALL)
        this._consentsRevokedCallback(error, GovSingleConsent.REJECT_ALL)
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

  private validateCallbacks(): void {
    if (!this._consentsUpdatedCallback || !this._consentsRevokedCallback) {
      throw new Error(
        'updateConsentsCallback and revokeConsentsCallback are required'
      )
    }

    if (
      typeof this._consentsUpdatedCallback !== 'function' ||
      typeof this._consentsRevokedCallback !== 'function'
    ) {
      throw new Error(
        'updateConsentsCallback and revokeConsentsCallback must be functions'
      )
    }
  }

  private setUIDCookie(uid: string): void {
    const cookieName = this.config.UID_KEY
    const lifetime = this.config.COOKIE_LIFETIME
    setCookie(cookieName, uid, lifetime)
  }

  private setConsentsCookie(consents: Consents): void {
    const cookieName = this.config.CONSENTS_COOKIE_NAME
    const value = JSON.stringify(consents)
    const lifetime = this.config.COOKIE_LIFETIME
    setCookie(cookieName, value, lifetime)
  }

  private hideUIDParameter(): void {
    history.replaceState(
      null,
      null,
      removeUrlParameter(location.href, this.config.UID_KEY)
    )
  }
}
