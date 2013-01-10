#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from napixd.launcher import Setup

options = set( sys.argv)
options.add( 'quiet')
options.add( 'silent')
application = Setup(options).get_app()
