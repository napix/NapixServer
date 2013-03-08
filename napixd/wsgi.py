#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import napixd

from napixd.launcher import Setup

options = set( sys.argv)
options.add( 'silent')

application = Setup(options).get_application()
