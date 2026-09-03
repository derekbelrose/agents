"""Allow the package to run with ``python -m web_search``."""

from web_search.cli import main

raise SystemExit(main())
