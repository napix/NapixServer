#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser,NoSectionError

from napixd.configfiles import ConfigFile,ConfigFileSection


class HgrcSection(ConfigFileSection):
    fields = ['section','options']

    def __init__(self,parent):
        self.hgrc=parent['parser']
        self.filename = parent['filename']

    def get(self):
        return { 'filename':self.filename }

    def list(self):
        return self.hgrc.sections()

    def child(self,name):
        try:
            return {'options':self.hgrc.items(name),'section':name}
        except NoSectionError:
            return None

    def create(self,values):
        section = values['section']
        options = values['options']
        self.hgrc.add_section(section)
        for k,v in options:
            self.hgrc.set(section,k,v)
        self._save()
        return section

    def delete(self,name):
        self.remove_section(name)
        self.hgrc.write()

    def _save(self):
        self.hgrc.write()

class HgrcFile(ConfigFile):
    fields = ['filename']
    resource_class = HgrcSection

    def child(self,filename):
        parser = ConfigParser()
        parser.readfp(open(filename))
        return {'filename':filename,'parser':parser}



