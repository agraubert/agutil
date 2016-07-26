_PROTOCOL_VERSION_ = '1.0.0'
_PROTOCOL_IDENTIFIER_ = "<agutil><__protocol__:%s>"%_PROTOCOL_VERSION_

def parseIdentifier(identifier):
    tags = identifier[1:-1].split("><")
    output = {}
    for tag in tags:
        data = tag.split(":")
        if len(data)==1:
            data.append(True)
        output[data[0]]=data[1]
    return (output, checkIdentifier(output, 'agutil') and checkIdentifier(output, '__protocol__', _PROTOCOL_VERSION_))

def checkIdentifier(identifier, key, value=True):
    return key in identifier and identifier[key]==value
