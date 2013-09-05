#!/usr/bin/env python
# -*- coding: utf-8 -*-


from napixd.plugins.auth import AAAPlugin
from napixd.plugins.exceptions import ExceptionsCatcher
from napixd.plugins.conversation import ConversationPlugin, UserAgentDetector
from napixd.plugins.middleware import CORSMiddleware, PathInfoMiddleware
from napixd.plugins.times import TimePlugin
