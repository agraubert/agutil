import argparse

_CONFIG = {
    'retries': 1,
    'timeout': .1
}

def run_task(socket, args_input):
    parser = argparse.ArgumentParser("Agutil-Secure")
    subparsers = parser.add_subparsers()

    send_msg = subparsers.add_parser(
        'send',
        help="Encrypt a message using RSA and send"
    )
    send_msg.add_argument(
        "message",
        nargs='+',
        help="The message to send"
    )
    send_msg.set_defaults(func=lambda args:socket.send(
        " ".join(args.message),
        _CONFIG['retries']
    ), kill=False)

    read_msg = subparsers.add_parser(
        'read',
        help="Read a message encrypted with RSA"
    )
    read_msg.set_defaults(func=lambda args:socket.read(
        True,
        _CONFIG['timeout']
    ), kill=False)

    disconnect = subparsers.add_parser(
        'disconnect',
        aliases=['close', 'exit', 'quit'],
        help="Close the connection and quit"
    )
    disconnect.set_defaults(func=lambda args:socket.close(), kill=True)
    print([i for i in args_input])
    args = parser.parse_args(args_input)
    args.func(args)
    if args.kill:
        return -1
    else:
        return 0
