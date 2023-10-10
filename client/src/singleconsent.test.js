const { _GovConsent, setUid, request } = require('./singleconsent');
const xhrMock = require('xhr-mock').default;
const {sequence} = require('xhr-mock');


MOCK_API_URL = 'https://test-url.com/api/';
MOCK_COOKIE_NAME = 'consent_uid';
MOCK_UID = 'test-uid';

let originalCookie;


const mockCookie = (name=MOCK_COOKIE_NAME, value=MOCK_UID, days=1) => {
    const date = new Date();
    date.setTime(date.getTime() + (days*24*60*60*1000));
    const expires = `; expires=${date.toGMTString()}`;

    Object.defineProperty(document, 'cookie', {
        writable: true,
        value: `${name}=${value}${expires}; path=/`
        });
}

const resetCookie = (_document) => {
    if (originalCookie) {
        Object.defineProperty(_document, 'cookie', originalCookie);
    } else {
        delete _document.cookie
    }
}   

describe('Consent Management', () => {
    beforeAll(() => {
        originalCookie = Object.getOwnPropertyDescriptor(document, 'cookie');
    })
  beforeEach(() => {
    xhrMock.setup();
    document.body.innerHTML = `<div data-consent-api-url="${MOCK_API_URL}"></div>`;
  });

  afterEach(() => {
    xhrMock.teardown();
    resetCookie(document);
  });

  it('should initialise Consent UID to undefined if no initial UID', () => {
    const consentInstance = new _GovConsent();
    consentInstance.init();
    expect(consentInstance.uid).toBeUndefined();
  });
  
  it('should initialise Consent UID to cookie value if defined', () => {
    mockCookie()
    const response1 = ["a", "b"]
    const response2 = {status: 200}
    xhrMock.get(MOCK_API_URL, sequence([{status: 200, body: JSON.stringify(response1)}, {status: 200, body: JSON.stringify(response2)}]))
    const consentInstance = new _GovConsent();
    consentInstance.init();
    expect(consentInstance.uid).toBe(MOCK_UID);
  });
});
