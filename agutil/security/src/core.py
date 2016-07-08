import ..io
import .channel

def new(address, port, password=None):
    if address == 'listen' or address == '':
        #listen for connections
        ss = io.SocketServer(port, queue=0)
        # s = channel.SecureSocket(io.QueuedSocket(ss.accept()), False, password)
        s = channel.SecureSocket(ss.accept(), False, password)
        ss.close()
        return s
    # return channel.SecureSocket(io.QueuedSocket(io.Socket(address, port)), True, password)
    return channel.SecureSocket(io.Socket(address, port), True, password)
