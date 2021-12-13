This module extends the `ir.sequence` allowing more legends. It adds the following legends:

* Current Buddhist Era (BE) year with century: `%(year_be)s`
* Current Buddhist Era (BE) year without century: `%(y_be)s`
* The begin of `date_range` Buddhist Era (BE) year with century: `%(range_year_be)s`
* The begin of `date_range` Buddhist Era (BE) year without century: `%(range_y_be)s`
* The end of `date_range` Buddhist Era (BE) year with century: `%(range_end_year_be)s`
* The end of `date_range` Buddhist Era (BE) year without century: `%(range_end_y_be)s`

This module works with `range_` and `range_end_`.

**Note**: This module does not depends on the `l10n_th_sequence_range_end`. Although, the module `l10n_th_sequence_range_end` must be manually installed in order to use `%(range_end_year_be)s` and `%(range_end_y_be)s` legends.
