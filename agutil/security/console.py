import argparse
from agutil.security.src.connection import SecureConnection
from agutil.security.console_task import run_task
from agutil.security import _PROTOCOL_VERSION_
import sys

def main():
    parser = argparse.ArgumentParser("agutil-secure")
    parser.add_argument(
        'address',
        help='The address to connect to, or \'listen\' if you instead wish to listen for an incoming connection'
    )
    parser.add_argument(
        'port',
        type=int,
        help='The port to connect to, or listen on'
    )
    parser.add_argument(
        '-p', '--password',
        help="Password to set the base encryption for the connection"
    )
    parser.add_argument(
        '-r', '--rsabits',
        type=int,
        help="Length (in bits) of the rsa encryption key to generate.  Default: 4096",
        default=4096
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Sets the connection to produce verbose output'
    )
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        help='Default timeout (in seconds) for the connection.  Default: 3 seconds',
        default=3
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help="Print the protocol version and exit"
    )
    args = parser.parse_args()
    if args.version:
        print("agutil-secure version", _PROTOCOL_VERSION_)
        sys.exit(0)
    socket = SecureConnection(args.address, args.port, args.password, args.rsabits, args.verbose, args.timeout)
    print()
    intake = input("Agutil-Secure> ")
    status = run_task(socket, intake.split(' '))
    while status:
        print()
        intake = input("Agutil-Secure> ")
        status = run_task(socket, intake.split(' '))


if __name__ == '__main__':
    main()
