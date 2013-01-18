good_address = {
    'adminEmailAddress': 'admin@place.com',
    'supportEmailAddress': 'support@place.com',
    'financeEmailAddress': 'finance@place.com',
    'paypalEmailAddress': 'paypal@place.com',
    'vendorName': 'Some Company',
    'companyName': 'Some Company, LLC',
    'address1': '111 Somewhere',
    'addressCity': 'Pleasantville',
    'addressState': 'CA',
    'addressZipCode': '11111',
    'addressPhone': '4445551111',
    'countryIso': 'USA',
    'currencyIso': 'USD',
    'seller': 1,
}

good_email = {
    'packageId': 1,
    'emailAddress': 'something@somewhere.com'
}

good_bango_number = {
    'packageId': 1,
    'name': 'A name for the number',
    'categoryId': 1,
}

good_make_premium = {
    'bango': '123',
    'price': 1,
    'currencyIso': 'CAD'
}

good_update_rating = {
    'ratingScheme': 'GLOBAL',
    'rating': 'UNIVERSAL',
}

good_billing_request = {
    'pageTitle': 'wat!',
    'prices': [
        {'amount': 2, 'currency': 'CAD'},
        {'amount': 1, 'currency': 'EUR'},
    ],
    'redirect_url_onsuccess': 'https://nowhere.com/success',
    'redirect_url_onerror': 'https://nowhere.com/error',
}

good_bank_details = {
    'bankAccountPayeeName': 'Andy',
    'bankAccountNumber': 'Yes',
    'bankAccountCode': '123',
    'bankName': 'Bailouts r us',
    'bankAddress1': '123 Yonge St',
    'bankAddressZipCode': 'V1V 1V1',
    'bankAddressIso': 'BRA'
}

premium_response = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <MakePremiumPerAccessResponse
            xmlns="com.bango.webservices.mozillaexporter">
            <MakePremiumPerAccessResult>
                <responseCode>OK</responseCode>
                <responseMessage>Success</responseMessage>
            </MakePremiumPerAccessResult>
        </MakePremiumPerAccessResponse>
    </soap:Body>
</soap:Envelope>"""

premium_response_failure = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <MakePremiumPerAccessResponse
            xmlns="com.bango.webservices.mozillaexporter">
            <MakePremiumPerAccessResult>
                <responseCode>wat</responseCode>
                <responseMessage>oops</responseMessage>
            </MakePremiumPerAccessResult>
        </MakePremiumPerAccessResponse>
    </soap:Body>
</soap:Envelope>"""

package_response = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <CreatePackageResponse xmlns="com.bango.webservices.mozillaexporter">
            <CreatePackageResult>
                <responseCode>OK</responseCode>
                <responseMessage>Success</responseMessage>
                <packageId>1</packageId>
                <adminPersonId>2</adminPersonId>
                <adminPersonPassword />
                <supportPersonId>3</supportPersonId>
                <supportPersonPassword />
                <financePersonId>4</financePersonId>
                <financePersonPassword />
            </CreatePackageResult>
        </CreatePackageResponse>
    </soap:Body>
</soap:Envelope>"""

sample_request = """<SOAP-ENV:Envelope
    xmlns:ns0="com.bango.webservices.mozillaexporter"
    xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Header/>
    <ns1:Body>
        <ns0:CreatePackage>
            <ns0:request>
                <ns0:username>weee!</ns0:username>
                <ns0:password>wooo!</ns0:password>
            </ns0:request>
        </ns0:CreatePackage>
    </ns1:Body>
</SOAP-ENV:Envelope>"""

billing_request = """<?xml version="1.0" encoding="UTF-8"?>
    <SOAP-ENV:Envelope
        xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:ns1="com.bango.webservices.billingconfiguration"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Header/>
    <ns0:Body>
        <ns1:CreateBillingConfiguration>
            <ns1:request>
                <ns1:username>Mozilla</ns1:username>
                <ns1:password></ns1:password>
                <ns1:bango>1</ns1:bango>
            </ns1:request>
        </ns1:CreateBillingConfiguration>
    </ns0:Body>
</SOAP-ENV:Envelope>"""
