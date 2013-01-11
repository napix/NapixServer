#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import napixd

path = os.path.realpath( os.path.join( os.path.dirname(__file__), '..' ))
sys.path.append(path)
napixd.HOME = path

from napixd.launcher import Setup

options = set( sys.argv)
options.add( 'silent')

application = Setup(options).get_application()
