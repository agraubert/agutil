from . import protocols
from os import urandom
import hashlib
import sys
import os
import Cryptodome.Cipher.AES as AES


def encryptFileObj(
    reader,
    writer,
    legacy_cipher,
    modern_cipher=None,
    validate=False,
    _prechunk=False
):
    if modern_cipher is not None or _prechunk:
        writer.write(legacy_cipher.encrypt(urandom(16)))
    if modern_cipher is not None or validate:
        writer.write(legacy_cipher.encrypt(
            (
                b'\x00'*16 if modern_cipher is None
                else b'\x01'*16
            )
        ))
    if modern_cipher is not None:
        cipher = modern_cipher
    else:
        cipher = legacy_cipher
    intake = reader.read(4095)
    while len(intake):
        writer.write(_encrypt_chunk(intake, cipher))
        writer.flush()
        intake = reader.read(4095)
    if cipher is modern_cipher:
        writer.write(legacy_cipher.encrypt(cipher.digest()))
        writer.flush()


def encryptFile(
    input_filename,
    output_filename,
    legacy_cipher,
    modern_cipher=None,
    validate=False,
    _prechunk=False
):
    reader = open(input_filename, mode='rb')
    writer = open(output_filename, mode='wb')
    encryptFileObj(
        reader,
        writer,
        legacy_cipher,
        modern_cipher,
        validate=validate,
        _prechunk=_prechunk
    )
    reader.close()
    writer.close()


def decryptFileObj(
    reader,
    writer,
    legacy_cipher,
    modern_cipher=None,
    validate=False,
    _prechunk=False
):
    tag = b''
    if modern_cipher is not None or _prechunk:
        legacy_cipher.decrypt(reader.read(16))
    if modern_cipher is not None or validate:
        mode = legacy_cipher.decrypt(reader.read(16))
        if mode == b'\x01' * 16:
            if modern_cipher is None:
                reader.close()
                writer.close()
                raise KeyError(
                    "Decryption Failed! A modern cipher is required"
                )
            cipher = modern_cipher
        elif mode == b'\x00' * 16:
            cipher = legacy_cipher
        else:
            reader.close()
            writer.close()
            raise KeyError(
                "Decryption Failed! The cipher used may be incorrect"
            )
    if modern_cipher is None and not (validate and _prechunk):
        cipher = legacy_cipher
    intake = reader.read(4112 if cipher is modern_cipher else 4096)
    while len(intake):
        if cipher is modern_cipher:
            intake = tag + intake
            tag = intake[-16:]
            intake = intake[:-16]
        writer.write(_decrypt_chunk(intake, cipher))
        writer.flush()
        intake = reader.read(4096)
    if len(tag):
        cipher.verify(legacy_cipher.decrypt(tag))


def decryptFile(
    input_filename,
    output_filename,
    legacy_cipher,
    modern_cipher=None,
    validate=False,
    _prechunk=False
):
    reader = open(input_filename, mode='rb')
    writer = open(output_filename, mode='wb')
    decryptFileObj(
        reader,
        writer,
        legacy_cipher,
        modern_cipher,
        validate=validate,
        _prechunk=_prechunk
    )
    reader.close()
    writer.close()


def _encrypt_chunk(chunk, cipher):
    return cipher.encrypt(protocols.padstring(chunk))


def _decrypt_chunk(chunk, cipher):
    return protocols.unpadstring(cipher.decrypt(chunk))
