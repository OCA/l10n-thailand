The `amount_to_text` function in the `res.currency` model allows you to convert amounts into text.
Below is an example of how to use it in a QWEB report:

Example Usage:
``` xml
<t t-foreach="docs" t-as="o">
    <t t-set="currency" t-value="o.currency_id"/>
    
    <!-- Convert amount to Thai text -->
    <t t-out="currency.with_context({'lang': 'th_TH'}).amount_to_text(45.75)"/>
    
    <!-- Convert amount to text using Odoo's default behavior -->
    <t t-out="currency.amount_to_text(45.75)"/>
</t>
```

**Results Based on Context:**

- When `lang=th_TH` context is sent:
  - Currency: **THB** → `สี่สิบห้าบาทเจ็ดสิบห้าสตางค์`
  - Currency: **EUR** → `สี่สิบห้ายูโรเจ็ดสิบห้าเซนต์`
  - Currency: **USD** → `สี่สิบห้าดอลลาร์เจ็ดสิบห้าเซนต์`

- When no context is sent:
  Odoo's default logic will handle the conversion.

**Important Notes:**

Ensure the Thai language (`th_TH`) is **activated** in your system before using the `lang='th_TH'` context.

Before sending the context with `th_TH` language,
If it is not activated, combining the `th_TH` language context with non-THB currencies may result in errors.