def _do_nothing(*args, **kwargs):
    print("doing nothing")
    return 

def _disable_signals(server):
    
    if hasattr(server, "server"):
        server = server.server
    if hasattr(server, "install_signal_handlers"):
        print("Disabling", server.install_signal_handlers)
        server.install_signal_handlers = _do_nothing