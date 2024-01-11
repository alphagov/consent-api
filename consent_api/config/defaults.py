class DEV:
    DEFAULT_CONSENT_API_ORIGIN = "http://consent-api"
    DEFAULT_OTHER_SERVICE_ORIGIN = "http://dummy-service-1"


class STAGING:
    DEFAULT_CONSENT_API_ORIGIN = "https://gds-single-consent-staging.app/"
    DEFAULT_OTHER_SERVICE_ORIGIN = ""


class PROD:
    DEFAULT_CONSENT_API_ORIGIN = ""
    DEFAULT_OTHER_SERVICE_ORIGIN = ""
