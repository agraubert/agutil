from . import protocols
from os import urandom
from io import BufferedIOBase

def encryptFile(input_filename, output_filename, cipher, _prechunk=False):
    if issubclass(type(input_filename), BufferedIOBase):
        closeR = False
        reader = input_filename
    else:
        closeR = True
        reader = open(input_filename, mode='rb')
    if issubclass(type(output_filename), BufferedIOBase):
        closeW = False
        writer = output_filename
    else:
        closeW = True
        writer = open(output_filename, mode='wb')
    if _prechunk:
        writer.write(cipher.encrypt(urandom(16)))
    intake = reader.read(4095)
    while len(intake):
        writer.write(_encrypt_chunk(intake, cipher))
        writer.flush()
        intake = reader.read(4095)
    if closeR:
        reader.close()
    if closeW:
        writer.close()

def decryptFile(input_filename, output_filename, cipher, _prechunk=False):
    if issubclass(type(input_filename), BufferedIOBase):
        closeR = False
        reader = input_filename
    else:
        closeR = True
        reader = open(input_filename, mode='rb')
    if issubclass(type(output_filename), BufferedIOBase):
        closeW = False
        writer = output_filename
    else:
        closeW = True
        writer = open(output_filename, mode='wb')
    if _prechunk:
        cipher.decrypt(reader.read(16))
    intake = reader.read(4096)
    while len(intake):
        print(len(intake))
        writer.write(_decrypt_chunk(intake, cipher))
        writer.flush()
        intake = reader.read(4096)
    if closeR:
        reader.close()
    if closeW:
        writer.close()

def _encrypt_chunk(chunk, cipher):
    return cipher.encrypt(protocols.padstring(chunk))

def _decrypt_chunk(chunk, cipher):
    return protocols.unpadstring(cipher.decrypt(chunk))
