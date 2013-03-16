import os

HOME = ''

def find_home( name, file):
    global HOME
    env = os.environ.get('NAPIXHOME')
    if env:
        HOME=env
        return HOME

    package_dir = os.path.dirname( file)
    site_package = os.path.realpath( os.path.join( os.path.dirname( __file__), '..'))

    if 'site-packages' in package_dir:
        #installed in a VENV
        HOME = os.path.join( os.path.expanduser('~'), '.' + name)
    else:
        HOME = site_package
    return HOME

find_home( 'napixd', __file__)

def get_file( path, create=True):
    dirname, filename = os.path.split( path)
    path = get_path( dirname, create)
    return os.path.join( path, filename)

def get_path( dirname='', create=True):
    if not dirname:
        path= HOME
    else:
        path = os.path.abspath( os.path.join( HOME, dirname, ''))
    if create and not os.path.isdir( path):
        os.makedirs( path)
    return path
