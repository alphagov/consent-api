/* global Utils, XMLHttpRequest */

(function () {
  'use strict'

  function Consent (apiUrl) {
    this.apiUrl = apiUrl
    const uidFromCookie = Utils.getCookie('uid')
    const uidFromUrl = Utils.getURLParameter('uid')
    if (uidFromCookie) {
      console.log('Consent: UID from cookie')
    } else if (uidFromUrl) {
      console.log('Consent: UID from URL parameter')
    }
    this.uid = uidFromCookie || uidFromUrl
    console.log('Consent: UID =', this.uid)
    this.eventListeners = {
      ConsentStatusLoaded: [],
      ConsentStatusSet: [],
      ConsentUidSet: [
        this.decorateLinks,
        this.setUidCookie
      ]
    }
  }

  Consent.prototype.init = function () {
    this.undecorateUrl()

    if (this.uid) {
      this.dispatchEvent('ConsentUidSet', this.uid)

      this.getStatus(function (response) {
        this.dispatchEvent('ConsentStatusLoaded', response.status)
      }.bind(this))
    }
  }

  Consent.prototype.setUidCookie = function (uid) {
    console.log('Consent.setUidCookie:', uid)
    Utils.setCookie('uid', uid, { days: 365 })
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

  Consent.prototype.undecorateUrl = function () {
    let editedUrl = Utils.removeURLParameter(window.location.href, 'uid')
    if (editedUrl.slice(-1) === '?') {
      editedUrl = editedUrl.slice(0, -1)
    }
    if (window.location.href !== editedUrl) {
      console.log('Consent.undecorateUrl:', window.location.href, '->', editedUrl)
      window.history.replaceState(null, null, editedUrl)
    }
  }

  Consent.prototype.getApiEndpoint = function () {
    return this.apiUrl.concat('consent', this.uid ? '/'.concat(this.uid) : '')
  }

  Consent.prototype.getStatus = function (callback) {
    const request = new XMLHttpRequest()
    request.onreadystatechange = function () {
      if (request.readyState === XMLHttpRequest.DONE) {
        let responseJSON = {}
        if (request.status === 0 || (request.status >= 200 && request.status < 400)) {
          responseJSON = JSON.parse(request.responseText)
          if (responseJSON) {
            console.log('Consent.getStatus: response =', responseJSON)
            callback(responseJSON)
          }
        }
      }
    }
    request.open('GET', this.getApiEndpoint())
    request.send()
  }

  Consent.prototype.setStatus = function (status) {
    if (status) {
      console.log('Consent.setStatus:', status)
      const request = new XMLHttpRequest()
      request.onreadystatechange = function () {
        if (request.readyState === XMLHttpRequest.DONE) {
          let responseJSON = {}
          if (request.status === 0 || (request.status >= 200 && request.status < 400)) {
            responseJSON = JSON.parse(request.responseText)
            if (responseJSON) {
              console.log('Consent.setStatus: response =', responseJSON)
              if (responseJSON.uid !== this.uid) {
                this.dispatchEvent('ConsentUidSet', responseJSON.uid)
              }
              this.dispatchEvent('ConsentStatusSet', responseJSON.status)
            }
          }
        }
      }.bind(this)
      request.open('POST', this.getApiEndpoint())
      request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
      request.send('status='.concat(JSON.stringify(status)))
    }
  }

  Consent.prototype.decorateLinks = function (uid) {
    if (uid) {
      console.log('Consent.decorateLinks:', uid)
      const nodes = document.querySelectorAll('[data-consent-share][href]')
      for (let index = 0; nodes.length > index; index++) {
        console.log('Adding event listener to', nodes[index])
        nodes[index].addEventListener('click', function (event) {
          const url = event.target.getAttribute('href')
          const decoratedUrl = Utils.addURLParameter(url, 'uid', uid)
          console.log(`Consent.decorateLinks: ${url} -> ${decoratedUrl}`)
          event.target.setAttribute('href', decoratedUrl)
        })
      }
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    const node = document.querySelector('[data-consent-api-url]')
    if (node) {
      window.Consent = new Consent(node.dataset.consentApiUrl)
      window.Consent.init()
    }
  })
})()
