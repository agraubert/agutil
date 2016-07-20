from . import protocols

def encryptFile(input_filename, output_filename, cipher):
    reader = open(input_filename, mode='rb')
    writer = open(output_filename, mode='wb')
    intake = reader.read(4095)
    while len(intake):
        writer.write(_encrypt_chunk(intake, cipher))
        writer.flush()
        intake = reader.read(4095)
    reader.close()
    writer.close()

def decryptFile(input_filename, output_filename, cipher):
    reader = open(input_filename, mode='rb')
    writer = open(output_filename, mode='wb')
    intake = reader.read(4095)
    while len(intake):
        writer.write(_decrypt_chunk(intake, cipher))
        writer.flush()
        intake = reader.read(4095)
    reader.close()
    writer.close()

def _encrypt_chunk(chunk, cipher):
    return cipher.encrypt(protocols.padstring(chunk))

def _decrypt_chunk(chunk, cipher):
    return protocols.unpadstring(cipher.decrypt(chunk))
