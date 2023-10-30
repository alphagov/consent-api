import { GovConsentConfig } from './GovConsentConfig'
import {
  addUrlParameter,
  getOriginFromLink,
  isCrossOrigin,
  removeUrlParameter,
  request,
} from './utils'

export class GovSingleConsent {
  static COOKIE_LIFETIME = 365 * 24 * 60 * 60 * 1000
  static ACCEPT_ALL = {
    essential: true,
    usage: true,
    campaigns: true,
    settings: true,
  }
  static REJECT_ALL = {
    essential: true,
    usage: false,
    campaigns: false,
    settings: false,
  }

  updateConsentsCallback: Function
  revokeConsentsCallback: Function

  config: GovConsentConfig

  uid?: string | null

  constructor(
    updateConsentsCallback: Function,
    revokeConsentsCallback: Function
  ) {
    /**
      Initialises _GovConsent object by performing the following:
      1. Removes 'uid' from URL.
      2. Sets 'uid' attribute from cookie or URL.
      3. Fetches consent status from API if 'uid' exists.
      4. Notifies event listeners with API response.

      @arg updateConsentsCallback: function(status) - callback to update consent status - response consents object passed
      @arg revokeConsentsCallback: function() - callback to revoke all consents - error is passed
      */

    this.updateConsentsCallback = updateConsentsCallback
    this.revokeConsentsCallback = revokeConsentsCallback

    this.validateCallbacks()

    this.config = new GovConsentConfig()

    // get the current uid from the cookie or the URL if it exists
    this.updateUID(this.config.uidFromCookie || this.config.uidFromUrl)
    if (this.uid) {
      var getConsentsUrl = this.config.getApiUrl().concat(this.uid)

      try {
        request(getConsentsUrl, { timeout: 1000 }, (responseData) => {
          this.updateConsentsCallback(responseData.status)
        })
      } catch (error) {
        this.revokeConsentsCallback(error)
      }
    }
  }

  private updateUID(uid) {
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

  private addUIDtoCrossOriginLinks(origins, uid) {
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
            this.config.uidKey,
            uid
          )
        })
      }
    })
  }

  private setUIDCookie(uid) {
    document.cookie = this.config.uidKey
      .concat('=', uid)
      .concat(
        '; path=/',
        '; max-age='.concat(GovSingleConsent.COOKIE_LIFETIME.toString()),
        document.location.protocol === 'https:' ? '; Secure' : ''
      )
  }

  setStatus(status, statusSetCallback, onErrorCallback) {
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

  private validateCallbacks() {
    if (!this.updateConsentsCallback || !this.revokeConsentsCallback) {
      throw new Error(
        'updateConsentsCallback and revokeConsentsCallback are required'
      )
    }

    if (
      typeof this.updateConsentsCallback !== 'function' ||
      typeof this.revokeConsentsCallback !== 'function'
    ) {
      throw new Error(
        'updateConsentsCallback and revokeConsentsCallback must be functions'
      )
    }
  }

  private hideUIDParameter() {
    history.replaceState(
      null,
      null,
      removeUrlParameter(location.href, this.config.uidKey)
    )
  }
}
