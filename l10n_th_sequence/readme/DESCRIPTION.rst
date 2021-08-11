This module refactor the `ir.sequence` allowing more legends. Then, it add the following legends:

* Current Buddhist Era (BE) Year with Century: `%(year_be)s`
* Current Buddhist Era (BE) Year without Century: `%(y_be)s`
* Quarter of the Year: `%(qoy)s`
* Company branch number (5-digit): `%(b5)s`
* Company branch number (4-digit): `%(b4)s`
* Company branch number (3-digit): `%(b3)s`
* Company branch number (2-digit): `%(b2)s`
* Company branch number (1-digit): `%(b1)s`

**Note**: This module does not depends on the `l10n_th_partner`, although it refer to the field `branch` of `res.company`.
if the module `l10n_th_partner` is not installed (`env.company` has no `branch` field), the company branch number will be computed as "00000".

This module works with `date` and `date_range`.
