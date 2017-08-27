import sys
from .base import *
try:
    from .local import *
except ImportError:
    print("Please create a settings/local.py file with your local settings.")
    print("You can use settings/local_example.py as a template.")
    sys.exit(78)  # BSD convention: EX_CONFIG
