import os

from napixd.resources import SimpleCollection,action
from napixd.exceptions import NotFound,ValidationError

__all__ = ('DirectoryManager',)

class FileManager(SimpleCollection):
    fields = ['content','filename']
    def __init__(self,parent):
        self.path = parent['path']
    def _path(self,filename):
        return os.path.join(self.path,filename)

    def list(self,fitlers):
        return [path for path in os.listdir(self.path)
                if path[0] != '.' and not os.path.isdir(path)]
    def create(self,values):
        filename = values.get('filename')
        content = values.get('content','')
        path = self._path(filename)
        open(path,'w').write(content)
        return filename
    def delete(self,fname):
        os.unlink(self._path(fname))
    def child(self,fname):
        try:
            content=open(self._path(fname),'r').read()
        except IOError:
            raise NotFound,fname
        return {'content':content,'filename':fname}

    @action
    def touch(self,fname):
        os.utime(self._path(self._path(fname)))

class DirectoryManager(SimpleCollection):
    fields =['path','mode']

    files = FileManager

    def check_id(self,id_):
        """
        Check that given identifier is a absolute path
        and remove the eventual trailing slashes
        """
        id_ = id_.replace('%2F','/')
        if not id_.startswith('/'):
            raise ValidationError('absolute paths must be given')
        #remove trailing /
        while id_[-1] == '/':
            id_ = id_[:-1]
        return id_

    def list(self,filters):
        try:
            basedir = filters['basedir']
        except KeyError:
            raise KeyError('basedir')
        return [os.path.join(basedir,path) for path in os.listdir(basedir)
                if os.path.isdir(os.path.join(basedir,path))]
    def child(self,path):
        """"""
        try:
            stats=os.stat(path)
        except OSError:
            raise NotFound,path
        return {'path':path, 'name':os.path.basename(path),
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
