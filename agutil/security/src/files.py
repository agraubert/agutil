from . import protocols
from os import urandom
import hashlib
import sys
import os
import Cryptodome.Cipher.AES as AES
from .cipher import EncryptionCipher, DecryptionCipher, CipherHeader


def encryptFileObj(reader, writer, key, nonce=None, **kwargs):
    if not isinstance(key, bytes):
        raise TypeError("key must be a bytes object")
    if not (isinstance(nonce, bytes) or nonce is None):
        raise TypeError("nonce must be a bytes object or None")
    cipher = EncryptionCipher(key, nonce, **kwargs)
    intake = reader.read(4096)
    while len(intake):
        writer.write(cipher.encrypt(intake))
        writer.flush()
        intake = reader.read(4096)
    writer.write(cipher.finish())
    writer.flush()
    return cipher.nonce


def encryptFile(input_filename, output_filename, key, nonce=None, **kwargs):
    with open(input_filename, mode='rb') as reader:
        with open(output_filename, mode='wb') as writer:
            return encryptFileObj(reader, writer, key, nonce, **kwargs)


def decryptFileObj(
    reader,
    writer,
    key,
    nonce=None,
    compatability=False
):
    if not isinstance(key, bytes):
        raise TypeError("key must be a bytes object")
    if not (isinstance(nonce, bytes) or nonce is None):
        raise TypeError("nonce must be a bytes object or None")
    intake = reader.read(64)  # read header data
    cipher = DecryptionCipher(intake, key, nonce, compatability)
    intake = reader.read(4096)
    while len(intake):
        writer.write(cipher.decrypt(intake))
        writer.flush()
        intake = reader.read(4096)
    writer.write(cipher.finish())
    writer.flush()


def decryptFile(
    input_filename,
    output_filename,
    key,
    nonce=None,
    compatability=False
):
    with open(input_filename, mode='rb') as reader:
        with open(output_filename, mode='wb') as writer:
            decryptFileObj(
                reader,
                writer,
                key,
                nonce,
                compatability
            )
