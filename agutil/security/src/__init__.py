"""
Agutil Cipher format:
[16 byte header]
[16 or 0 byte nonce block]
[Variable size extra-data block]
[Ciphertext]
[Variable size MAC tag block]

Legacy Compatability (headerless) format:
[16 byte nonce block]
[16 byte validation block]
[Ciphertext]

Header format (16 Bytes):
[0x00], [legacy cipher bitmask], [modern cipher bitmask],
[size of extradata block], [modern cipher id], [legacy cipher id],
[
    Cipher data:
    [Modern extended bitmask],
    [Size of MAC tag block],
    [Size of each ciphertext chunk/256],
    [3 bytes of cipher-specific data]
], [2 bytes reserved 0x0000], [0xae], [Header checksum (hamming weight)]

Legacy Cipher Bitmask format:
0, [use legacy cipher], [legacy cipher uses a randomized nonce],
[legacy cipher should read/write the nonce from/to the nonce block],
[0. Cipher sets internally if legacy headerless mode is enabled],
[legacy cipher uses the extra-data block as validation],
[2 bits reserved. Currently: use legacy cipher, use legacy cipher]

Modern Cipher Bitmask Format:
0, [use modern cipher],
[modern cipher should read/write the nonce from/to the nonce block],
[use legacy cipher to encrypt/decrypt the nonce block],
[modern cipher should read/write the MAC tag to the tag block],
[use legacy cipher to encrypt/decrypt the tag block],
[0. Cipher sets internally if current configuration supports streaming],
[1 bit reserved. Currently: use modern cipher]

Modern Extended Bitmask Format:
0000000,
[0. Cipher sets internally if the chosen cipher requires a 16-byte key]
"""
