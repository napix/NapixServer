import os
from bottle import HTTPError

from napixd.collections import  SimpleCollection,SubResource

class File(SimpleCollection):
    fields = ['content','filename']
    def __init__(self,parent):
        self.parent = parent
    def _path(self,filename):
        os.path.join(self.parent['path'],filename)

    def create(self,values):
        filename = values.get('filename')
        content = values.get('content','')
        path = self._path(filename)
        open(path,'w').write(content)
    def delete(self,fname):
        os.unlink(self._path(fname))
    def child(self,fname):
        try:
            content=open(self._path(fname),'r').read()
        except IOError:
            raise HTTPError,404
        return {'content':content,'filename':fname}

class Directory(SimpleCollection):
    fields =['path','mode']

    files = SubResource(File)

    def __init__(self,root):
        if root[0] != '/':
            raise ValueError,'Root must be an absolute path name'
        self.root=root

    def check_id(self,id):
        """
        Check that given identifier is a absolute path
        and remove the eventual trailing slashes
        """
        if not id.startswith(self.root):
            raise HTTPError(400,'Only children of %s are accessible'%self.root)
        #remove trailing /
        while id[-1] == '/':
            id = id[:-1]
        return id

    def find_all(self,filters):
        try:
            basedir = filters['basedir']
        except ValueError:
            raise HTTPError(400,'This method require a "basedir" filter')
        return [path for path in os.listdir(basedir)
                if os.path.isdir(os.path.join(basedir,path))]
    def child(self,path):
        """"""
        try:
            stats=os.stat(path)
        except OSError:
            raise HTTPError,404
        return {'path':os.path.basename(path),
                'mode':('%o'%stats.st_mode)[-4:]}

    def create(self,values):
        """Create a directory at given path with given mode"""
        mode = values.get('mode','755')
        #set in base 8
        mode = int(mode,8)
        path = values['path']
        os.mkdir(path,mode)
        return path

    def delete(self,rep):
        """ delete the directory at the path *rep*"""
        os.rmdir(rep)
