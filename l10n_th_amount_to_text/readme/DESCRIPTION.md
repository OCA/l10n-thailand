Odoo's core functionality includes the `amount_to_text` function,
which converts numerical amounts into text based on the user's language settings or context.
However, this conversion may produce incorrect results for Thai.

**Example:**
- Amount: 45.75 Baht
    - User Language: **Thai** → สี่สิบห้า Baht และ เจ็ดสิบห้า Satang
    - User Language: **English** → Forty-Five Baht and Seventy-Five Satang

These results are inaccurate for Thai language formatting.
This module provides a base for accurately converting numbers to Thai text.