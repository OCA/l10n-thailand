This module adds branch management to `res.company` and `res.partner`.

It also enhances name computation for `res.users` and `res.partner` based on the entity type:

- Individual: Computes the name using Title, First Name, and Last Name.
- Company: Computes the name based on the Legal Form.