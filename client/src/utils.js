let Utils;

(function () {
  'use strict'

  Utils = window.Utils = {}

  Utils.ALL_COOKIES = {
    essential: true,
    usage: true,
    campaigns: true,
    settings: true
  }

  Utils.ESSENTIAL_COOKIES = {
    essential: true,
    usage: false,
    campaigns: false,
    settings: false
  }

  Utils.acceptedAdditionalCookies = function (status) {
    let responded = false; let acceptedAdditionalCookies = false
    for (const key in status) {
      if (Object.prototype.hasOwnProperty.call(status, key)) {
        responded = true
        if (key !== 'essential') {
          acceptedAdditionalCookies ||= status[key]
        }
      }
    }
    return { responded, acceptedAdditionalCookies }
  }

  Utils.getQueryString = function (url) {
    return url.slice((url.indexOf('?') + 1) || url.length)
  }

  Utils.getURLParameter = function (name) {
    name += '='
    const pairs = Utils.getQueryString(window.location.href).split('&')
    for (let index = 0; pairs.length > index; index++) {
      if (pairs[index].slice(0, name.length) === name) {
        return pairs[index].slice(name.length)
      }
    }
  }

  Utils.getCookie = function (name, defaultValue) {
    name += '='
    const cookies = document.cookie.split(';')
    for (let index = 0; cookies.length > index; index++) {
      if (cookies[index].trim().slice(0, name.length) === name) {
        return decodeURIComponent(cookies[index].trim().slice(name.length))
      }
    }
    return defaultValue || null
  }

  Utils.setCookie = function (name, value, options) {
    options = (options || {})
    let cookieString = name.concat('=', value, '; path=/')
    if (options.days) {
      const expiryDate = new Date()
      expiryDate.setTime(expiryDate.getTime() + (options.days * 24 * 60 * 60 * 1000))
      cookieString += '; expires='.concat(expiryDate.toGMTString())
    }
    if (document.location.protocol === 'https:') {
      cookieString += '; Secure'
    }
    document.cookie = cookieString
  }

  Utils.addURLParameter = function (url, name, value) {
    name = encodeURIComponent(name).concat('=')
    value = encodeURIComponent(value)
    const [address, queryString] = url.split('?')
    const parameters = (queryString || '').split('&')
    let index = 0; const newParameters = []; let modified = false
    for (; parameters.length > index; index++) {
      if (parameters[index].slice(0, name.length) === name) {
        newParameters[newParameters.length] = name.concat(value)
        modified = true
      } else if (parameters[index] !== '') {
        newParameters[newParameters.length] = parameters[index]
      }
    }
    if (!modified) {
      newParameters[newParameters.length] = name.concat(value)
    }
    return [address, newParameters.join('&')].join('?')
  }

  Utils.removeURLParameter = function (url, name) {
    name += '='
    const [address, queryString] = url.split('?')
    const parameters = (queryString || '').split('&')
    for (let index = 0; parameters.length > index; index++) {
      if (parameters[index].slice(0, name.length) === name) {
        parameters.splice(index--, 1)
      }
    }
    return [address, parameters.join('&')].join('?')
  }
})()
