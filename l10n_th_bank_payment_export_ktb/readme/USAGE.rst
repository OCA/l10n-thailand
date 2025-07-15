You can use this module to export a bank payment file in the format required by KTB. There are two main ways to initiate the export:

* Create from a Vendor Payment
    #. Go to menu *Invoicing > Vendors > Payments*.
    #. Select payment > Action > Create Bank Payment Export

* Create from the Export Menu
    #. Go to menu *Invoicing > Accounting > Bank Payment Export*.
    #. Create > select payment or Click *Get All Payments* when you need all payment to export

Then you can do following:

#. Select Bank *KTB*
#. Fill in required fields under the Information Export tab manually, or choose a pre-configured Template to auto-fill values.
#. Click `Confirm` to validate the document.
#. Click `Export Excel` to preview the information in .xlsx format.
#. Click `Export Text File` to generate and download the `.txt` file. The document's state will change to Done.
#. If a payment fails (after sending a text file to the bank), you can reject each line and generate a new document by clicking 'reject' on each line.

Notes:

* Export Excel: To review information (.xlsx)
* Export Text File: To create a text file and send it to the bank (.txt)
* You must enable "Show Full Accounting Features" in user settings to access Bank Payment Export.
* Only `Account Managers` can confirm and export documents.
* You can `Cancel` an export document before it is submitted to the bank (different from Reject, which occurs post-submission).
