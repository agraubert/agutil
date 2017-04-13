import argparse
import hashlib
import sys
import os
import Crypto.Cipher.AES as AES
from getpass import getpass

try:
    from .src import files
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from agutil.security.src import files

def simple_pbkdf2_hmac(_, password, salt, iterations):
    current = hashlib.sha512(password+salt).digest()
    for _ in range(iterations):
        current = hashlib.sha512(current+salt).digest()
    return current

def main(args_input = sys.argv[1:]):
    parser = argparse.ArgumentParser("agutil-secure")
    parser.add_argument(
        'action',
        choices=['encrypt', 'decrypt'],
        help="Sets the mode to either encryption or decryption"
    )
    parser.add_argument(
        'input',
        type=argparse.FileType('rb'),
        help="Input file to encrypt or decrypt"
    )
    parser.add_argument(
        '-p', '--password',
        default=None,
        help="The password to encrypt or decrypt with.  Note: passwords containing " " (spaces) must be encapsulated with quotations (\"\")"
    )
    parser.add_argument(
        '-o','--output',
        type=argparse.FileType('wb'),
        default=None,
        help="Where to save the encrypted or decrypted file. If omitted, agutil-secure will replace the input file"
    )
    parser.add_argument(
        '--py33',
        action='store_true',
        help="Forces encryption or decryption to use the simplified, 3.3 compatable pbkdf2_hmac "
    )
    parser.add_argument(
        '-f', '--force',
        action='store_false',
        help="Attempts to decrypt the file without verifying the password. \
        Files encrypted with agutil version 1.1.3 and earlier MUST be decrypted with this option"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Display the progress of the operation"
    )
    args = parser.parse_args(args_input)
    if args.py33 or sys.version_info<(3,4):
        key_algo = simple_pbkdf2_hmac
    else:
        key_algo = hashlib.pbkdf2_hmac
    if args.password is None:
        args.password = getpass(args.action.title()+"ion password: ")
        if args.action == 'encrypt':
            check = getpass("Confirm password: ")
            if check != args.password:
                sys.exit("Passwords do not match!")
    if args.output is None:
        from tempfile import mkstemp
        (handle, output_name) = mkstemp()
        os.close(handle)
        output_file = open(output_name, mode='wb')
    else:
        output_file = args.output

    key = hashlib.sha256(key_algo('sha512', args.password.encode(), b'this is some serious salt, yo', 250000)).digest()
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    if args.verbose:
        #this is definitely a hacky solution, but it looks better from the user's perspective
        #I have no way of reporting the progress of copying the file in place,
        #But I think it looks nicer to have the bar stick at 100% while doing that operation
        #Than to just disappear and leave the user waiting at a blank line before the
        #program finishes
        from .. import status_bar
        bar = status_bar(os.path.getsize(args.input.name), show_percent=True, init=False)
        def wrapper(func):
            def call(chunk, cipher):
                call.progress += len(chunk)
                bar.update(call.progress)
                return func(chunk, cipher)
            call.progress = 0
            return call
        if args.action == 'encrypt':
            files._encrypt_chunk = wrapper(files._encrypt_chunk)
        else:
            files._decrypt_chunk = wrapper(files._decrypt_chunk)
    try:
        if args.action == 'encrypt':
            files.encryptFile(
                args.input.name,
                output_file.name,
                cipher,
                validate=args.force,
                _prechunk=True
            )
        else:
            files.decryptFile(
                args.input.name,
                output_file.name,
                cipher,
                validate=args.force,
                _prechunk=True
            )
    except KeyError:
        sys.exit("Failed!  The provided password may be incorrect")
    finally:
        args.input.close()
        output_file.close()

    if args.output is None:
        from shutil import copyfile
        copyfile(output_file.name, args.input.name)
        os.remove(output_file.name)

    if args.verbose:
        bar.clear()


if __name__ == '__main__':
    main()
