Development
===========

Developing datazilla requires installing the dev-only dependencies::

    pip install -r requirements/dev.txt


Tests
-----

To run the Python tests, run ``./runtests.sh`` (your ``DATAZILLA_DATABASE_*``
settings in ``datazilla/settings/local.py`` must be configured).

This will output test coverage metrics in HTML format to the ``htmlcov/``
directory.


Dependencies
------------

To add or change a pure-Python production dependency, add or modify the
appropriate line in ``requirements/pure.txt``, then run
``bin/generate-vendor-lib.py``. You should see the actual code changes
in the dependency reflected in ``vendor/`` if you ``git diff``. Commit
both the change to ``requirements/pure.txt`` and the changes in
``vendor/``.

To add or change a non-pure-Python production dependency, simply add or
modify the appropriate line in ``requirements/compiled.txt``.

To add or change a development-only dependency, simply add or modify the
appropriate line in ``requirements/dev.txt``.
