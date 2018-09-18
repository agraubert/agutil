from . import protocols
from os import urandom
import hashlib
import sys
import io
import os
import Cryptodome.Cipher.AES as AES
from .cipher_header import CipherHeader, Bitmask
from ... import bytesToInt, intToBytes
from functools import wraps


def expect_stream(func):
    @wraps(func)
    def call(size, *args, **kwargs):
        result = func(size, *args, **kwargs)
        if len(result) < size:
            raise HeaderLengthError(
                "Cipher requires additional data to initialize"
            )
        return result
    return call


def cipher_type(name):
    if isinstance(name, int):
        return name
    return getattr(
        AES,
        'mode_'+name
    )


class CipherError(ValueError):
    pass


class HeaderError(CipherError):
    pass


class HeaderLengthError(HeaderError):
    pass


class InvalidHeaderError(HeaderError):
    pass


class EncryptionError(CipherError):
    pass


class DecryptionError(CipherError):
    pass


def apply_user_options(defaults, opts):
    implications = {}
    if 'encrypted_nonce' in opts and opts['encrypted_nonce']:
        implications['legacy_store_nonce'] = True
        implications['legacy_randomized_nonce'] = False
        implications['legacy_validate_nonce'] = False
    if (
        'cipher_type' in opts
        and cipher_type(opts['cipher_type']) == AES.MODE_CCM
    ):
        if 'ccm_message_length' in opts:
            implications['enable_streaming'] = True
        else:
            implications['enable_streaming'] = False
    if (
        'cipher_type' in opts
        and cipher_type(opts['cipher_type']) in _LEGACY_CIPHERS
    ):
        implications['store_tag'] = False
    if (
        'secondary_cipher_type' in opts
        and cipher_type(opts['secondary_cipher_type']) == AES.MODE_CTR
    ):
        implications['cipher_nonce_length'] = 8
    if (
        'secondary_cipher_type' in opts
        and cipher_type(opts['secondary_cipher_type']) == AES.MODE_OPENPGP
    ):
        implications['legacy_store_nonce'] = True
        implications['legacy_randomized_nonce'] = False
    if (
        'cipher_type' in opts
        and cipher_type(opts['cipher_type']) == AES.MODE_OPENPGP
    ):
        implications['store_nonce'] = True
        implications['encrypted_nonce'] = False
    if (
        'secondary_cipher_type' in opts
        and cipher_type(opts['secondary_cipher_type']) == AES.MODE_ECB
    ):
        implications['legacy_store_nonce'] = False
        implications['legacy_randomized_nonce'] = False
    if (
        'cipher_type' in opts
        and cipher_type(opts['cipher_type']) == AES.MODE_ECB
    ):
        implications['store_nonce'] = False
        implications['encrypted_nonce'] = False
    if 'cipher_type' in opts:
        if (cipher_type(opts['cipher_type']) == AES.MODE_CTR):
            implications['cipher_nonce_length'] = 8
        elif cipher_type(opts['cipher_type']) == AES.MODE_CCM:
            implications['cipher_nonce_length'] = 7
        elif cipher_type(opts['cipher_type']) == AES.MODE_OCB:
            implications['cipher_nonce_length'] = 15
        elif cipher_type(opts['cipher_type']) == AES.MODE_SIV:
            implications['store_tag'] = True
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
        raise InvalidHeaderError(
            "Legacy cipher cannot be CCM, EAX, GCM, SIV, or OCB"
        )
    if opts['encrypted_nonce'] and opts['legacy_validate_nonce']:
        raise InvalidHeaderError(
            "Cannot store encrypted nonce and enable legacy nonce validation"
        )
    if opts['encrypted_tag'] and not opts['encrypted_nonce']:
        raise InvalidHeaderError(
            "Cannot encrypt tag without encrypting nonce"
        )
    if (
        opts['cipher_type'] == AES.MODE_CTR
        or opts['secondary_cipher_type'] == AES.MODE_CTR
    ):
        length = opts['cipher_nonce_length']
        if length < 0 or length > 15:
            raise InvalidHeaderError(
                "CTR ciphers must have nonce in range [0, 15]"
            )
        start = opts['ctr_initial_value']
        if start < 0 or start > 65535:
            raise InvalidHeaderError(
                "CTR ciphers must have initial value in range [0, 65535]"
            )
    if opts['cipher_type'] == AES.MODE_OPENPGP and not opts['store_nonce']:
        raise InvalidHeaderError(
            "OPENPGP ciphers require store_nonce and legacy_store_nonce"
        )
    if opts['cipher_type'] == AES.MODE_OPENPGP and opts['encrypted_nonce']:
        raise InvalidHeaderError(
            'Cannot use encrypted_nonce with OPENPGP ciphers'
        )
    if (
        opts['secondary_cipher_type'] == AES.MODE_OPENPGP
        and not opts['legacy_store_nonce']
    ):
        raise InvalidHeaderError(
            "OPENPGP ciphers require store_nonce and legacy_store_nonce"
        )
    if opts['cipher_type'] == AES.MODE_ECB and opts['store_nonce']:
        raise InvalidHeaderError(
            "ECB ciphers do not use a nonce"
        )
    if opts['cipher_type'] == AES.MODE_ECB and opts['encrypted_nonce']:
        raise InvalidHeaderError(
            "ECB ciphers do not use a nonce"
        )
    if (
        opts['secondary_cipher_type'] == AES.MODE_ECB
        and (opts['legacy_store_nonce'] or opts['legacy_randomized_nonce'])
    ):
        raise InvalidHeaderError(
            "ECB ciphers do not use a nonce"
        )
    if opts['cipher_type'] == AES.MODE_CCM:
        length = opts['cipher_nonce_length']
        if length < 7 or length > 13:
            raise InvalidHeaderError(
                "CCM ciphers must have nonce in range [7, 13]"
            )
        length = opts['ccm_message_length']
        if length is not None and (length < 0 or length > 65535):
            raise InvalidHeaderError(
                "CCM ciphers must have message length in range [0, 65535]. "
                "If you desire a longer message size, do not specify size "
                "in advance (which disables streaming)"
            )
    elif opts['cipher_type'] == AES.MODE_OCB:
        length = opts['cipher_nonce_length']
        if length < 1 or length > 15:
            raise InvalidHeaderError(
                "OCB ciphers must have nonce in range [1, 15]"
            )
    elif opts['cipher_type'] == AES.MODE_SIV and (
        opts['enable_streaming'] or not opts['store_tag']
    ):
        raise InvalidHeaderError(
            "SIV ciphers must disable streaming and must store the tag"
        )
    if opts['enable_compatability'] and (opts['store_nonce']
                                         or opts['encrypted_nonce']
                                         or opts['store_tag']
                                         or opts['encrypted_tag']
                                         or opts['legacy_store_nonce']):
        raise InvalidHeaderError(
            "Compatability mode cannot be combined with "
            "store_nonce, encrypted_nonce, store_tag, encrypted_tag, "
            "or legacy_store_nonce"
        )
    if opts['enable_compatability'] and not opts['use_legacy_ciphers']:
        raise InvalidHeaderError(
            "Legacy ciphers must be used in compatability mode"
        )
    if opts['legacy_randomized_nonce'] and opts['legacy_store_nonce']:
        raise InvalidHeaderError(
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
        becomes available. Implied value depends on cipher type.
        If streaming is disabled, either explicitly, or implicitly (by using a
        cipher which does not support output), the entire plaintext must be
        encrypted before any output will be produced
        be produced. Default: True
    cipher_nonce_length: Sets the length of the nonce for CTR, CCM, and OCB
        ciphers. Please check the Pycryptodome docs for allowed sizes.
        For ciphers besides these three, this parameter is ignored and a
        16-byte nonce is used.
        Default: Largest allowed nonce based on cipher type.
    ccm_message_length: Sets the length of the message for a CCM cipher.
        If this parameter is provided, it will imply enable_streaming.
        CCM ciphers cannot enable streaming without this setting.
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


class AbstractCipher(object):
    secondary_cipher = None
    block_size = 4096
    tag_size = 16
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
    def __init__(self, key, nonce=None, header=None, **kwargs):
        if header is None:
            header = configure_cipher(**kwargs)
        if nonce is None:
            nonce = os.urandom(16)
        self.header = header
        self.header_buffer = self.header.data
        # Initialize the cipher and buffer any initial data
        # (header, nonce, validation/extra-data blocks)
        if not self.header.valid:
            raise InvalidHeaderError("Header is not valid")
        if self.header.use_modern_cipher:
            self.tag_size = self.header.cipher_data[1]
            self.block_size = self.header.cipher_data[2] * 256
            if self.header.control_bitmask[3]:
                if self.header.legacy_bitmask[2]:
                    self.secondary_cipher = self._initialize_legacy_cipher(
                        key
                    )
                    self.header_buffer += self.secondary_cipher.encrypt(
                        os.urandom(16)  # bypass block
                    )
                else:
                    self.secondary_cipher = self._initialize_legacy_cipher(
                        key,
                        nonce
                    )
                    if self.header.secondary_id not in _SKIP_NONCE:
                        self.header_buffer += nonce
                    nonce = os.urandom(16)
                self.header_buffer += self.secondary_cipher.encrypt(nonce)
            elif self.header.control_bitmask[2]:
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
            if self.header.cipher_id == AES.MODE_OPENPGP:
                self.header_buffer = self.header_buffer[:-16]
        else:
            self.cipher = self._initialize_legacy_cipher(key, nonce)
            if self.header.legacy_bitmask[4]:
                # If the cipher is in compatability (headerless) mode,
                # clear out the header. We don't need to store it
                self.header_buffer = b''
            if self.header.legacy_bitmask[2]:
                self.header_buffer += self.cipher.encrypt(os.urandom(16))
            elif (
                self.header.legacy_bitmask[3]
                and not self.header.secondary_id == AES.MODE_OPENPGP
                and not self.header.secondary_id == AES.MODE_ECB
            ):
                self.header_buffer += nonce
            if self.header.legacy_bitmask[5]:
                self.header_buffer += self.cipher.encrypt(
                    b'\x00'*self.header.exdata_size
                )
        self.nonce = nonce

    def _initialize_legacy_cipher(self, key, nonce=None):
        if self.header.secondary_id != AES.MODE_ECB:
            if self.header.legacy_bitmask[2]:
                nonce = os.urandom(16)
        return initialize_cipher(
            self.header.secondary_id,
            key,
            nonce,
            self.header.cipher_data[3:],
            16
        )

    def _siv_terminate(self, output):
        ciphertext, tag = self.cipher.encrypt_and_digest(output)
        if self.header.control_bitmask[5]:
            if self.secondary_cipher is None:
                raise EncryptionError(
                    "Cannot encrypt tag without secondary cipher"
                )
            tag = self.secondary_cipher.encrypt(tag)
        return ciphertext + tag

    def _terminate(self):
        output = b''
        if not self.streaming_enabled:
            # Cipher was not stream enabled, so do all the chunk preparation
            # that streaming ciphers did earlier
            if len(self.data_buffer) >= self.block_size - 1:
                while len(self.data_buffer) >= self.block_size - 1:
                    output += protocols.padstring(
                        self.data_buffer[:self.block_size - 1]
                    )
                    self.data_buffer = self.data_buffer[self.block_size - 1:]
        if len(self.data_buffer):
            # Any leftover data in the buffer needs to be padded for encryption
            output += protocols.padstring(self.data_buffer)
        if len(output):
            # If there is any unencrypted data, encrypt it now
            # For non-streaming ciphers, this is the single encryption step
            if self.header.cipher_id == AES.MODE_SIV:
                return self._siv_terminate(output)
            output = self.cipher.encrypt(output)
            if self.header.cipher_id == AES.MODE_OCB:
                output += self.cipher.encrypt()
        if self.header.use_modern_cipher and self.header.control_bitmask[4]:
            # Generate a MAC tag, if we are configured to do so
            tag = self.cipher.digest()
            if self.header.control_bitmask[5]:
                if self.secondary_cipher is None:
                    raise EncryptionError(
                        "Cannot encrypt tag without secondary cipher"
                    )
                tag = self.secondary_cipher.encrypt(tag)
            output += tag
        # Now output any ciphertext and/or MAC tag data generated
        return output

    def encrypt(self, data):
        self.data_buffer += data
        output = b'' + self.header_buffer
        self.header_buffer = b''
        if not self.streaming_enabled:
            # Cipher does not support streaming
            # Buffer the data until we finish
            pass
        elif len(self.data_buffer) >= self.block_size - 1:
            input_data = b''
            # Encrypt as many complete chunks that we have data for
            # Buffer leftover data for later
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
        self.stream = io.BytesIO(init_data)
        if len(init_data) < 16:
            raise HeaderLengthError(
                "Cannot initialize cipher without at least 16 bytes"
            )
        self.stream.read = expect_stream(self.stream.read)
        header_data = self.stream.read(16)
        self._raw_header = header_data
        header = CipherHeader(header_data[:-1])
        # Check the header. If it's valid, use it to configure the cipher
        # If it's not, assume headerless format. The data we just read was
        # probably the nonce block. In that case, generate a fake header to
        # configure the cipher
        if header.valid:
            if header.weight == header_data[-1]:
                self.header = header
            elif legacy_force:
                self.header = CipherHeader()
                control = Bitmask()
                control[1] = True  # Enable legacy cipher
                control[2] = True  # Pick random nonce
                control[4] = True  # Use raw_header instead of nonce block
                control.set_range(6, 8)  # Enable legacy cipher
                self.header.legacy_bitmask = control
                self.header.secondary_id = AES.MODE_CBC
            else:
                raise InvalidHeaderError("This header is in an invalid state")
        elif legacy_force:
            self.header = CipherHeader()
            control = Bitmask()
            control[1] = True  # Enable legacy cipher
            control[2] = True  # Pick random nonce
            control[4] = True  # Use raw_header instead of nonce block
            control.set_range(6, 8)  # Enable legacy cipher
            self.header.legacy_bitmask = control
            self.header.secondary_id = AES.MODE_CBC
        else:
            self.header = CipherHeader()
            control = Bitmask()
            control[1] = True  # Enable legacy cipher
            control[2] = True  # Pick random nonce
            control[4] = True  # Use raw_header instead of nonce block
            control[5] = True  # Read exdata for validation
            self.header.legacy_bitmask = control
            self.header.exdata_size = 16  # validation block stored in exdata
            self.header.secondary_id = AES.MODE_CBC
        if self.header.use_modern_cipher:
            if self.header.control_bitmask[2]:
                if self.header.control_bitmask[3]:
                    self.secondary_cipher = self._initialize_legacy_cipher(
                        key,
                        nonce
                    )
                    rn = (
                        self.stream.read(self.header.exdata_size)
                        if self.header.legacy_bitmask[2]
                        or self.header.legacy_bitmask[3]
                        else self.stream.read(16)
                    )
                    nonce = self.secondary_cipher.decrypt(rn)
                elif self.header.cipher_id == AES.MODE_OPENPGP:
                    nonce = self.stream.read(18)
                else:
                    nonce = self.stream.read(16)
            if nonce is None and self.header.cipher_id != AES.MODE_ECB:
                raise HeaderError(
                    "Header specified external nonce but a nonce was not "
                    "provided"
                )
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
        self.tag_size = (
            self.header.cipher_data[1]
            if self.header.use_modern_cipher and self.header.control_bitmask[4]
            else 0
        )
        self.stream.read = self.stream.read.__wrapped__

    def _initialize_legacy_cipher(self, key, nonce=None):
        if self.header.secondary_id != AES.MODE_ECB:
            if self.header.legacy_bitmask[2]:
                nonce = os.urandom(16)
            elif self.header.secondary_id == AES.MODE_OPENPGP:
                nonce = self.stream.read(18)
            elif self.header.legacy_bitmask[3]:
                nonce = self.stream.read(16)
            elif nonce is None:
                raise HeaderError(
                    "Header specified external nonce but a nonce was not "
                    "provided"
                )
        cipher = initialize_cipher(
            self.header.secondary_id,
            key,
            nonce,
            self.header.cipher_data[3:],
            16
        )
        if (
            self.header.secondary_id != AES.MODE_ECB
            and self.header.legacy_bitmask[2]
        ):
            if self.header.legacy_bitmask[4]:
                cipher.decrypt(self._raw_header)
            else:
                cipher.decrypt(self.stream.read(16))
        if self.header.legacy_bitmask[5]:
            validation = cipher.decrypt(
                self.stream.read(
                    self.header.exdata_size
                )
            )
            if validation != b'\x00'*self.header.exdata_size:
                raise DecryptionError(
                    "Header validation block did not match expected value"
                )
        return cipher

    def decrypt(self, data=b''):
        data = self.stream.read() + data
        output = b''
        if self.streaming_enabled:
            # Chunk the buffered ciphertext into complete padded ciphertext
            for block in self._blk_read(data):
                output += block
            if len(output) >= self.block_size:
                # Decrypt blocks which are ready
                output = self.cipher.decrypt(output)
        else:
            # This cipher does not support streaming, so buffer until we finish
            self.data_buffer += data
        return self._unpad_blocks(output)

    def _terminate(self):
        # Finish decryption
        if self.streaming_enabled:
            # If we have been streaming data, decrypt any remaining data
            # in the buffer
            output = (
                self.decrypt(b'')
                + self.cipher.decrypt(self.data_buffer)
            )
        elif self.header.cipher_id != AES.MODE_SIV:
            # If the cipher has not been streaming, then all the ciphertext is
            # currently buffered. Decrypt now
            output = self.cipher.decrypt(
                b''.join(block for block in self._blk_read(self.stream.read()))
                + self.data_buffer
            )
        else:
            return self._siv_terminate()
        if self.header.cipher_id == AES.MODE_OCB:
            output += self.cipher.decrypt()
        # At this point, all ciphertext has been decrypted and (if enabled)
        # the MAC tag remains in the tag buffer
        if self.header.use_modern_cipher and self.header.control_bitmask[4]:
            # Use the buffered tag data as the MAC tag
            if len(self.tag_buffer) != self.tag_size:
                raise DecryptionError(
                    "No data left in stream"
                )
            if self.header.control_bitmask[5]:
                if self.secondary_cipher is None:
                    raise DecryptionError(
                        "Cannot decrypt tag without secondary cipher"
                    )
                self.tag_buffer = self.secondary_cipher.decrypt(
                    self.tag_buffer
                )
            self.cipher.verify(self.tag_buffer)
        return self._unpad_blocks(output)

    def _blk_read(self, data):
        # Read blocks of data and yield chunks, while making sure to store
        # enough data to use as a MAC tag
        self.data_buffer += self.tag_buffer + data
        while len(self.data_buffer) >= self.block_size + self.tag_size:
            self.tag_buffer = self.data_buffer[self.block_size:]
            # Yield one full chunk of data
            yield self.data_buffer[:self.block_size]
            self.data_buffer = self.data_buffer[self.block_size:]
        if self.tag_size > 0:
            self.tag_buffer = self.data_buffer[-1*self.tag_size:]
            self.data_buffer = self.data_buffer[:-1*self.tag_size]
        else:
            self.tag_buffer = b''
        # No more complete data chunks. Store remaining data in buffer

    def _unpad_blocks(self, data):
        # Unpad full chunks of data back into plaintext
        output = b''
        while len(data) >= self.block_size:
            output += protocols.unpadstring(data[:self.block_size])
            data = data[self.block_size:]
        if len(data):
            output += protocols.unpadstring(data)
        return output

    def _siv_terminate(self):
        output = (
            b''.join(block for block in self._blk_read(self.stream.read()))
            + self.data_buffer
        )
        if len(self.tag_buffer) != self.tag_size:
            raise DecryptionError(
                "No data left in stream"
            )
        if self.header.control_bitmask[5]:
            if self.secondary_cipher is None:
                raise DecryptionError(
                    "Cannot decrypt tag without secondary cipher"
                )
            self.tag_buffer = self.secondary_cipher.decrypt(
                self.tag_buffer
            )
        plaintext = self.cipher.decrypt_and_verify(output, self.tag_buffer)
        return self._unpad_blocks(plaintext)


_IV_CIPHERS = {AES.MODE_CBC, AES.MODE_CFB, AES.MODE_OFB, AES.MODE_OPENPGP}
_NONCE_CIPHERS = {AES.MODE_EAX, AES.MODE_GCM}
_LEGACY_CIPHERS = {
    AES.MODE_ECB, AES.MODE_CBC, AES.MODE_CTR, AES.MODE_CFB, AES.MODE_OFB,
    AES.MODE_OPENPGP
}
_SKIP_NONCE = {AES.MODE_ECB, AES.MODE_OPENPGP}
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
