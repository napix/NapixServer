#!/usr/bin/env python
# -*- coding: utf-8 -*-

import operator
import os
import subprocess
import logging
import json

from pwd import getpwall,getpwuid

from piston.utils import rc,translate_mime,coerce_put_post
from piston import emitters

from django.conf.urls.defaults import url
from django.core.exceptions import ValidationError
from django.http import HttpResponse

logger = logging.getLogger('napix')

class HTTPException(Exception):
    status = 200
class HTTP400(HTTPException):
    status = 400
class HTTP404(HTTPException):
    status = 404
class HTTP405(HTTPException):
    status = 405
class HTTP500(HTTPException):
    status = 500

def ValidateIf(fn):
    def inner(self,r_id):
        if not fn(self,r_id):
            raise ValidationError,''
        return r_id
    return inner

def run_command(command):
    logger.info('Running '+' '.join(command))
    shell = subprocess.Popen(command,stderr=open('/dev/null'),stdout=open('/dev/null'))
    return shell.wait()

def run_command_or_fail(command):
    code = run_command(command)
    if code != 0:
        raise HTTP500,'Oops command returned '+code

class Service(object):
    def __init__(self,handler):
        self.handler = handler()

    def find_resource(self,rid):
        if rid is None :
            raise HTTP400,'Resource identifier required'
        try:
            resource_id = self.handler.validate_resource_id(rid)
        except ValidationError:
            raise HTTP400,'Invalid resource identifier'
        resource = self.handler.find(resource_id)
        if resource == None:
            raise HTTP404
        return resource

    def filter_values(self,data):
        values = {}
        for f in self.handler.fields :
            try:
                values[f] =data[f]
            except KeyError:
                pass
        if not values:
            return None
        return values

    def view(self,request,rid=None):
        try:
            resp = self.actually_do_stuff(request,rid)
        except HTTPException,e:
            return HttpResponse(str(e),status=e.status)
        return HttpResponse(json.dumps(resp),mimetype='application/json')

    def actually_do_stuff(self,request,rid=None):
        meth = request.method.upper()
        if not meth in self.handler.allowed_methods:
            raise HTTP405
        if rid :
            res = self.find_resource(rid)
        if meth in ('POST','PUT'):
            if meth == 'PUT':
                coerce_put_post(request)
            translate_mime(request)
            values = self.filter_values(request.data)
        if meth in ('PUT','DELETE'):
            if not res:
                return HTTP400,'Resource required'
        logger.info('request %s %s',meth,rid)
        if meth == 'GET':
            if rid:
                return res
            else:
                return self.handler.find_all()
        elif meth == 'POST':
            return self.handler.create(values)
        elif meth == 'PUT':
            return self.handler.modify(res,values)
        elif meth == 'DELETE':
            return self.handler.delete(self,values)

class NAPIXHandler(object):
    _registry = {}
    @classmethod
    def register(selfcls,url):
        def inner(cls):
            selfcls._registry[url] = cls
            return cls
        return inner

    @classmethod
    def get_urls(cls):
        r=[]
        for url_prefix,handler in cls._registry.items():
            handler = Service(handler)
            r.append(url('^%s/$'%url_prefix,handler.view))
            r.append(url('^%s/(?P<rid>.+)/$'%url_prefix,handler.view))
        return r

class BaseHandler(object):
    allowed_methods = ('GET',)
    fields = []

    def validate_resource_id(self,r_id):
        return r_id
    def find(self,rid):
        raise NotImplementedError
    def find_all(self):
        raise NotImplementedError
    def add(self,values):
        raise NotImplementedError
    def modify(self,resource,values):
        raise NotImplementedError
    def delete(self,resource):
        raise NotImplementedError

@NAPIXHandler.register('napix')
class NAPIXAPIHandler(BaseHandler):
    """ API de gestion des API """

    allowed_methods = ('GET',)
    fields =  ('doc','resource_id','methods','fields')

    def validate_resource_id(self,r_id):
        """ Prefixe de l'url """
        return r_id

    def find(self,resource_id):
        try:
            api= NAPIXHandler._registry[resource_id]
        except KeyError:
            return None
        return {
                'doc':api.__doc__,
                'resource_id':api.validate_resource_id.__doc__,
                'methods':api.allowed_methods,
                'fields':api.fields
                }

    def find_all(self):
        return NAPIXHandler._registry.keys()

@NAPIXHandler.register('unixaccounts')
class UnixAccountHandler(BaseHandler):
    """Gestionnaire des comptes UNIX """
    fields = ('name','gid','gecos','dir','shell',)
    allowed_methods = ('GET','PUT','POST','DELETE')
    table_pwd = { 'name' : 'login', 'gid': 'gid', 'gecos':'comment' ,'shell':'shell','dir':'home'}

    def validate_resource_id(self,r_id):
        """ UID de l'utilisateur"""
        try:
            return int(r_id)
        except ValueError:
            raise ValidationError,''

    def find(self,uid):
        try:
            x= getpwuid(uid)
        except KeyError:
            return None
        y = {}
        for i in self.fields:
            y[i] = getattr(x,'pw_'+i)
        return y

    def find_all(self):
        return map(operator.attrgetter('pw_uid'),getpwall())

    def add(self,values):
        command = ['/usr/sbin/useradd']
        try:
            login = values.pop('name')
        except KeyError:
            raise HTTP400,'<name> parameter required'
        for f,x in values.items():
            command.append('--'+self.table_pwd[f])
            command.append(x)
        command.append(login)
        code =  run_command(command)
        if code == 0:
            return rc.CREATED
        if code == 9:
            return rc.DUPLICATE_ENTRY
        return HTTP500

    def modify(self,resource,values):
        command = ['/usr/sbin/usermod']
        for f,x in values.items() :
            command.append('--'+self.table_pwd[f])
            command.append(x)
        command.append(resource['name'])
        run_command_or_fail(command)
        return rc.ALL_OK

    def remove(self,resource):
        run_command_or_fail(['/usr/sbin/userdel',resource['name']])
        return rc.DELETED

@NAPIXHandler.register('initd')
class InitdHandler(BaseHandler):
    """ Gestionnaire des scripts init.d """

    path = '/etc/init.d'
    fields = ('state',)
    allowed_methods = ('GET','PUT')

    def modify(self,resource,values):
        if 'state' not in values:
            return HTTP400('<state> parameter required')
        status = values['state'] == 'off' and 'stop' or 'start'
        run_command_or_fail([resource,status])
        return rc.ALL_OK

    @ValidateIf
    def validate_resource_id(self,name):
        """ nom du daemon """
        return not '/' in name

    def find_all(self):
        return os.listdir(self.path)

    def find(self,name):
        path =  os.path.join(self.path,name)
        if not os.path.isfile(os.path.join(self.path,name)):
            return None
        running = (run_command([path,'status']) == 0)
        return {'state': running and 'on' or 'off'}

