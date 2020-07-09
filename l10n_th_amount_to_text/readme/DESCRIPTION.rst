Normally, Core odoo has function ``amount_to_text`` and
return text language from context or user setting

Example : 45.75 Baht

* User Language 'Thai' -> สี่สิบห้า Baht และ เจ็ดสิบห้า Satang
* User Language 'English' -> Forty-Five Baht and Seventy-Five Satang

Which is incorrect when converted into thai.

This module provides base for convert number to text thai.
