#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import napixd  # noqa

from napixd.launcher import Setup

options = set(sys.argv)
application = Setup(options).get_application()
