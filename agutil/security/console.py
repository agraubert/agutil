import argparse
import hashlib
import sys
import os
import Cryptodome.Cipher.AES as AES
from getpass import getpass
from itertools import chain
from contextlib import ExitStack
from functools import wraps
from .src.cipher import EncryptionCipher, DecryptionCipher, configure_cipher
from .. import __version__ as version

try:
    from .src import files
except ImportError:
    sys.path.append(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(
                            __file__
                        )
                    )
                )
            )
        )
    )
    from agutil.security.src import files


def simple_pbkdf2_hmac(_, password, salt, iterations):
    current = hashlib.sha512(password+salt).digest()
    for _ in range(iterations):
        current = hashlib.sha512(current+salt).digest()
    return current


def main(args_input=sys.argv[1:]):
    from pkg_resources import get_distribution
    parser = argparse.ArgumentParser("agutil-secure")
    parser.add_argument(
        '--version',
        action='version',
        version="%(prog)s (agutil) verion "+version,
        help="Display the current version and exit"
    )
    parser.add_argument(
        'action',
        choices=['encrypt', 'decrypt'],
        help="Sets the mode to either encryption or decryption"
    )
    parser.add_argument(
        'input',
        type=argparse.FileType('rb'),
        nargs='+',
        help="Input file(s) to encrypt or decrypt"
    )
    parser.add_argument(
        '-p', '--password',
        default=None,
        help="The password to encrypt or decrypt with.  Note: passwords "
        "containing " " (spaces) must be encapsulated with quotations (\"\")"
    )
    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('wb'),
        action='append',
        default=[],
        help="Where to save the encrypted or decrypted file(s). "
        "If omitted, agutil-secure will replace the input file(s). "
        "If any output files are provided, you must provide the same number "
        "of outputs as inputs, by providing the -o argument multiple times"
    )
    parser.add_argument(
        '--py33',
        action='store_true',
        help="Forces encryption or decryption to use the simplified, "
        "3.3 compatable pbkdf2_hmac "
    )
    parser.add_argument(
        '-l', '--legacy',
        action='store_true',
        help="Enables compatability with agutil version 1.1.3 and earlier. "
        "Encrypting in this mode will produce output which can be decrypted "
        "by agutil 1.1.3 and earlier without additonal options and by agutil "
        "3.1.2 and earlier with the '-f' option. "
        "Decrypting in this mode is compatable only with files encrypted under"
        " the conditions described above."
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Display the progress of the operation"
    )
    args = parser.parse_args(args_input)
    if args.py33 or sys.version_info < (3, 4):
        key_algo = simple_pbkdf2_hmac
    else:
        key_algo = hashlib.pbkdf2_hmac
    if args.password is None:
        args.password = getpass(args.action.title()+"ion password: ")
        if args.action == 'encrypt':
            check = getpass("Confirm password: ")
            if check != args.password:
                sys.exit("Passwords do not match!")
    if len(args.output) > 0 and len(args.output) != len(args.input):
        sys.exit(
            "Must specify the same number of input files as outputs "
            "if explicitly providing output files"
        )
    files.EncryptionCipher.encrypt.__wrapped__ = files.EncryptionCipher.encrypt
    files.DecryptionCipher.decrypt.__wrapped__ = files.DecryptionCipher.decrypt
    with ExitStack() as exitStack:
        for (input_file, output_arg) in zip(
            args.input, chain(args.output, [None]*len(args.input))
        ):
            if output_arg is None:
                from tempfile import mkstemp
                (handle, output_name) = mkstemp()
                os.close(handle)
                output_file = open(output_name, mode='wb')
            else:
                output_file = output_arg
            exitStack.enter_context(input_file)
            exitStack.enter_context(output_file)
            key = hashlib.sha256(key_algo(
                'sha512',
                args.password.encode(),
                b'this is some serious salt, yo',
                250000
            )).digest()
            nonce = key[-16:]
            iv = os.urandom(16)
            legacy_cipher = AES.new(key, AES.MODE_CBC, iv=iv)
            modern_cipher = AES.new(
                hashlib.md5(key).digest(),
                mode=AES.MODE_EAX,
                nonce=nonce
            )
            if args.verbose:
                # this is definitely a hacky solution, but it looks better from
                # the user's perspective.  I have no way of reporting the
                # progress of copying the file in place, but I think it looks
                # nicer to have the bar stick at 100% while doing that
                # operation than to just disappear and leave the user waiting
                # at a blank line before the program finishes
                from .. import status_bar
                bar = status_bar(
                    os.path.getsize(input_file.name),
                    show_percent=True,
                    init=False
                )

                def wrapper(func):
                    @wraps(func)
                    def call(cipher, chunk):
                        call.progress += len(chunk)
                        bar.update(call.progress)
                        return func(cipher, chunk)
                    call.progress = 0
                    return call
                if args.action == 'encrypt':
                    files.EncryptionCipher.encrypt = wrapper(
                        files.EncryptionCipher.encrypt.__wrapped__
                    )
                else:
                    files.DecryptionCipher.decrypt = wrapper(
                        files.DecryptionCipher.decrypt.__wrapped__
                    )
            try:
                if args.action == 'encrypt':
                    files.encryptFile(
                        input_file.name,
                        output_file.name,
                        key,
                        enable_compatability=args.legacy
                    )
                else:
                    files.decryptFile(
                        input_file.name,
                        output_file.name,
                        key,
                        compatability=args.legacy
                    )
            except ValueError:
                if args.verbose:
                    bar.clear()
                sys.exit(
                    "Failed! The password may be incorrect or the file may be "
                    "corrupt"
                )

            if output_arg is None:
                from shutil import copyfile
                copyfile(output_file.name, input_file.name)
                os.remove(output_file.name)

            if args.verbose:
                bar.clear()


if __name__ == '__main__':
    main()
