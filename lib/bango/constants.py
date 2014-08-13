# -*- coding: utf8 -*-
import re

from suds.options import Options
from suds.reader import Reader

from solitude.base import invert

STATUS_UNKNOWN = 0
STATUS_GOOD = 1
STATUS_BAD = 2
STATUSES = {
    'unknown': STATUS_UNKNOWN,
    'good': STATUS_GOOD,
    'bad': STATUS_BAD,
}

STATUS_CHOICES = invert(STATUSES)

ACCESS_DENIED = 'ACCESS_DENIED'
ALREADY_REFUNDED = 'ALREADY_REFUNDED'
BANGO_ALREADY_PREMIUM_ENABLED = 'BANGO_ALREADY_PREMIUM_ENABLED'
BANK_DETAILS_EXIST = 'BANK_DETAILS_EXIST'
CANCEL = 'CANCEL'
CANT_REFUND = 'CANT_REFUND'
INTERNAL_ERROR = 'INTERNAL_ERROR'
# There is one of these for every field.
INVALID = re.compile('^INVALID_\w+$')
INVALID_PERSON = 'INVALID_PERSON'
NO_BANGO_EXISTS = 'NO_BANGO_EXISTS'
OK = 'OK'
PENDING = 'PENDING'
NOT_SUPPORTED = 'NOT_SUPPORTED'
REQUIRED_CONFIGURATION_MISSING = 'REQUIRED_CONFIGURATION_MISSING'
SBI_ALREADY_ACCEPTED = 'SBI_ALREADY_ACCEPTED'
SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE'
VAT_NUMBER_DOES_NOT_EXIST = 'VAT_NUMBER_DOES_NOT_EXIST'

HEADERS_SERVICE = 'x-solitude-service'
HEADERS_SERVICE_GET = 'HTTP_X_SOLITUDE_SERVICE'

# A whitelist of headers that we need to pass through from suds to the
# proxy. These will be passed through as HTTP headers to the proxy.
HEADERS_WHITELIST = {'SOAPAction': 'x-solitude-soapaction'}
HEADERS_WHITELIST_INVERTED = dict(invert(HEADERS_WHITELIST))

CURRENCIES = {
    'AUD': 'Australian Dollars',
    # BDT not in docs, but added in for bug 1043481.
    'BDT': 'Bangladesh Taka',
    'CAD': 'Canadian Dollars',
    'CHF': 'Swiss Francs',
    'COP': 'Colombian Pesos',
    'DKK': 'Danish Krone',
    'EGP': 'Egyptian Pound',
    'EUR': 'Euro',
    'GBP': 'Pounds Sterling',
    'HUF': 'Hungarian Forint',
    'IDR': 'Indonesian Rupiah',
    'MXN': 'Mexican Pesos',
    'MYR': 'Malaysian Ringgit',
    'NOK': 'Norwegian Krone',
    'NZD': 'New Zealand Dollars',
    'PHP': 'Philippine Peso',
    'PLN': u'Polish Złoty',
    'QAR': 'Qatar riyal',
    'SEK': 'Swedish Krone',
    'SGD': 'Singapore Dollar',
    'THB': 'Thai Baht',
    'USD': 'US Dollars',
    'ZAR': 'South African Rand',
}

# TODO: Expand this bug 814492.
CATEGORIES = {
    1: 'Games'
}

# List of valid country codes: http://en.wikipedia.org/wiki/ISO_3166-1_alpha-3
COUNTRIES = [
    'AFG', 'ALA', 'ALB', 'DZA', 'ASM', 'AND', 'AGO', 'AIA', 'ATA', 'ATG',
    'ARG', 'ARM', 'ABW', 'AUS', 'AUT', 'AZE', 'BHS', 'BHR', 'BGD', 'BRB',
    'BLR', 'BEL', 'BLZ', 'BEN', 'BMU', 'BTN', 'BOL', 'BES', 'BIH', 'BWA',
    'BVT', 'BRA', 'IOT', 'BRN', 'BGR', 'BFA', 'BDI', 'KHM', 'CMR', 'CAN',
    'CPV', 'CYM', 'CAF', 'TCD', 'CHL', 'CHN', 'CXR', 'CCK', 'COL', 'COM',
    'COG', 'COD', 'COK', 'CRI', 'CIV', 'HRV', 'CUB', 'CUW', 'CYP', 'CZE',
    'DNK', 'DJI', 'DMA', 'DOM', 'ECU', 'EGY', 'SLV', 'GNQ', 'ERI', 'EST',
    'ETH', 'FLK', 'FRO', 'FJI', 'FIN', 'FRA', 'GUF', 'PYF', 'ATF', 'GAB',
    'GMB', 'GEO', 'DEU', 'GHA', 'GIB', 'GRC', 'GRL', 'GRD', 'GLP', 'GUM',
    'GTM', 'GGY', 'GIN', 'GNB', 'GUY', 'HTI', 'HMD', 'VAT', 'HND', 'HKG',
    'HUN', 'ISL', 'IND', 'IDN', 'IRQ', 'IRL', 'IMN', 'ISR', 'ITA',  # IRN
    'JAM', 'JPN', 'JEY', 'JOR', 'KAZ', 'KEN', 'KIR', 'KOR', 'KOS',  # PRK
    'KWT', 'KGZ', 'LAO', 'LVA', 'LBN', 'LSO', 'LBR', 'LBY', 'LIE', 'LTU',
    'LUX', 'MAC', 'MKD', 'MDG', 'MWI', 'MYS', 'MDV', 'MLI', 'MLT', 'MHL',
    'MTQ', 'MRT', 'MUS', 'MYT', 'MEX', 'FSM', 'MDA', 'MCO', 'MNG', 'MNE',
    'MSR', 'MAR', 'MOZ', 'MMR', 'NAM', 'NRU', 'NPL', 'NLD', 'NCL', 'NZL',
    'NIC', 'NER', 'NGA', 'NIU', 'NFK', 'MNP', 'NOR', 'OMN', 'PAK', 'PLW',
    'PSE', 'PAN', 'PNG', 'PRY', 'PER', 'PHL', 'PCN', 'POL', 'PRT', 'PRI',
    'QAT', 'REU', 'ROU', 'RUS', 'RWA', 'BLM', 'SHN', 'KNA', 'LCA', 'MAF',
    'SPM', 'VCT', 'WSM', 'SMR', 'STP', 'SAU', 'SEN', 'SRB', 'SCG', 'SYC',
    'SLE', 'SGP', 'SXM', 'SVK', 'SVN', 'SLB', 'SOM', 'ZAF', 'SGS', 'SSD',
    'ESP', 'LKA', 'SDN', 'SUR', 'SJM', 'SWZ', 'SWE', 'CHE', 'SYR', 'TWN',
    'TJK', 'TZA', 'THA', 'TLS', 'TGO', 'TKL', 'TON', 'TTO', 'TUN', 'TUR',
    'TKM', 'TCA', 'TUV', 'UGA', 'UKR', 'ARE', 'GBR', 'USA', 'UMI', 'URY',
    'UZB', 'VUT', 'VEN', 'VNM', 'VGB', 'VIR', 'WLF', 'ESH', 'YEM', 'ZMB',
    'ZWE',
]

RATINGS = ['GLOBAL', 'UNIVERSAL', 'RESTRICTED', 'GENERAL']
RATINGS_SCHEME = ['GLOBAL', 'USA']

# The Bango payment types available for micro payments.
MICRO_PAYMENT_TYPES = ('OPERATOR', 'PSMS', 'INTERNET')
# The Bango payment types available for all payments.
PAYMENT_TYPES = MICRO_PAYMENT_TYPES + ('CARD',)


def match(status, constant):
    # There's going to be an INVALID_ something for every field in every form
    # adding them all to this is boring. Let's make a regex to map them.
    if isinstance(constant, basestring):
        return status, constant
    return constant.match(status)


# This is a map of Bango WSDLs. They are divided into prod and test.
# Each file has a nickname (eg: exporter) followed by the URL and file.
WSDL_MAP = {
    'prod': {
        'exporter': {
            'url': 'https://webservices.bango.com/mozillaexporter/?WSDL',
            'file': 'mozilla_exporter.wsdl'
        },
        'billing': {
            'url': 'https://webservices.bango.com/billingconfiguration/?WSDL',
            'file': 'billing_configuration.wsdl'
        },
        'billing_v2': {
            'url': 'https://webservices.bango.com'
                   '/billingconfiguration_v2_0/?WSDL',
            'file': 'billing_configuration_v2_0.wsdl'
        },
        'billing_service': {
            'url': 'https://webservices.bango.com'
                   '/billingconfiguration_v2_0/Service.svc?xsd=xsd0',
            'file': 'billing_configuration_service.wsdl'
        },
        'direct': {
            'url': 'https://webservices.bango.com/directbilling_v3_1/?wsdl',
            'file': 'direct_billing.wsdl'
        },
        'token': {
            'url': 'https://mozilla.bango.net/_/ws/tokenchecker.asmx?wsdl',
            'file': 'token_checker.wsdl'
        }
    },
    'test': {
        'exporter': {
            'url': 'https://webservices.test.bango.org/mozillaexporter/?WSDL',
            'file': 'mozilla_exporter.wsdl'
        },
        'billing': {
            'url': 'https://webservices.test.bango.org'
                   '/billingconfiguration/?WSDL',
            'file': 'billing_configuration.wsdl'
        },
        'billing_v2': {
            'url': 'https://webservices.test.bango.org'
                   '/billingconfiguration_v2_0/?WSDL',
            'file': 'billing_configuration_v2_0.wsdl'
        },
        'billing_service': {
            'url': 'https://webservices.test.bango.org'
                   '/billingconfiguration_v2_0/Service.svc?xsd=xsd0',
            'file': 'billing_configuration_service.wsdl'
        },
        'direct': {
            'url': 'https://webservices.test.bango.org'
                   '/directbilling_v3_1/?wsdl',
            'file': 'direct_billing.wsdl'
        },
        'token': {
            'url': 'https://mozilla.test.bango.org'
                   '/_/ws/tokenchecker.asmx?wsdl',
            'file': 'token_checker.wsdl'
        }
    }
}


def key(mapping):
    """
    Suds can ask for the URL, or the mangled cache. This mapping
    ensures that if suds asks for a:
    * URL
    * wsdl file that's been saved to the cache
    * document file that's been saved to the cache
    ... we've got a valid response.
    """
    res = {}

    def mangle(url, typ):
        return Reader(Options()).mangle(url, typ)

    for k, v in mapping.items():
        res[v['url']] = v['file']
        res[mangle(v['url'], 'document')] = v['file']
        res[mangle(v['url'], 'wsdl')] = v['file']
    return res


WSDL_MAP_MANGLED = {
    'prod': key(WSDL_MAP['prod']),
    'test': key(WSDL_MAP['test'])
}
