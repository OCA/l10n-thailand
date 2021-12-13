This module extends the `ir.sequence` allowing more legends. It adds the following legends:

* Quarter of the Year: `%(qoy)s`
* The begin of `date_range` quarter of the Year: `%(range_qoy)s`
* The end of `date_range` quarter of the Year: `%(range_end_qoy)s`


This module works with `range_` and `range_end_`.

**Note**: This module does not depends on the `l10n_th_sequence_range_end`. Although, the module `l10n_th_sequence_range_end` must be manually installed in order to use the `%(range_end_qoy)s` legend.
