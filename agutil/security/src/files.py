from . import protocols
from os import urandom


def encryptFileObj(
    reader,
    writer,
    cipher,
    validate=False,
    _prechunk=False
):
    if _prechunk:
        writer.write(cipher.encrypt(urandom(16)))
    if validate:
        writer.write(cipher.encrypt(b'\x00'*16))
    intake = reader.read(4095)
    while len(intake):
        writer.write(_encrypt_chunk(intake, cipher))
        writer.flush()
        intake = reader.read(4095)


def encryptFile(
    input_filename,
    output_filename,
    cipher,
    validate=False,
    _prechunk=False
):
    reader = open(input_filename, mode='rb')
    writer = open(output_filename, mode='wb')
    encryptFileObj(reader, writer, cipher, validate=validate, _prechunk=_prechunk)
    reader.close()
    writer.close()


def decryptFileObj(
    reader,
    writer,
    cipher,
    validate=False,
    _prechunk=False
):
    if _prechunk:
        cipher.decrypt(reader.read(16))
    if validate:
        if cipher.decrypt(reader.read(16)) != b'\x00'*16:
            reader.close()
            writer.close()
            raise KeyError(
                "Decryption Failed! The cipher used may be incorrect"
            )
    intake = reader.read(4096)
    while len(intake):
        writer.write(_decrypt_chunk(intake, cipher))
        writer.flush()
        intake = reader.read(4096)


def decryptFile(
    input_filename,
    output_filename,
    cipher,
    validate=False,
    _prechunk=False
):
    reader = open(input_filename, mode='rb')
    writer = open(output_filename, mode='wb')
    decryptFileObj(reader, writer, cipher, validate=validate, _prechunk=_prechunk)
    reader.close()
    writer.close()


def _encrypt_chunk(chunk, cipher):
    return cipher.encrypt(protocols.padstring(chunk))


def _decrypt_chunk(chunk, cipher):
    return protocols.unpadstring(cipher.decrypt(chunk))
