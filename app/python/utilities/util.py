import os, time, sys
from io import StringIO
from datetime import datetime


"""
Note: Micropython epoch starts in 2000, c-python epoch in 1970.

      Add 
            config.get('app', 'epoch-offset') 
      to get c-python epoch from micropython.

"""
def timestamp() -> int:
    # TODO: handle uninitialized time!
    return time.time()

def isodatetime() -> str:
    return datetime.now().isoformat()

def makedirs(path) -> None:
    if path.endswith('/'): path = path[:-1] 
    try:
        os.mkdir(path)
    except OSError as e:
        if e.args[0]==2:
            makedirs(path[:path.rfind('/')])
            os.mkdir(path)
        elif e.args[0]==17:
            pass
        else:
            raise

def format_error(msg, exception=None):
    """Format error message with optional exception trace."""
    s = StringIO()
    s.write("***** ")
    s.write(msg)
    if exception:
        s.write('\n')
        sys.print_exception(exception, s)
    return s.getvalue()
