from . import protocols
from os import urandom
import hashlib
import sys
import io
import os
import Cryptodome.Cipher.AES as AES
from .cipher_header import CipherHeader, Bitmask
from ... import bytesToInt, intToBytes

if True:
    def do_print(*args, **kwargs):
        pass
else:
    do_print = print
# File format:
# Legacy:
# [16: encrypted(random)]
# [16: encrypted(0x00)]
# Modern (superformat):
# [16: format header]
# [toggle:16: nonce block] <- read unless modern and disabled nonce block
# [variable: exdata block] <- read under conditions where legacy cipher is used to parse nonce
# [body]
# [variable: tag]

# header format (16):
# 0x00, [legacy control bitmask], [modern control bitmask],
# [exdata blocksize], [modern cipher ID], [legacy cipher ID],
# [6:cipher specific data], [2:reserved], \xae, [header hamming weight]

# legacy control bitmask format:
# 0, [should use legacy cipher], [should use randomized nonce],
# [should read nonce block as nonce], [legacy compatability: use header for bypass],
# [should read exdata as validation], [should use legacy cipher] *2

# modern control bitmask format:
# 0, [should use modern cipher], [should read nonce block],
# [nonce block is legacy encrypted], [should read tag block],
# [tag block is legacy encrypted], [cipher is stream enabled],
# [should use modern cipher]

# modern cipher_data:
# [ex_cipher_bitmask], [tag block size], [data block size], [cipher data]*3
# ex_cipher_bitmask:
# [should use md5 on key], *

# on init, use mode argument to determine task
# decrypt init:
# read header: if valid, parse as modern header
# if invalid:
# if legacy_force is false: decrypt header and first block.
# expect block to be \x00*16
# if legacy_force is true: decrypt body and make no assertions

from functools import wraps
def expect_stream(func):
    @wraps(func)
    def call(size, *args, **kwargs):
        result = func(size, *args, **kwargs)
        if len(result) < size:
            raise ValueError("Cipher requires additional data to initialize")
        return result
    return call


def cipher_type(name):
    if isinstance(name, int):
        return name
    return getattr(
        AES,
        'mode_'+name
    )

def apply_user_options(defaults, opts):
    implications = {}
    if 'encrypted_nonce' in opts and opts['encrypted_nonce']:
        implications['legacy_store_nonce'] = True
        implications['legacy_randomized_nonce'] = False
        implications['legacy_validate_nonce'] = False
    if ('cipher_type' in opts
        and cipher_type(opts['cipher_type']) == AES.MODE_CCM):
        if 'ccm_message_length' in opts:
            implications['enable_streaming'] = True
        else:
            implications['enable_streaming'] = False
    if 'enable_compatability' in opts and opts['enable_compatability']:
        implications['store_nonce'] = False
        implications['encrypted_nonce'] = False
        implications['store_tag'] = False
        implications['encrypted_tag'] = False
        implications['use_legacy_ciphers'] = True
        implications['legacy_randomized_nonce'] = True
        implications['legacy_store_nonce'] = False
        implications['legacy_validate_nonce'] = True
    defaults.update(implications)
    defaults.update(opts)
    return defaults

def validate_config(opts):
    opts['cipher_type'] = cipher_type(opts['cipher_type'])
    opts['secondary_cipher_type'] = cipher_type(opts['secondary_cipher_type'])
    if opts['secondary_cipher_type'] not in _LEGACY_CIPHERS:
        raise ValueError("Legacy cipher cannot be CCM, EAX, GCM, SIV, or OCB")
    if opts['encrypted_nonce'] and opts['legacy_validate_nonce']:
        raise ValueError(
            "Cannot store encrypted nonce and enable legacy nonce validation"
        )
    if opts['encrypted_tag'] and not ops['encrypted_nonce']:
        raise ValueError(
            "Cannot encrypt tag without encrypting nonce"
        )
    if (opts['cipher_type'] == AES.MODE_CTR
        or opts['secondary_cipher_type'] == AES.MODE_CTR):
        length = opts['cipher_nonce_length']
        if length < 0 or length > 15:
            raise ValueError("CTR ciphers must have nonce in range [0, 15]")
        start = opts['ctr_initial_value']
        if start < 0 or start > 65535:
            raise ValueError(
                "CTR ciphers must have initial value in range [0, 65535]"
            )
    if opts['cipher_type'] == AES.MODE_CCM:
        length = opts['cipher_nonce_length']
        if length < 7 or length > 13:
            raise ValueError(
                "CCM ciphers must have nonce in range [7, 13]"
            )
        length = opts['ccm_message_length']
        if length is not None and (length < 0 or length > 65535):
            raise ValueError(
                "CCM ciphers must have message length in range [0, 65535]. "
                "If you desire a longer message size, do not specify size "
                "in advance (which disables streaming)"
            )
    elif opts['cipher_type'] == AES.MODE_OCB:
        length = opts['cipher_nonce_length']
        if length < 1 or length > 15:
            raise ValueError("OCB ciphers must have nonce in range [1, 15]")
    if opts['enable_compatability'] and (opts['store_nonce']
                                         or opts['encrypted_nonce']
                                         or opts['store_tag']
                                         or opts['encrypted_tag']
                                         or opts['legacy_store_nonce']):
        raise ValueError(
            "Compatability mode cannot be combined with "
            "store_nonce, encrypted_nonce, store_tag, encrypted_tag, "
            "or legacy_store_nonce"
        )
    if opts['enable_compatability'] and not opts['use_legacy_ciphers']:
        raise ValueError("Legacy ciphers must be used in compatability mode")
    if opts['legacy_randomized_nonce'] and opts['legacy_store_nonce']:
        raise ValueError(
            "legacy_randomized_nonce and legacy_store_nonce are mutually "
            "exclusive"
        )

def configure_cipher(**kwargs):
    """
    Keyword arguments:
    cipher_type: The AES cipher mode to use. Defaults to EAX.
        Ciphers can be given as the AES.MODE enumeration or a string value
        (Ex: 'EAX' or 9)
    secondary_cipher_type: The AES cipher mode to use for the legacy cipher.
        Cannot be CCM, EAX, GCM, SIV, or OCB. Defaults to CBC
    store_nonce: Stores nonce data in output. If this is disabled, the nonce
        must be communicated separately. Default: True
    encrypted_nonce: Use a legacy cipher to encrypt the primary cipher's nonce.
        Implies legacy_store_nonce and not legacy_randomized_nonce.
        Default: False
    store_tag: Stores a message tag to verify message authenticity. If this is
        disabled, the validity and integrity of the message cannot be
        guaranteed. Default: True
    tag_length: The length (in bytes) of tne message tag. Default: 16
    chunk_length: The length (in blocks of 256 bytes) of plaintext for each
        chunk. The cipher stream will emit one chunk of ciphertext each time a
        full plaintext chunk is read. Ciphertext and plaintext chunks are not
        necessarily the same size. Default: 16 blocks (4096 bytes)
    encrypted_tag: Use a legacy cipher to encrypt the message authentication
        block. Default: False
    enable_streaming: Configure the cipher to be able to encrypt data as it
        becomes available. Implied value depends on cipher type. If this is
        enabled in conjunction with a cipher that does not support streaming
        (CCM), the entire plaintext must be read in before any output will
        be produced. Default: True
    cipher_nonce_length: Sets the length of the nonce for CTR, CCM, and OCB
        ciphers. Please check the Pycryptodome docs for allowed sizes.
        For ciphers besides these three, this parameter is ignored and a
        16-byte nonce is used.
        Default: Largest allowed nonce based on cipher type.
    ccm_message_length: Sets the length of the message for a CCM cipher.
        If this parameter is provided, it will imply enable_streaming.
        If streaming is enabled without this parameter, the cipher must read
        the entire plaintext before producing any output.
        Maximum value: 65535
    ctr_initial_value: Sets the initial value of the counter for a CTR cipher.
        Maximum value: 65535. Default: 1.
    enable_compatability: Outputs data in a legacy format compataible with
        older versions of agutil. For compatability with the oldest versions of
        agutil, disable legacy_validate_nonce.
        Implies use_legacy_ciphers and disables all non-legacy configuration
        options. Default: False
    use_legacy_ciphers: Outputs data in the default modern format, but uses
        a legacy cipher configuration. Required by enable_compatability.
        Default: False
    legacy_randomized_nonce: Do not store Nonce or IV in output. Instead, a
        CBC mode cipher will be used and a special data block will be stored
        to allow Decryption without the IV. Exclusive to legacy_store_nonce.
        Implies legacy_cipher=CBC and not legacy_store_nonce. Default: False
    legacy_store_nonce: Stores the nonce in plaintext. Exclusive to
        legacy_randomized_nonce. If both this and legacy_randomized_nonce
        are False, the nonce must be communicated separately. Default: True
    legacy_validate_nonce: Stores data in the EXData block so that the key and
        nonce can be validated during Decryption. Exclusive to encrypted_nonce.
        Disable for compatability with the oldest versions of agutil.
        Default: True
    """
    config = {
        # default config with implications
        'cipher_type': AES.MODE_EAX,
        'secondary_cipher_type': AES.MODE_CBC,
        'store_nonce': True,
        'encrypted_nonce': False,
        'store_tag': True,
        'tag_length': 16,
        'chunk_length': 16,
        'encrypted_tag': False,
        'enable_streaming': True,
        'cipher_nonce_length': 16,
        'ccm_message_length': None,
        'ctr_initial_value': 1,
        'enable_compatability': False,
        'use_legacy_ciphers': False,
        'legacy_randomized_nonce': False,
        'legacy_store_nonce': True,
        'legacy_validate_nonce': True
    }
    # add user settings and implications

    config = apply_user_options(config, kwargs)
    validate_config(config)
    header = CipherHeader()
    legacy = Bitmask()
    legacy[1] = config['use_legacy_ciphers']
    legacy[2] = config['legacy_randomized_nonce']
    legacy[3] = config['legacy_store_nonce']
    legacy[4] = config['enable_compatability']
    legacy[5] = config['legacy_validate_nonce']
    legacy.set_range(6, 8, config['use_legacy_ciphers'])
    header.legacy_bitmask = legacy
    modern = Bitmask()
    modern[1] = not config['use_legacy_ciphers']
    modern[2] = config['store_nonce']
    modern[3] = config['encrypted_nonce']
    modern[4] = config['store_tag']
    modern[5] = config['encrypted_tag']
    modern[6] = config['enable_streaming']
    modern[7] = not config['use_legacy_ciphers']
    header.control_bitmask = modern
    use_exdata = config['legacy_validate_nonce']
    use_exdata |= config['encrypted_nonce'] and (
        config['legacy_store_nonce']
        or config['legacy_randomized_nonce']
    )
    if use_exdata:
        header.exdata_size = 16
    header.cipher_id = config['cipher_type']
    header.secondary_id = config['secondary_cipher_type']
    cipher_data = b'\x00'
    if header.cipher_id in _SHORT_KEY_CIPHERS:
        cipher_data = b'\x01'
    cipher_data += intToBytes(config['tag_length'])
    cipher_data += intToBytes(config['chunk_length'])
    if header.cipher_id == AES.MODE_CTR or header.secondary_id == AES.MODE_CTR:
        cipher_data += (
            intToBytes(config['cipher_nonce_length']) +
            intToBytes(config['ctr_initial_value'], 2)
        )
    if header.cipher_id == AES.MODE_CCM:
        if config['ccm_message_length'] is None:
            config['ccm_message_length'] = 0
        cipher_data += (
            intToBytes(config['cipher_nonce_length']) +
            intToBytes(config['ccm_message_length'], 2)
        )
    elif header.cipher_id == AES.MODE_OCB:
        cipher_data += (
            intToBytes(config['cipher_nonce_length']) +
            intToBytes(0, 2)
        )
    if len(cipher_data) < 6:
        cipher_data += b'\x00' * (6-len(cipher_data))
    header.cipher_data = cipher_data
    return header

class CipherManager(object):
    def __init__(self):
        self.cache = set()
    def validate_nonce(self, value):
        if value in self.cache:
            raise ValueError("This nonce has been previously used")
        self.cache.add(value)

class AbstractCipher(object):
    secondary_cipher = None
    block_size = 4096
    tag_size = 16
    parent = None
    data_buffer = b''

    @property
    def streaming_enabled(self):
        return (
            self.header.control_bitmask[6]
            or not self.header.use_modern_cipher
        )

    def finish(self):
        return self._terminate()

class EncryptionCipher(AbstractCipher):
    def __init__(self, header, key, nonce=None):
        if nonce is None:
            nonce = os.urandom(16)
        do_print("Initializing new cipher")
        self.header = header
        self.header_buffer = self.header.data
        if not self.header.valid:
            raise ValueError("Header is not valid")
        if self.header.use_modern_cipher:
            self.tag_size = self.header.cipher_data[1]
            self.block_size = self.header.cipher_data[2] * 256
            do_print("Config specifies modern cipher")
            if self.header.control_bitmask[3]:
                do_print("Generating legacy cipher to produce nonce")
                if self.header.legacy_bitmask[2]:
                    do_print("Legacy cipher uses randomized nonce")
                    self.secondary_cipher = self._initialize_legacy_cipher(
                        key
                    )
                    self.header_buffer += self.secondary_cipher.encrypt(
                        os.urandom(16) # bypass block
                    )
                else:
                    do_print("Legacy cipher uses given nonce")
                    self.secondary_cipher = self._initialize_legacy_cipher(
                        key,
                        nonce
                    )
                    self.header_buffer += nonce
                    nonce = os.urandom(16)
                self.header_buffer += self.secondary_cipher.encrypt(nonce)
            elif self.header.control_bitmask[2]:
                do_print("Storing plaintext nonce")
                self.header_buffer += nonce
            self.cipher = initialize_cipher(
                self.header.cipher_id,
                (
                    key
                    if not self.header.cipher_data[0]
                    else hashlib.md5(key).digest()
                ),
                nonce,
                self.header.cipher_data[3:],
                self.header.cipher_data[1]
            )
        else:
            self.cipher = self._initialize_legacy_cipher(key, nonce)
            if self.header.legacy_bitmask[4]:
                do_print("compatability mode. Clearing header buffer")
                self.header_buffer = b''
            if self.header.legacy_bitmask[2]:
                do_print("Storing nonce bypass block")
                self.header_buffer += self.cipher.encrypt(os.urandom(16))
            elif self.header.legacy_bitmask[3]:
                do_print("Storing plaintext nonce")
                self.header_buffer += nonce
            if self.header.legacy_bitmask[5]:
                do_print("Storing validation block")
                self.header_buffer += self.cipher.encrypt(b'\x00'*16)
        self.nonce = nonce

    def _initialize_legacy_cipher(self, key, nonce=None):
        do_print("Initializing a legacy cipher")
        if self.header.secondary_id != AES.MODE_ECB:
            do_print("Legacy - Nonce required by this cipher")
            if self.header.legacy_bitmask[2]:
                do_print("Using randomized nonce")
                nonce = os.urandom(16)
        return initialize_cipher(
            self.header.secondary_id,
            key,
            nonce,
            self.header.cipher_data[3:],
            16
        )

    def _terminate(self):
        do_print("TERM")
        output = b''
        if not self.streaming_enabled:
            do_print("Cipher is not stream-enabled. Chunking data now")
            if len(self.data_buffer) >= self.block_size - 1:
                while len(self.data_buffer) >= self.block_size - 1:
                    output += protocols.padstring(
                        self.data_buffer[:self.block_size - 1]
                    )
                    self.data_buffer = self.data_buffer[self.block_size - 1:]
        if len(self.data_buffer):
            output += protocols.padstring(self.data_buffer)
        if len(output):
            do_print("Padded plaintext:", output)
            output = self.cipher.encrypt(output)
        if self.header.use_modern_cipher and self.header.control_bitmask[4]:
            tag = self.cipher.digest()
            do_print("Plaintext tag:", tag, len(tag))
            if self.header.control_bitmask[5]:
                if self.secondary_cipher is None:
                    raise ValueError(
                        "Cannot encrypt tag without secondary cipher"
                    )
                tag = self.secondary_cipher.encrypt(tag)
            output += tag
        return output

    def encrypt(self, data):
        self.data_buffer += data
        output = b'' + self.header_buffer
        self.header_buffer = b''
        if not self.streaming_enabled:
            do_print("Cipher is not stream-enabled. Buffering data")
        elif len(self.data_buffer) >= self.block_size - 1:
            input_data = b''
            while len(self.data_buffer) >= self.block_size - 1:
                input_data += protocols.padstring(
                    self.data_buffer[:self.block_size - 1]
                )
                self.data_buffer = self.data_buffer[self.block_size - 1:]
            output += self.cipher.encrypt(input_data)
        return output


class DecryptionCipher(AbstractCipher):
    tag_buffer = b''
    def __init__(self, init_data, key, nonce=None, legacy_force=False):
        do_print("Stream initialized with", len(init_data), 'bytes')
        self.stream = io.BytesIO(init_data)
        if len(init_data) < 16:
            raise ValueError(
                "Cannot initialize cipher without at least 16 bytes"
            )
        self.stream.read = expect_stream(self.stream.read)
        header_data = self.stream.read(16)
        self._raw_header = header_data
        do_print("Initializing Cipher in Decryption Mode")
        header = CipherHeader(header_data[:-1])
        if header.valid:
            if header.weight == header_data[-1]:
                do_print("Header valid. Continuing in modern mode")
                self.header = header
            elif legacy_force:
                do_print("Using legacy_force mode. Modern failed hamming weight")
                self.header = CipherHeader()
                control = Bitmask()
                control[1] = True # Enable legacy cipher
                control[2] = True # Pick random nonce
                control[4] = True # Use raw_header instead of nonce block
                control.set_range(6, 8) # Enable legacy cipher
                self.header.legacy_bitmask = control
                self.header.secondary_id = AES.MODE_CBC
            else:
                raise ValueError("This header is in an invalid state")
        elif legacy_force:
            do_print("Using legacy_force mode. Modern failed header validity")
            self.header = CipherHeader()
            control = Bitmask()
            control[1] = True # Enable legacy cipher
            control[2] = True # Pick random nonce
            control[4] = True # Use raw_header instead of nonce block
            control.set_range(6, 8) # Enable legacy cipher
            self.header.legacy_bitmask = control
            self.header.secondary_id = AES.MODE_CBC
        else:
            do_print("Using Legacy mode. Modern failed header validity")
            self.header = CipherHeader()
            control = Bitmask()
            control[1] = True # Enable legacy cipher
            control[2] = True # Pick random nonce
            control[4] = True # Use raw_header instead of nonce block
            control[5] = True # Read exdata for validation
            self.header.legacy_bitmask = control
            self.header.exdata_size = 16 # validation block stored in exdata
            self.header.secondary_id = AES.MODE_CBC
        if self.header.use_modern_cipher:
            do_print("Initializing modern cipher")
            if self.header.control_bitmask[2]:
                do_print("Reading nonce from stream")
                if self.header.control_bitmask[3]:
                    do_print("Bitmask is encrypted. Assuming format from config:")
                    if self.header.legacy_bitmask[2]:
                        do_print("Legacy uses randomized nonce. Assumed settings 2")
                        do_print("Nonce block contains bypass")
                        do_print("Exdata contains encrypted nonce")
                    elif self.header.legacy_bitmask[3]:
                        do_print("Legacy uses stored nonce. Assumed settings 3")
                        do_print("nonce block contains legacy nonce")
                        do_print("Exdata contains encrypted nonce")
                    else:
                        do_print("Legacy uses given nonce or no nonce. Assumed settings -")
                        do_print("Nonce block contains encrypted nonce")
                        do_print("0 exdata")
                    self.secondary_cipher = self._initialize_legacy_cipher(
                        key,
                        nonce
                    )
                    nonce = self.secondary_cipher.decrypt(
                        self.stream.read(self.header.exdata_size)
                        if self.header.legacy_bitmask[2]
                        or self.header.legacy_bitmask[3]
                        else self.stream.read(16)
                    )
                else:
                    do_print("Reading plaintext nonce")
                    nonce = self.stream.read(16)
            if nonce is None and self.header.cipher_id != AES.MODE_ECB:
                raise ValueError(
                    "Header specified external nonce but a nonce was not "
                    "provided"
                )
            elif self.parent is not None and not self.header.legacy_bitmask[2]:
                do_print("Validating nonce")
                self.parent.validate_nonce(nonce)
            self.block_size = self.header.cipher_data[2] * 256
            self.cipher = initialize_cipher(
                self.header.cipher_id,
                (
                    hashlib.md5(key).digest()
                    if self.header.cipher_data[0]
                    else key
                ),
                nonce,
                self.header.cipher_data[3:],
                self.tag_size
            )
        else:
            self.cipher = self._initialize_legacy_cipher(key, nonce)
        # At this point, self.cipher is configured properly to read data
        do_print("Cipher ready")
        self.tag_size = (
            self.header.cipher_data[1]
            if self.header.use_modern_cipher and self.header.control_bitmask[4]
            else 0
        )
        self.stream.read = self.stream.read.__wrapped__

    def _initialize_legacy_cipher(self, key, nonce=None):
        do_print("Initializing a legacy cipher")
        if self.header.secondary_id != AES.MODE_ECB:
            do_print("Legacy - Nonce required by this cipher")
            if self.header.legacy_bitmask[2]:
                do_print("Using randomized nonce")
                nonce = os.urandom(16)
            elif self.header.legacy_bitmask[3]:
                do_print("Reading nonce block as nonce")
                nonce = self.stream.read(16)
            elif nonce is None:
                raise ValueError(
                    "Header specified external nonce but a nonce was not "
                    "provided"
                )
        if (self.parent is not None
            and not self.header.legacy_bitmask[2]
            and not self.header.use_modern_cipher):
            do_print("Parent available and nonce stored in plaintext. Validating nonce")
            self.parent.validate_nonce(nonce)
        do_print("Initializing cipher now")
        cipher = initialize_cipher(
            self.header.secondary_id,
            key,
            nonce,
            self.header.cipher_data[3:],
            16
        )
        if (self.header.secondary_id != AES.MODE_ECB
            and self.header.legacy_bitmask[2]):
            do_print("A randomized nonce was used")
            if self.header.legacy_bitmask[4]:
                do_print("Compatability mode: Using header as bypass")
                cipher.decrypt(self._raw_header)
            else:
                do_print("Reading nonce block for bypass")
                cipher.decrypt(self.stream.read(16))
        if self.header.legacy_bitmask[5]:
            do_print("Reading exdata for validation")
            validation = cipher.decrypt(
                self.stream.read(
                    self.header.exdata_size
                )
            )
            if validation != b'\x00'*self.header.exdata_size:
                raise ValueError(
                    "Header validation block did not match expected value"
                )
        do_print("Legacy cipher initialized")
        return cipher

    # def _block_read(self, block, block_size=None):
    #     if block_size is None:
    #         block_size = self.block_size
    #     if self.header.use_modern_cipher and len(self.tag_buffer) < self.tag_size:
    #         intake = self.stream.read(block_size + self.tag_size) + block
    #         self.tag_buffer = intake[-1*self.tag_size:]
    #         return intake[:-1*self.tag_size]
    #     elif len(self.tag_buffer):
    #         intake = self.tag_buffer + self.stream.read(block_size) + block
    #         self.tag_buffer = intake[-1*self.tag_size:]
    #         return intake[:-1*self.tag_size]
    #     return self.stream.read(self.block_size) + block

    def decrypt(self, data=b''):
        data = self.stream.read() + data
        do_print("Data for decryption:", data)
        output = b''
        if self.streaming_enabled:
            for block in self._blk_read(data):
                output += block
            do_print("Blocks ready for output:", output)
            if len(output) >= self.block_size:
                do_print("Decrypting blocks")
                output = self.cipher.decrypt(output)
        else:
            do_print("Cipher is not stream-enabled. Buffering data")
            self.data_buffer += data
        return self._unpad_blocks(output)

    def _terminate(self):
        do_print("Terminating. Available data:", self.data_buffer)
        if self.streaming_enabled:
            output = self.cipher.decrypt(self.data_buffer)
        else:
            do_print("Cipher is not stream-enabled. Chunking data now")
            output = self.cipher.decrypt(
                b''.join(block for block in self._blk_read(b''))
                + self.data_buffer
            )
            do_print("Length of plaintext:", len(output))
        do_print("Tag buffer state:", self.tag_buffer, len(self.tag_buffer))
        if self.header.use_modern_cipher and self.header.control_bitmask[4]:
            do_print("Extracting tag from buffer")
            if len(self.tag_buffer) != self.tag_size:
                raise ValueError(
                    "No data left in stream"
                )
            if self.header.control_bitmask[5]:
                if self.secondary_cipher is None:
                    raise ValueError(
                        "Cannot decrypt tag without secondary cipher"
                    )
                self.tag_buffer = self.secondary_cipher.decrypt(
                    self.tag_buffer
                )
            do_print("Plaintext tag:", self.tag_buffer, len(self.tag_buffer))
            self.cipher.verify(self.tag_buffer)
        do_print("Length of plaintext:", len(self._unpad_blocks(output)))
        return self._unpad_blocks(output)

    def _blk_read(self, data):
        do_print("BLK READ:", self.tag_buffer, self.tag_size)
        self.data_buffer += self.tag_buffer + data
        while len(self.data_buffer) >= self.block_size + self.tag_size:
            self.tag_buffer = self.data_buffer[self.block_size:]
            do_print("Yielding block:", self.data_buffer[:self.block_size])
            yield self.data_buffer[:self.block_size]
            self.data_buffer = self.data_buffer[self.block_size:]
        if self.tag_size > 0:
            self.tag_buffer = self.data_buffer[-1*self.tag_size:]
            self.data_buffer = self.data_buffer[:-1*self.tag_size]
        else:
            self.tag_buffer = b''
        do_print("Not enough data in buffer. Remaining buffer:", self.data_buffer)

    def _unpad_blocks(self, data):
        do_print("Unpadding plaintext:", data)
        output = b''
        while len(data) >= self.block_size:
            output += protocols.unpadstring(data[:self.block_size])
            data = data[self.block_size:]
        if len(data):
            output += protocols.unpadstring(data)
        return output



_IV_CIPHERS = {AES.MODE_CBC, AES.MODE_CFB, AES.MODE_OFB, AES.MODE_OPENPGP}
_NONCE_CIPHERS = {AES.MODE_EAX, AES.MODE_GCM}
_LEGACY_CIPHERS = {
    AES.MODE_ECB, AES.MODE_CBC, AES.MODE_CTR, AES.MODE_CFB, AES.MODE_OFB,
    AES.MODE_OPENPGP
}
_SHORT_KEY_CIPHERS = {AES.MODE_EAX}

def initialize_cipher(cipher_id, key, nonce, cipher_data, tag_length):
    if cipher_id == AES.MODE_ECB:
        return AES.new(
            key=key,
            mode=AES.MODE_ECB
        )
    elif cipher_id in _IV_CIPHERS:
        return AES.new(
            key=key,
            mode=cipher_id,
            iv=nonce
        )
    elif cipher_id == AES.MODE_CTR:
        # cipher-data = [nonce length], [ctr_iv:2]
        return AES.new(
            key=key,
            mode=AES.MODE_CTR,
            nonce=nonce[:cipher_data[0]],
            initial_value=bytesToInt(cipher_data[1:])
        )
    elif cipher_id == AES.MODE_CCM:
        # cipher_data = [nonce length], [length_of_message:2]
        msg_len = bytesToInt(cipher_data[1:])
        if msg_len == 0:
            msg_len = None
        return AES.new(
            key=key,
            mode=AES.MODE_CCM,
            nonce=nonce[:cipher_data[0]],
            mac_len=tag_length,
            msg_len=msg_len
        )
    elif cipher_id in _NONCE_CIPHERS:
        return AES.new(
            key=key,
            mode=cipher_id,
            nonce=nonce,
            mac_len=tag_length
        )
    elif cipher_id == AES.MODE_SIV:
        return AES.new(
            key=key,
            mode=AES.MODE_SIV,
            nonce=nonce,
        )
    elif cipher_id == AES.MODE_OCB:
        # cipher_data = [nonce length], 0*2
        return AES.new(
            key=key,
            mode=AES.MODE_OCB,
            nonce=nonce[:cipher_data[0]],
            mac_len=tag_length,
        )
