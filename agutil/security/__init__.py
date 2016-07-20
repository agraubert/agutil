_PROTOCOL_VERSION_ = '2.0.0'
_PROTOCOL_IDENTIFIER_ = "<Agutil-security> <v%s>"%(_PROTOCOL_VERSION_)
from .src.securesocket import SecureSocket
from .src.connection import SecureConnection
from .src.files import encryptFile, decryptFile
from .src.server import SecureServer
