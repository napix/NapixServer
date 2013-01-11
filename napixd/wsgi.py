#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import napixd
from napixd.launcher import Setup

path = os.path.realpath( os.path.join( os.path.dirname(__file__), '..' ))
sys.path.append(path)
napixd.HOME = path

options = set( sys.argv)
options.add( 'quiet')
options.add( 'silent')
application = Setup(options).get_app()
