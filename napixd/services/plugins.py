#!/usr/bin/env python
# -*- coding: utf-8 -*-


import functools
import itertools
import urllib


class ArgumentsPlugin(object):
    """
    Bottle only passes the arguments from the url by keyword.

    This bottle plugin get the dict provided by bottle and get it in a tuple form

    url: /plugin/:f1/:f2/:f3
    bottle args : { f1:path1, f2:path2, f3:path3 }
    after plugin: (path1,path2,path3)
    """
    name='argument'
    api = 2
    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner_arguments(*args,**kw):
            path = self._get_path(args,kw)
            path = map(urllib.unquote, path)
            return callback(path)
        return inner_arguments

    def _get_path(self,args,kw):
        if args :
            return args
        return map(lambda x:kw[x],
                #limit to keywords given in the kwargs
                itertools.takewhile(lambda x:x in kw,
                    #infinite generator of f0,f1,f2,...
                    itertools.imap(lambda x:'f%i'%x,
                        #infinite generator of 0,1,2,3...
                        itertools.count())))
