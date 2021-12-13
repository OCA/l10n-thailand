This module refactor the `ir.sequence` allowing more legends to be added with minimal code duplication.

Adding more legends to `ir.sequence` requires an extension of an inner method `_interpolation_dict()` of the `_get_prefix_suffix()` method. An extension of an inner method is impractical, therefore this module override the `_get_prefix_suffix()` method by moving the inner private method `_interpolation_dict()` to a private method. Therefore, this allows another module to add more legends to the `ir.sequence`.

This modules works as a base module to other modules to add more legends to `ir.sequence`.
