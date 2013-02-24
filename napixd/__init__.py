import os

HOME = ( os.environ.get('NAPIXHOME') or
        os.path.abspath( os.path.join( os.path.dirname( __file__ ), '..')))

def get_file( path, create=True):
    dirname, filename = os.path.split( path)
    path = get_path( dirname, create)
    return os.path.join( path, filename)

def get_path( dirname='', create=True):
    if not dirname:
        path= HOME
    else:
        path = os.path.abspath( os.path.join( HOME, dirname, ''))
    if not os.path.isdir( path):
        os.makedirs( path)
    return path
