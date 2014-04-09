empty = \
    """<?xml version='1.0' encoding='UTF-8' ?>
    <billing-request>
    </billing-request>"""

billing_request = \
    """<?xml version='1.0' encoding='UTF-8' ?>
    <billing-request>
      <result-code>{result_code}</result-code>
      <result-msg>{result_message}</result-msg>
    </billing-request>"""

pricing_request = \
    """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <pricing>
      <timestamp string="2014-04-08 15:58:25">1396972705026</timestamp>
      <action>price</action>
      <result-code>0</result-code>
      <result-msg>Operation Successful</result-msg>
      <reference-currency>USD</reference-currency>
      <pricing
        country="CA"
        amount="1500"
        currency="CDN"
        currency-symbol="$"
        currency-symbol-orientation="l"
        currency-decimal-places="2"
        price-inc-salestax="1500"
        price-ex-salestax="1293"
        receivable-gross="465"
        receivable-net="419"
        exchange="13.01193"
        reference-amount="115"
        reference-price-inc-salestax="115"
        reference-price-ex-salestax="99"
        reference-receivable-gross="36"
        reference-receivable-net="32"
        number-billed-messages="1"
        status="1" display-price="$15.00"
      />
    </pricing>"""

prepare_request = \
    """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <prepare-request>
      <action>prepare</action>
      <trx-id>{transaction_id}</trx-id>
      <result-code>0</result-code>
      <result-msg>Operation Successful</result-msg>
      <button-markup>example_markup</button-markup>
      <buy-url>http://example_buy_url/</buy-url>
    </prepare-request>"""

transaction_request = \
    """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <billing-request>
      <action>verify-trx-id</action>
      <trx-id>{transaction_id}</trx-id>
      <result-code>0</result-code>
      <result-msg>Operation Successful</result-msg>
      <amount>100</amount>
      <paid>100</paid>
    </billing-request>"""
