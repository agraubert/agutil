import logging
import time
import sys
import functools
# Timestamp format: "[%a %m/%d/%Y %I:%M:%S %p]"


def DummyLog(msg, channel=""):
    pass


def _bindToSender(x):
    return DummyLog


def _close():
    pass


DummyLog.bindToSender = _bindToSender
DummyLog.name = ""
DummyLog.close = _close


class Logger(object):
    LOGLEVEL_NONE = logging.CRITICAL
    LOGLEVEL_ERROR = logging.ERROR
    LOGLEVEL_WARN = logging.WARN
    LOGLEVEL_INFO = logging.INFO
    LOGLEVEL_DEBUG = logging.DEBUG
    LOGLEVEL_DETAIL = 5

    def __init__(
        self,
        filename=None,
        name='agutil',
        loglevel=logging.INFO
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(loglevel)
        if filename is None:
            self.handler = logging.StreamHandler(sys.stdout)
        elif isinstance(filename, str):
            self.handler = logging.FileHandler(filename)
        else:
            self.handler = logging.StreamHandler(filename)
        self.handler.setFormatter(
            logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                '%a %m/%d/%Y %I:%M:%S %p'
            )
        )
        # self.handler.setLevel(loglevel)
        self.logger.addHandler(self.handler)

        self.collection = {}
        self.channel_defs = {
            'DEBUG': logging.DEBUG,
            'DETAIL': 5,
            'INFO': logging.INFO,
            'WARNING': logging.WARN,
            'ERROR': logging.ERROR
        }
        self.mutes = {}
        logging.addLevelName(5, 'DETAIL')
        if loglevel <= logging.ERROR:
            self.setChannelCollection('ERROR', True)
        if loglevel <= logging.WARNING:
            self.setChannelCollection("WARNING", True)
        self.name = name
        self.log('[LOG STARTED]', 'LOGGER')

    def _forward_warn(self, channel):
        return (
            'WARNING'
            if channel == 'WARN' and 'WARN' not in self.channel_defs
            else channel
        )

    def __call__(self, message, sender='ANONYMOUS', channel='INFO'):
        return self.log(message, sender, channel)

    def log(self, message, sender='ANONYMOUS', channel='INFO'):
        channel = self._forward_warn(channel)
        if channel in self.collection:
            self.handler.acquire()
            try:
                self.collection[channel].append(
                    '[%s] [%s] [%s] : %s' % (
                        time.strftime("%a %m/%d/%Y %I:%M:%S %p"),
                        channel,
                        sender,
                        message
                    )
                )
            finally:
                self.handler.release()
        if sender not in self.mutes:
            try:
                self.logger.log(
                    self.channel_defs[channel],
                    '[%s] : %s' % (sender, message)
                )
            except KeyError as e:
                self.log(
                    "Sender [%s] attempted to use undefined channel [%s]" % (
                        sender, channel
                    ),
                    'LOGGER',
                    'WARN'
                )
        else:
            self.mutes[sender].append((message, channel))

    def _raw_message(self, msg, ch=20):
        self.logger.callHandlers(
            self.logger.makeRecord(
                self.logger.name,
                ch,
                '<NONE>',
                ch,
                msg,
                (),
                None
            )
        )

    def _set_level(self, l):
        self.logger.setLevel(l)

    def _get_level(self, l):
        return self.logger.getEffectiveLevel()

    level = property(_get_level, _set_level)

    def addChannel(self, name, priority):
        self.channel_defs[name] = priority
        logging.addLevelName(priority, name)
        if priority >= logging.WARNING and self.logger.isEnabledFor(priority):
            self.setChannelCollection(name, True)

    def bindToSender(self, sender, can_close=True):
        output = functools.partial(self.log, sender=sender)
        output.bindToSender = functools.partial(
            self.bindToSender,
            can_close=False
        )
        output.name = sender
        output.close = self.close if can_close else lambda: None
        return output

    def setChannelCollection(self, channel, collect=True):
        channel = self._forward_warn(channel)
        if channel not in self.channel_defs:
            raise NameError("No such channel '%s'" % channel)
        self.handler.acquire()
        try:
            if collect and channel not in self.collection:
                self.collection[channel] = []
            elif channel in self.collection and not collect:
                del self.collection[channel]
        finally:
            self.handler.release()

    def mute(self, mutee, muter="ANONYMOUS"):
        if mutee not in self.mutes:
            self.mutes[mutee] = []
            self.log(
                "Muting sender [%s]" % mutee,
                muter
            )

    def unmute(self, mutee):
        if mutee in self.mutes:
            self.log("Sender [%s] has been unmuted" % mutee, sender="LOGGER")
            if len(self.mutes[mutee]):
                (message, channel) = self.mutes[mutee][-1]
                suppressed = len(self.mutes[mutee])-1
                del self.mutes[mutee]
                self.log(
                    "%s <An additional %d messages were suppressed>" % (
                        message,
                        suppressed
                    ),
                    mutee,
                    channel
                )
            else:
                del self.mutes[mutee]

    def close(self):
        self.log("Logger shutting down", 'LOGGER')
        self.handler.setFormatter(
            logging.Formatter('%(message)s')
        )
        for channel in sorted(self.collection):
            enabled = self.logger.isEnabledFor(self.channel_defs[channel])
            if len(self.collection[channel]) and enabled:
                self._raw_message(
                    "<Dump of channel "+channel+'>',
                    self.channel_defs[channel]
                )
                for line in self.collection[channel]:
                    self._raw_message(line, self.channel_defs[channel])
                self._raw_message(
                    '--------------------',
                    self.channel_defs[channel]
                )
        self._raw_message(
            '[%s] [%s] [%s] : %s' % (
                time.strftime("%a %m/%d/%Y %I:%M:%S %p"),
                'INFO',
                'LOGGER',
                '[LOG STOPPED]'
            )
        )
        self.handler.acquire()
        try:
            self.logger.removeHandler(self.handler)
            self.handler.close()
        finally:
            self.handler.release()
