import { isBrowser } from './utils'
import { GovSingleConsent } from './GovSingleConsent'

if (isBrowser()) {
  window.GovSingleConsent = GovSingleConsent
}
