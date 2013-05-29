# -*- coding: utf8 -*-
import re

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

CURRENCIES = {
    'AUD': 'Australian Dollars',
    'CAD': 'Canadian Dollars',
    'CHF': 'Swiss Francs',
    'COP': 'Colombian Pesos',
    'DKK': 'Danish Krone',
    'EGP': 'Egyptian Pound',
    'EUR': 'Euro',
    'GBP': 'Pounds Sterling',
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
