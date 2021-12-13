This module extends the `ir.sequence` adding `preview` fields on both `ir.sequence` and `ir.sequence.date_range` models.
the `preview` field is a computed fields that only visible in edit-mode of the form view. It helps users to check and validate the prefix, suffix, and padding configuration easily without a need to actually generate an actual document.

This module works with `range_` and `range_end_`.
