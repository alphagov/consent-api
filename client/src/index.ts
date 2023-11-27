import { isBrowser } from './utils'
import { GovSingleConsent } from './GovSingleConsent'

if (isBrowser()) {
  ;(window as any).GovSingleConsent = GovSingleConsent
}

export { GovSingleConsent }
