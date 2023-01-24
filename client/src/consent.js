/* global Utils, XMLHttpRequest */

(function () {
  'use strict'

  function Consent () {
    this.sharedUID = Utils.getURLParameter('uid')
    this.undecorateURL()
    this.localUID = Utils.getCookie('uid')
    this.uid = this.sharedUID || this.localUID
    this.eventListeners = {
      statusShared: [
        this.updateCookiesPolicyCookie
      ],
      uidAssigned: [
        this.setUIDCookie,
        this.decorateLinks
      ]
    }
  }

  Consent.prototype.init = function () {
    this.apiURL = document.querySelector('[data-consent-api-url]').dataset.consentApiUrl

    if (!this.localUID && this.sharedUID) {
      this.setUIDCookie(this.uid)
    }

    this.status = {}

    this.getStatus((response) => {
      if (response) {
        if (!this.uid) {
          this.uid = response.uid
          this.dispatchEvent('uidAssigned', this.uid)
        }
        const meta = Utils.acceptedAdditionalCookies(response.status)
        if (meta.responded) {
          this.status = response.status
          this.dispatchEvent('statusShared', this.status)
        }
      }
    })
  }

  Consent.prototype.setUIDCookie = function (uid) {
    Utils.setCookie('uid', uid, { days: 365 })
  }

  Consent.prototype.updateCookiesPolicyCookie = function (cookiesPolicy) {
    Utils.setCookie('cookies_policy', JSON.stringify(cookiesPolicy), { days: 365 })
    Utils.setCookie('cookies_preferences_set', 'true')
  }

  Consent.prototype.addEventListener = function (eventName, callback) {
    if (eventName in this.eventListeners) {
      this.eventListeners[eventName].push(callback)
    }
  }

  Consent.prototype.dispatchEvent = function (eventName, details) {
    if (eventName in this.eventListeners) {
      this.eventListeners[eventName].forEach(function (callback) {
        callback(details)
      })
    }
  }

  Consent.prototype.undecorateURL = function () {
    const undecoratedURL = Utils.removeURLParameter(window.location.href, 'uid')
    window.history.replaceState(null, null, undecoratedURL)
  }

  Consent.prototype.getApiEndpoint = function () {
    return this.apiURL.concat('consent', this.uid ? '/'.concat(this.uid) : '')
  }

  Consent.prototype.getStatus = function (callback) {
    const request = new XMLHttpRequest()
    request.onreadystatechange = function () {
      if (request.readyState === XMLHttpRequest.DONE) {
        let responseJSON = {}
        if (request.status === 0 || (request.status >= 200 && request.status < 400)) {
          responseJSON = JSON.parse(request.responseText)
        }
        callback(responseJSON)
      }
    }
    request.open('GET', this.getApiEndpoint())
    request.send()
  }

  Consent.prototype.setStatus = function (status) {
    if (status) {
      this.status = status
      const request = new XMLHttpRequest()
      request.open('POST', this.getApiEndpoint())
      request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
      request.send('status='.concat(JSON.stringify(this.status)))
    }
  }

  Consent.prototype.decorateLinks = function (uid) {
    if (uid) {
      const nodes = document.querySelectorAll('[data-consent-share]')
      for (let index = 0; nodes.length > index; index++) {
        nodes[index].addEventListener('click', function (event) {
          if (event.target.hasAttribute('href')) {
            const url = event.target.getAttribute('href')
            const decoratedUrl = Utils.addURLParameter(url, 'uid', uid)
            event.target.setAttribute('href', decoratedUrl)
          }
        })
      }
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    window.Consent = new Consent()
    window.Consent.init()
  })
})()
