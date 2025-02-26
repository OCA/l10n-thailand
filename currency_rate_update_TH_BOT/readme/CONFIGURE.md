To enable scheduled currency rates update:

1. Go to **Invoicing > Configuration > Settings**
2. Ensure **Automatic Currency Rates (OCA)** is checked

To configure currency rates providers:

1. Go to **Invoicing > Configuration > Currency Rates Providers**
2. Create and configure one or more providers

To configure bot.or.th currency rates provider credentials

Follow the steps below to obtain the API token from **BOT** (bot.or.th) and configure it in Odoo:

1. **Login / Sign Up**  
   Visit the following URL to log in or sign up for a new account:  
   [BOT API Login / Sign Up](https://apiportal.bot.or.th/bot/public/user/login)

2. **Access API Products**  
   After logging in, go to **API Products**. Select **Exchange Rates (2.0.1)** from the available products.  
   Alternatively, you can access the Exchange Rates product directly via this link:  
   [Exchange Rates API Product](https://apiportal.bot.or.th/bot/public/node/504)

3. **Subscribe to the Exchange Rates API**  
   Click on **Subscribe** to start the subscription process. Follow the on-screen instructions until you receive your API token.

4. **Copy the API Token**  
   Once the subscription is complete, you will be provided with an API token. **Copy the token** to use in the next step.

5. **Configure Odoo with the BOT Token**  
   - In Odoo, Go to *Invoicing > Configuration > Settings*
   - Find the **BOT Provider** section under the **Currencies** settings.
   - Paste the copied API token into the **Client ID** field.

6. **Save the Settings**  
   After pasting the token, save the changes in Odoo. Your system will now be connected to the BOT API for currency rate updates.
