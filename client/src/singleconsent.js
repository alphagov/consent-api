'use strict'

function _GovConsentConfig() {
  var uidKey = 'gov_singleconsent_uid'
  return {
    uidKey: uidKey,
    uidFromCookie: findByKey(uidKey, document.cookie.split(';')),
    uidFromUrl: findByKey(uidKey, parseUrl(location.href).params),
    getApiUrl: function () {
      var el = document.querySelector('[data-gov-singleconsent-api-url]')
      return el
        ? el.dataset.govSingleconsentApiUrl.replace(/\/?$/, '/')
        : 'https://consent-api-bgzqvpmbyq-nw.a.run.app/api/v1/consent/'
    },
  }
}

function GovSingleConsent() {
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
}

function validateCallbacks(updateConsentsCallback, revokeConsentsCallback) {
  if (!updateConsentsCallback || !revokeConsentsCallback) {
    throw new Error(
      'updateConsentsCallback and revokeConsentsCallback are required'
    )
  }

  if (
    typeof updateConsentsCallback !== 'function' ||
    typeof revokeConsentsCallback !== 'function'
  ) {
    throw new Error(
      'updateConsentsCallback and revokeConsentsCallback must be functions'
    )
  }
}

GovSingleConsent.prototype.init = function (
  updateConsentsCallback,
  revokeConsentsCallback
) {
  /**
    Initialises _GovConsent object by performing the following:
    1. Removes 'uid' from URL.
    2. Sets 'uid' attribute from cookie or URL.
    3. Fetches consent object from API if 'uid' exists.
    4. Notifies event listeners with API response.

    @arg updateConsentsCallback: function(consent) - callback to update consent - response consent object passed
    @arg revokeConsentsCallback: function() - callback to revoke all consent - error is passed
    */

  validateCallbacks(updateConsentsCallback, revokeConsentsCallback)

  this.updateConsentsCallback = updateConsentsCallback
  this.revokeConsentsCallback = revokeConsentsCallback

  var consentConfig = _GovConsentConfig()

  // hide uid URL parameter
  history.replaceState(
    null,
    null,
    removeUrlParameter(location.href, consentConfig.uidKey)
  )

  // get the current uid from the cookie or the URL if it exists
  this.updateUID.bind(this)(
    consentConfig.uidFromCookie || consentConfig.uidFromUrl
  )
  if (this.uid) {
    var getConsentsUrl = _GovConsentConfig().getApiUrl().concat(this.uid)

    try {
      request(
        getConsentsUrl,
        { timeout: 1000 },
        function (responseData) {
          this.updateConsentsCallback(responseData.consent)
        }.bind(this)
      )
    } catch (error) {
      this.revokeConsentsCallback(error)
    }
  }
}

GovSingleConsent.prototype.setConsent = function (
  consent,
  consentSetCallback,
  onErrorCallback
) {
  if (!consent) {
    throw new Error('consent is required in GovSingleConsent.setConsents()')
  }

  var url = _GovConsentConfig()
    .getApiUrl()
    .concat(this.uid || '')

  var callback = function (response) {
    // get the current uid from the API if we don't already have one
    this.updateUID.bind(this)(response.uid)
    if (consentSetCallback) {
      consentSetCallback()
    }
  }.bind(this)

  try {
    request(
      url,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'consent='.concat(JSON.stringify(consent)),
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

GovSingleConsent.prototype.addUIDtoCrossOriginLinks = function (origins, uid) {
  /**
   * Adds uid URL parameter to consent sharing links.
   * Only links with known origins are updated.
   */

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

GovSingleConsent.prototype.setUIDCookie = function (uid) {
  document.cookie = _GovConsentConfig()
    .uidKey.concat('=', uid)
    .concat(
      '; path=/',
      '; max-age='.concat(GovSingleConsent.COOKIE_LIFETIME),
      document.location.protocol === 'https:' ? '; Secure' : ''
    )
}

GovSingleConsent.prototype.updateUID = function (uid) {
  /**
   * Sets the new UID, updates page links and sets the UID cookie.
   */

  if (!uid || uid === this.uid) {
    return
  }

  this.uid = uid

  // Get origins
  request(
    _GovConsentConfig().getApiUrl().replace('/consent/', '/origins/'),
    {},
    // Update links with UID
    function (origins) {
      this.addUIDtoCrossOriginLinks(origins, uid)
    }.bind(this)
  )

  // Update UID cookie
  this.setUIDCookie(uid)
}

function request(url, options, onSuccess) {
  var req = new XMLHttpRequest()
  var isTimeout = false
  options = options || {}

  req.onreadystatechange = function () {
    if (req.readyState === req.DONE) {
      if (req.status >= 200 && req.status < 400) {
        onSuccess(JSON.parse(req.responseText))
      } else if (req.status === 0 && req.timeout > 0) {
        // Possible timeout, waiting for ontimeout event
        // Timeout will throw a status = 0 request
        // onreadystatechange preempts ontimeout
        // And we can't know for sure at this stage if it's a timeout
        setTimeout(function () {
          if (isTimeout) {
            return
          }
          throw new Error(
            'Request to ' + url + ' failed with status: ' + req.status
          )
        }, 500)
      } else {
        throw new Error(
          'Request to ' + url + ' failed with status: ' + req.status
        )
      }
    }
  }

  if (options.timeout) {
    req.timeout = options.timeout
  }

  req.ontimeout = function () {
    isTimeout = true
    throw new Error('Request to ' + url + ' timed out')
  }

  req.open(options.method || 'GET', url, true)

  var headers = options.headers || {}
  for (var name in headers) {
    req.setRequestHeader(name, headers[name])
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
  window.GovSingleConsent = new GovSingleConsent()
} else {
  module.exports = {
    GovSingleConsent: GovSingleConsent,
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
