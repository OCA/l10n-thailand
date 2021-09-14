This module extends the `ir.sequence` allowing more legends. It adds the following legends:

* Company branch number (5-digit): `%(b5)s`
* Company branch number (4-digit): `%(b4)s`
* Company branch number (3-digit): `%(b3)s`
* Company branch number (2-digit): `%(b2)s`
* Company branch number (1-digit): `%(b1)s`

**Note**: This module depends on the `l10n_th_partner`. If the `branch` field is not set, the company branch number will be computed as "00000".
