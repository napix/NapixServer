from base import Collection

class Sample(Collection):
    child_fields = []
    fields =[]

    def __init__(self,path):
        self.path = path

    def list_children(self):
        #GET /that/child/
        pass

    def create_child(self,values):
        #GET /that/child/
        pass

    def delete_child(self,fname):
        #DELETE /that/child
        pass

    def get_child(self,fname):
        #GET /that/child
        pass

    @classmethod
    def list(cls):
        #GET /that/
        pass

    @classmethod
    def get(cls,path):
        #GET /that
        pass

    @classmethod
    def create(self,values):
        #POST /that/
        pass

    @classmethod
    def delete(self,rep):
        #DELETE /that/
        pass
