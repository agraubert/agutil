from ... import io
from . import securesocket

def new(address, port, initPassword=None, defaultbits=4096, verbose=False, _debug_keys=None):
    return securesocket.SecureSocket(address, port, initPassword, defaultbits, verbose, _debug_keys=_debug_keys)
