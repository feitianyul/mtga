import sys
from multiprocessing import freeze_support

from mtga_app import main

freeze_support()

if __name__ == "__main__":
    sys.exit(main())
