/* global Consent, Utils */

(function () {
  function CookieSettings ($module) {
    this.$module = $module
  }

  CookieSettings.prototype.init = function () {
    this.$module.submitSettingsForm = this.submitSettingsForm.bind(this)
    this.$module.getFormValues = this.getFormValues.bind(this)
    this.$module.setFormValues = this.setFormValues.bind(this)

    document.querySelector('form[data-module=cookie-settings]')
      .addEventListener('submit', this.$module.submitSettingsForm)

    this.cookiesPolicy = JSON.parse(Utils.getCookie('cookies_policy'))
    if (!this.cookiesPolicy) {
      console.log('CookieSettings.init: no cookie, setting default ESSENTIAL_COOKIES')
      this.cookiesPolicy = Utils.ESSENTIAL_COOKIES
      Utils.setCookie('cookies_policy', JSON.stringify(this.cookiesPolicy), { days: 365 })
    }

    this.setFormValues(this.cookiesPolicy)

    Consent.addEventListener('ConsentStatusLoaded', function (status) {
      console.log('CookieSettings.handleConsentStatusLoaded:', status)
      this.setFormValues(status)
    }.bind(this))
  }

  CookieSettings.prototype.setFormValues = function (cookiesPolicy) {
    cookiesPolicy ||= this.cookiesPolicy
    console.log('CookieSettings.setFormValues: ', cookiesPolicy)

    for (const category in cookiesPolicy) {
      if (category === 'essential') {
        // this cannot be set by the user
        continue
      }
      const input = this.$module.querySelector(`input[name=cookies-${category}][value=${cookiesPolicy[category] ? 'on' : 'off'}]`)
      if (input) {
        input.checked = true
      }
    }
  }

  CookieSettings.prototype.getFormValues = function (form) {
    form = (form || this.$module)
    const formInputs = form.getElementsByTagName('input')
    const values = {}

    for (let i = 0; i < formInputs.length; i++) {
      const input = formInputs[i]
      if (input.checked) {
        const name = input.name.replace('cookies-', '')
        const value = input.value === 'on'

        values[name] = value
      }
    }

    values.essential = true

    return values
  }

  CookieSettings.prototype.submitSettingsForm = function (event) {
    event.preventDefault()

    this.cookiesPolicy = this.getFormValues(event.target)

    console.log('CookieSettings.submitSettingsForm: setting cookiesPolicy', this.cookiesPolicy)
    Utils.setCookie('cookies_policy', JSON.stringify(this.cookiesPolicy), { days: 365 })
    Utils.setCookie('cookies_preferences_set', true, { days: 365 })

    Consent.setStatus(this.cookiesPolicy)

    this.showConfirmationMessage()
  }

  CookieSettings.prototype.showConfirmationMessage = function () {
    const confirmationMessage = document.querySelector('div[data-cookie-confirmation]')
    // hide the message if already visible so assistive tech is triggered when it appears
    confirmationMessage.style.display = 'none'
    const previousPageLink = document.querySelector('.cookie-settings__prev-page')
    const referrer = CookieSettings.prototype.getReferrerLink()

    document.body.scrollTop = document.documentElement.scrollTop = 0

    if (referrer && referrer !== document.location.pathname) {
      previousPageLink.href = referrer
      previousPageLink.style.display = 'inline'
    } else {
      previousPageLink.style.display = 'none'
    }

    confirmationMessage.style.display = 'block'
  }

  CookieSettings.prototype.getReferrerLink = function () {
    return document.referrer ? new URL(document.referrer).pathname : false
  }

  document.addEventListener('DOMContentLoaded', function () {
    const nodes = document.querySelectorAll('[data-module~="cookie-settings"]')
    for (let index = 0; nodes.length > index; index++) {
      new CookieSettings(nodes[index]).init()
    }
  })
})()
