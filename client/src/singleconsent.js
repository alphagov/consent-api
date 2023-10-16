'use strict'

function _GovConsentConfig() {
  var uidKey = 'consent_uid'
  return {
    "uidKey": uidKey,
    uidFromCookie: findByKey(uidKey, document.cookie.split(';')),
    uidFromUrl: findByKey(uidKey, parseUrl(location.href).params),
    getApiUrl: function () {
      var el = document.querySelector('[data-consent-api-url]')
      return el
        ? el.dataset.consentApiUrl.replace(/\/?$/, '/')
        : 'https://consent-api-bgzqvpmbyq-nw.a.run.app/api/v1/consent/'
    },
  }
}

function _GovConsent() {
  // one year in milliseconds
  this.COOKIE_LIFETIME = 365 * 24 * 60 * 60 * 1000
  this.ACCEPT_ALL = {
    essential: true,
    usage: true,
    campaigns: true,
    settings: true,
  }

  this.REJECT_ALL = {
    essential: true,
    usage: false,
    campaigns: false,
    settings: false,
  }
  this.eventListeners = []
}

_GovConsent.prototype.init = function () {
  /**
    Initialises _GovConsent object by performing the following:
    1. Removes 'uid' from URL.
    2. Sets 'uid' attribute from cookie or URL.
    3. Fetches consent status from API if 'uid' exists.
    4. Notifies event listeners with API response.
    */
  var consentConfig = _GovConsentConfig()

  // hide uid URL parameter
  history.replaceState(
    null,
    null,
    removeUrlParameter(location.href, consentConfig.uidKey)
  )

  // get the current uid from the cookie or the URL if it exists
  setUid(this, consentConfig.uidFromCookie || consentConfig.uidFromUrl)
  if (this.uid) {
    request(
      _GovConsentConfig().getApiUrl().concat(this.uid),
      {},
      function (response) {
        this.eventListeners.forEach(function (callback) {
          callback(response.status)
        })
      }.bind(this)
    )
  }
}

_GovConsent.prototype.onStatusLoaded = function (callback) {
  this.eventListeners.push(callback)
}

_GovConsent.prototype.setStatus = function (status, callback) {
  if (status) {
    request(
      _GovConsentConfig()
        .getApiUrl()
        .concat(this.uid || ''),
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'status='.concat(JSON.stringify(status)),
      },
      function (response) {
        // get the current uid from the API if we don't already have one
        setUid(this, response.uid)
        if (callback) {
          callback()
        }
      }.bind(this)
    )
  }
}

// TODO: Make a setter method for uid?
function setUid(consent, uid) {
  /**
   * Updates uid in the consent object and performs the following:
   * 1. Sets 'uid' if it's different from the current one.
   * 2. Fetches list of known origins from API.
   * 3. Updates consent sharing links with new 'uid'.
   * 4. Sets a cookie with the new 'uid'.
   */
  if (uid && uid !== consent.uid) {
    consent.uid = uid

    // fetch known origins
    request(
      _GovConsentConfig().getApiUrl().replace('/consent/', '/origins/'),
      {},
      function (origins) {
        // add uid URL parameter to consent sharing links
        var links = document.querySelectorAll('a[href]')
        Array.prototype.forEach.call(links, function (link) {
          if (isCrossOrigin(link) && origins.indexOf(origin(link)) >= 0) {
            link.addEventListener('click', function (event) {
              event.target.href = addUrlParameter(
                event.target.href,
                _GovConsentConfig().uidKey,
                uid
              )
            })
          }
        })
      }
    )

    // set uid cookie
    document.cookie = _GovConsentConfig()
      .uidKey.concat('=', uid)
      .concat(
        '; path=/',
        '; max-age='.concat(_GovConsent.COOKIE_LIFETIME),
        document.location.protocol === 'https:' ? '; Secure' : ''
      )
  }
}

function request(url, options, callback) {
  var req = new XMLHttpRequest()
  options = options || {}
  req.onreadystatechange = function () {
    if (
      req.readyState === req.DONE &&
      (req.status === 0 || (req.status >= 200 && req.status < 400))
    ) {
      callback(JSON.parse(req.responseText))
    }
  }
  req.open(options.method || 'GET', url)
  for (var name in options.headers || {}) {
    req.setRequestHeader(name, options.headers[name])
  }
  req.send(options.body || null)
}

function addUrlParameter(url, name, value) {
  url = parseUrl(url)
  var newParam = name.concat('=', value)
  var modified = false
  findByKey(name, url.params, function (index) {
    url.params[index] = newParam
    modified = true
  })
  if (!modified) {
    url.params.push(newParam)
  }
  return buildUrl(url)
}

function removeUrlParameter(url, name) {
  url = parseUrl(url)
  findByKey(name, url.params, function (index) {
    url.params.splice(index--, 1)
  })
  return buildUrl(url)
}

function parseUrl(url) {
  var parts = url.split('?')
  return {
    address: parts[0],
    params: (parts[1] || '').split('&').filter(Boolean),
  }
}

function buildUrl(parts) {
  return [parts.address, parts.params.join('&')].join('?').replace(/\??$/, '')
}

function findByKey(key, keyvals, callback) {
  key += '='
  for (var index = 0; keyvals.length > index; index++) {
    if (keyvals[index].trim().slice(0, key.length) === key) {
      var value = keyvals[index].trim().slice(key.length)
      if (callback) {
        callback(index, value)
      } else {
        return value
      }
    }
  }
}

function isCrossOrigin(link) {
  return (
    link.protocol !== window.location.protocol ||
    link.hostname !== window.location.hostname ||
    (link.port || '80') !== (window.location.port || '80')
  )
}

function origin(link) {
  var origin = link.protocol.concat('//', link.hostname)
  if (link.port && link.port !== '80') {
    origin = origin.concat(':', link.port)
  }
  return origin
}

function isBrowser() {
  return typeof module === 'undefined'
}

if (isBrowser()) {
  window.Consent = new _GovConsent()

  document.addEventListener('DOMContentLoaded', function () {
    window.Consent.init()
  })
} else {
  module.exports = {
    "_GovConsent": _GovConsent,
    setUid: setUid,
    request: request,
    addUrlParameter: addUrlParameter,
    removeUrlParameter: removeUrlParameter,
    parseUrl: parseUrl,
    buildUrl: buildUrl,
    findByKey: findByKey,
    isCrossOrigin: isCrossOrigin,
    origin: origin,
  }
}
