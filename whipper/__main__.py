# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import sys

from whipper.command.main import main


if __name__ == '__main__':
    # Make accuraterip_checksum be found automatically if it was built
    local_arb = os.path.join(os.path.dirname(__file__), '..', 'src')
    os.environ['PATH'] = ':'.join([os.getenv('PATH'), local_arb])
    sys.exit(main())
