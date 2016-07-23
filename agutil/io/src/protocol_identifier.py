_PROTOCOL_VERSION_ = '1.0.0'
_PROTOCOL_IDENTIFIER_ = "<agutil><__protocol__:%s>"%_PROTOCOL_VERSION_

def parseIdentifier(identifier):
    tags = identifier[1:-1].split("><")
    output = {}
    for tag in tags:
        (key, value) = tag.split(":")
        if value == '':
            value = True
        output[key]=value
    return (output, checkIdentifier(output, 'agutil') and checkIdentifier(output, '__protocol__', _PROTOCOL_VERSION_))

def checkIdentifier(identifier, key, value=True):
    return key in identifier and identifier[key]==value
