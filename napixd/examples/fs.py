from base import Collection

class Sample(Collection):
    child_fields = []
    fields =[]

    def __init__(child,that):
        child.parent = that

    def list_children(self):
        #GET /that/child/
        pass

    def create_child(self,values):
        #GET /that/child/
        pass

    def delete_child(self,):
        #DELETE /that/child
        pass

    def get_child(self,id):
        #GET /that/child
        pass

    def modify_child(self,id,values):
        #PUT /that/child
        pass

    @classmethod
    def list(cls):
        #GET /that/
        pass

    @classmethod
    def get(cls,id):
        #GET /that
        pass

    @classmethod
    def create(self,values):
        #POST /that/
        pass

    @classmethod
    def delete(self,id):
        #DELETE /that/
        pass

    @classmethod
    def modify(self,id,values):
        #PUT /that/
        pass
