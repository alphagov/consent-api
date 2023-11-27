/* eslint-disable */

/**
 * This Common JS example illustrates a potential usage of the "GovSingleConsent" library.
 *
 * Please note that this is not executable code; it's a guideline intended to show how one might
 * use the library within a Javascript application.
 *
 * The purpose of this example is to demonstrate the integration points and
 * typical interactions with the "GovSingleConsent" class.
 *
 * Functions such as "hideCookieBanner" or "sendErrorLog" are conceptual and represent
 * placeholders for your actual implementation.
 *
 * The constant `SINGLE_CONSENT_API_URL` is a dummy URL and should be replaced with the actual
 * endpoint from which the consent status can be fetched or to which it can be sent.
 */

const { GovSingleConsent } = require('govuk-single-consent')

const SINGLE_CONSENT_API_URL = 'dummy-url.gov.uk'

const onConsentsUpdated = (consents, consentsPreferencesSet, error) => {
  // Do something with the consents
  // e.g

  if (consentsPreferencesSet) {
    hideCookieBanner()
  }

  if (error) {
    sendErrorLog(error)
  }
}

const singleConsent = new GovSingleConsent(
  onConsentsUpdated,
  SINGLE_CONSENT_API_URL
)

/**
 * Some Cookie Banner Event Handlers
 */

const onRejectAllButtonClick = () => {
  singleConsent.setConsents(GovSingleConsent.REJECT_ALL)
}

const onAcceptAllButtonClick = () => {
  singleConsent.setConsents(GovSingleConsent.ACCEPT_ALL)
}

const onAcceptCustomConsentsButtonClick = (customConsents) => {
  singleConsent.setConsents(customConsents)
}

/**
 * Some Logic That Depends On Consents
 */

const sendToAnalytics = (event) => {
  if (!GovSingleConsent.hasConsentedToUsage()) {
    return
  }
  // Send event to analytics here
}
