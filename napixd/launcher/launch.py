#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The launcher defines the infrastructure to prepare and run the Napix Server.

:class:`Setup` is intended to be overidden to customize running
as an integrated component or in a specialized server.
"""

import sys
import optparse
import logging

from napixd.launcher.setup import Setup, CannotLaunch
from napixd.launcher.setup_class import get_setup_class


console = logging.getLogger('Napix.console')


def launch(options, setup_class=None):
    """
    Helper function to run Napix.

    It creates a **setup_class** (by default :class:`Setup` instance with the given **options**.

    **options** is an iterable.

    The exceptions are caught and logged.
    The function will block until the server is killed.
    """

    parser = optparse.OptionParser(usage=Setup.HELP_TEXT)
    parser.add_option('-p', '--port',
                      help='The TCP port to listen to',
                      type='int',
                      )
    parser.add_option('-s', '--setup-class',
                      help='The setup class used to start the Napix server',
                      )
    keys, options = parser.parse_args(options)

    sys.stdin.close()

    try:
        setup_class = setup_class or keys.setup_class and get_setup_class(keys.setup_class) or Setup
    except CannotLaunch as e:
        sys.stderr.write('{0}\n'.format(e))
        sys.exit(2)
        return

    try:
        setup = setup_class(options, port=keys.port)
    except CannotLaunch as e:
        console.critical(e)
        sys.exit(1)
        return
    except Exception as e:
        if not logging.getLogger('Napix').handlers:
            sys.stderr.write('Napix failed before the loggers went up\n')
            import traceback
            traceback.print_exc()
        else:
            console.exception(e)
            console.critical(e)
        sys.exit(-1)
        return

    try:
        setup.run()
    except (KeyboardInterrupt, SystemExit) as e:
        console.warning('Got %s, exiting', e.__class__.__name__)
        return
    except Exception, e:
        if 'print_exc' in setup.options:
            console.exception(e)
        console.critical(e)
        sys.exit(3)
