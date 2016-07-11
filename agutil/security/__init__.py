_PROTOCOL_VERSION_ = '1.0.0'
_PROTOCOL_IDENTIFIER_ = "<Agutil-security> <v%s>"%(_PROTOCOL_VERSION_)
from .src.core import new
from .src.channel import SecureSocket
