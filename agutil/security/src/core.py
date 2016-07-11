from ... import io
from . import channel

def new(address, port, password=None, defaultbits=4096, verbose=False):
    if address == 'listen' or address == '':
        #listen for connections
        if verbose:
            print("Awaiting an incoming connection...")
        ss = io.SocketServer(port, queue=0)
        s = channel.SecureSocket(ss.accept(), False, password, defaultbits, verbose)
        ss.close()
        return s
    return channel.SecureSocket(io.Socket(address, port), True, password, defaultbits, verbose)
