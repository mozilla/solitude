sub = """<?xml version="1.0" encoding="UTF-8"?>
<notification>
  <kind>{kind}</kind>
  <timestamp type="datetime">2015-06-15T18:34:41Z</timestamp>
  <subject>
    <subscription>
      <add-ons type="array"/>
      <balance>0.00</balance>
      <billing-day-of-month type="integer">{now.day}</billing-day-of-month>
      <billing-period-end-date type="date">{next:%Y-%m-%d}</billing-period-end-date>
      <billing-period-start-date type="date">{now:%Y-%m-%d}</billing-period-start-date>
      <created-at type="datetime">{timestamp}</created-at>
      <updated-at type="datetime">{timestamp}</updated-at>
      <current-billing-cycle type="integer">1</current-billing-cycle>
      <days-past-due nil="true"/>
      <discounts type="array"/>
      <failure-count type="integer">0</failure-count>
      <first-billing-date type="date">{now:%Y-%m-%d}</first-billing-date>
      <id>{sub.provider_id}</id>
      <merchant-account-id>{merchant_account_id}</merchant-account-id>
      <never-expires type="boolean">true</never-expires>
      <next-bill-amount>{product.amount}</next-bill-amount>
      <next-billing-period-amount>{product.amount}</next-billing-period-amount>
      <next-billing-date type="date">{next:%Y-%m-%d}</next-billing-date>
      <number-of-billing-cycles nil="true"/>
      <paid-through-date type="date">{paid:%Y-%m-%d}</paid-through-date>
      <payment-method-token>7js9mb</payment-method-token>
      <plan-id>{plan_id}</plan-id>
      <price>{product.amount}</price>
      <status>Active</status>
      <trial-duration nil="true"/>
      <trial-duration-unit>day</trial-duration-unit>
      <trial-period type="boolean">false</trial-period>
      <descriptor>
        <name>Mozilla*product</name>
        <phone nil="true"/>
        <url>mozilla.org</url>
      </descriptor>
      <transactions type="array">
        <transaction>
          <id>{transaction[id]}</id>
          <status>{transaction[status]}</status>
          <type>sale</type>
          <currency-iso-code>{product.currency}</currency-iso-code>
          <amount>{product.amount}</amount>
          <merchant-account-id>{merchant_account_id}</merchant-account-id>
          <order-id nil="true"/>
          <created-at type="datetime">{timestamp}</created-at>
          <updated-at type="datetime">{timestamp}</updated-at>
          <customer>
            <id>86199926</id>
            <first-name nil="true"/>
            <last-name nil="true"/>
            <company nil="true"/>
            <email nil="true"/>
            <website nil="true"/>
            <phone nil="true"/>
            <fax nil="true"/>
          </customer>
          <billing>
            <id nil="true"/>
            <first-name nil="true"/>
            <last-name nil="true"/>
            <company nil="true"/>
            <street-address nil="true"/>
            <extended-address nil="true"/>
            <locality nil="true"/>
            <region nil="true"/>
            <postal-code nil="true"/>
            <country-name nil="true"/>
            <country-code-alpha2 nil="true"/>
            <country-code-alpha3 nil="true"/>
            <country-code-numeric nil="true"/>
          </billing>
          <refund-id nil="true"/>
          <refund-ids type="array"/>
          <refunded-transaction-id nil="true"/>
          <settlement-batch-id nil="true"/>
          <shipping>
            <id nil="true"/>
            <first-name nil="true"/>
            <last-name nil="true"/>
            <company nil="true"/>
            <street-address nil="true"/>
            <extended-address nil="true"/>
            <locality nil="true"/>
            <region nil="true"/>
            <postal-code nil="true"/>
            <country-name nil="true"/>
            <country-code-alpha2 nil="true"/>
            <country-code-alpha3 nil="true"/>
            <country-code-numeric nil="true"/>
          </shipping>
          <custom-fields/>
          <avs-error-response-code nil="true"/>
          <avs-postal-code-response-code>I</avs-postal-code-response-code>
          <avs-street-address-response-code>I</avs-street-address-response-code>
          <cvv-response-code>I</cvv-response-code>
          <gateway-rejection-reason nil="true"/>
          <processor-authorization-code>KQPBDL</processor-authorization-code>
          <processor-response-code>{processor-response[code]}</processor-response-code>
          <processor-response-text>{processor-response[text]}</processor-response-text>
          <additional-processor-response nil="true"/>
          <voice-referral-number nil="true"/>
          <purchase-order-number nil="true"/>
          <tax-amount nil="true"/>
          <tax-exempt type="boolean">false</tax-exempt>
          <credit-card>
            <token>7js9mb</token>
            <bin>411111</bin>
            <last-4>1111</last-4>
            <card-type>Visa</card-type>
            <expiration-month>12</expiration-month>
            <expiration-year>2015</expiration-year>
            <customer-location>US</customer-location>
            <cardholder-name nil="true"/>
            <image-url>https://assets.braintreegateway.com/payment_method_logo/visa.png?environment=sandbox</image-url>
            <unique-number-identifier>21ee4272998b10107aeee9d50d6fe1ae</unique-number-identifier>
            <prepaid>Unknown</prepaid>
            <healthcare>Unknown</healthcare>
            <debit>Unknown</debit>
            <durbin-regulated>Unknown</durbin-regulated>
            <commercial>Unknown</commercial>
            <payroll>Unknown</payroll>
            <issuing-bank>Unknown</issuing-bank>
            <country-of-issuance>Unknown</country-of-issuance>
            <product-id>Unknown</product-id>
            <venmo-sdk type="boolean">false</venmo-sdk>
          </credit-card>
          <status-history type="array">
            <status-event>
              <timestamp type="datetime">{timestamp}</timestamp>
              <status>authorized</status>
              <amount>{product.amount}</amount>
              <user>andymckay</user>
              <transaction-source>recurring</transaction-source>
            </status-event>
            <status-event>
              <timestamp type="datetime">{timestamp}</timestamp>
              <status>submitted_for_settlement</status>
              <amount>{product.amount}</amount>
              <user>andymckay</user>
              <transaction-source>recurring</transaction-source>
            </status-event>
          </status-history>
          <plan-id>{plan_id}</plan-id>
          <subscription-id>fpps4w</subscription-id>
          <subscription>
            <billing-period-end-date type="date">2015-07-14</billing-period-end-date>
            <billing-period-start-date type="date">2015-06-15</billing-period-start-date>
          </subscription>
          <add-ons type="array"/>
          <discounts type="array"/>
          <descriptor>
            <name>Mozilla*product</name>
            <phone nil="true"/>
            <url>mozilla.org</url>
          </descriptor>
          <recurring type="boolean">true</recurring>
          <channel nil="true"/>
          <service-fee-amount nil="true"/>
          <escrow-status nil="true"/>
          <disbursement-details>
            <disbursement-date nil="true"/>
            <settlement-amount nil="true"/>
            <settlement-currency-iso-code nil="true"/>
            <settlement-currency-exchange-rate nil="true"/>
            <funds-held nil="true"/>
            <success nil="true"/>
          </disbursement-details>
          <disputes type="array"/>
          <payment-instrument-type>credit_card</payment-instrument-type>
          <processor-settlement-response-code></processor-settlement-response-code>
          <processor-settlement-response-text></processor-settlement-response-text>
          <risk-data>
            <id>3CSZ08CD2ZY4</id>
            <decision>Approve</decision>
          </risk-data>
          <three-d-secure-info nil="true"/>
        </transaction>
      </transactions>
      <status-history type="array">
        <status-event>
          <timestamp type="datetime">{timestamp}</timestamp>
          <status>Active</status>
          <user>andymckay</user>
          <subscription-source>api</subscription-source>
          <balance>0.00</balance>
          <price>{product.amount}</price>
        </status-event>
      </status-history>
    </subscription>
  </subject>
</notification>
"""  # noqa
