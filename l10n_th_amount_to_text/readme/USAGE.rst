Call function amount_to_text in model currency (res.currency).

For example if you need to convert amount to text in the QWEB your report,
add this code to your report::

    <t t-foreach="docs" t-as="o">
        <t t-set="currency" t-value="o.currency_id"/>
        # Convert to Thai Text
        <t t-esc="currency.with_context({'lang': 'th_TH'}).amount_to_text(45.75)"/>

        # Convert to Text, By core odoo
        <t t-esc="currency.amount_to_text(45.75)"/>
    </t>

If you send context lang th_TH

* Currency is THB, result is ``สี่สิบห้าบาทเจ็ดสิบห้าสตางค์``
* Currency is EUR, result is ``สี่สิบห้ายูโรเจ็ดสิบห้าเซนต์``
* Currency is USD, result is ``สี่สิบห้าดอลลาร์เจ็ดสิบห้าเซนต์``

if not send context, result will call core odoo
