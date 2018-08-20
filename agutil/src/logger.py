import logging
import time
import sys
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

class object:
    def __init__(self, val):
        self.val = val

    def __le__(self, other):
        print("GETTING:", self.val, other)
        return False

    def __ge__(self, other):
        print("GETTING:", self.val, other)
        return False

    def __len__(self):
        return len(self.val)

    def __getitem__(self, idx):
        return self.val[idx]

class Logger(object):
    LOGLEVEL_NONE = logging.CRITICAL
    LOGLEVEL_ERROR = logging.ERROR
    LOGLEVEL_WARN = logging.WARN
    LOGLEVEL_INFO = logging.INFO
    LOGLEVEL_DEBUG = logging.DEBUG
    LOGLEVEL_DETAIL = logging.DEBUG
    def __init__(
        self,
        name='agutil',
        filename=None,
        loglevel=logging.INFO
    ):
        self.logger = logging.getLogger('agutil')
        self.logger.setLevel(1)
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
        self.handler.createLock()
        self.raw_message('[LOG STARTED]')
        self.collection = {
            'ERROR': [],
            'DEBUG': []
        }
        self.mutes = {}

    def log(self, message, sender='ANONYMOUS', channel='INFO'):
        channel = {
            'DEBUG': logging.DEBUG,
            'DETAIL': logging.DEBUG,
            'INFO': logging.INFO,
            'WARN': logging.WARN,
            'ERROR': logging.ERROR
        }[channel]
        self.logger.log(
            channel,
            '[%s] : %s' % (sender, message)
        )
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

    def raw_message(self, msg):
        self.logger.handle(
            self.logger.makeRecord(
                self.logger.name,
                20,
                '20',
                20,
                msg,
                (msg,),
                None
            )
        )

    def bindToSender(self, sender, can_close=True):

        def output(message, channel="INFO"):
            return self.log(message, sender, channel)

        def _bindToSender(sender):
            return self.bindToSender(sender, False)
        output.bindToSender = _bindToSender
        output.name = sender
        output.close = self.close if can_close else lambda: None
        return output

    def setChannelCollection(self, channel, collect):
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
                "Sender [%s] has been muted by [%s]" % (
                    mutee,
                    muter
                ),
                sender="LOGGER"
            )

    def unmute(self, mutee):
        if mutee in self.mutes:
            self.log("Sender [%s] has been unmuted" % mutee, sender="LOGGER")
            if len(self.mutes[mutee]):
                (message, channel) = self.mutes[mutee][0]
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

    def close(self):
        self.raw_message(">>>>>Logger shutting down")
        for channel in sorted(self.collection):
            if len(self.collection[channel]):
                self.raw_message(">>>>>Dump of channel "+channel)
                for line in self.collection[channel]:
                    self.raw_message(line)
                self.raw_message('--------------------')
            self.log('---[LOG STOPPED]---', 'LOGGER', 'INFO')
        self.handler.acquire()
        try:
            self.logger.removeHandler(self.handler)
            self.handler.close()
        finally:
            self.handler.release()

# class Logger(object):
#
#
#     def __init__(
#         self,
#         filename,
#         header="Agutil Logger",
#         log_level=LOGLEVEL_INFO,
#         stdout_level=LOGLEVEL_NONE
#     ):
#         self.logger = logging.getLogger('agutil')
#         self.logger.setLevel(1)
#         self.filelog = (
#             logging.FileHandler(filename) if filename is not None
#             else None
#         )
#         if self.filelog is not None:
#             self.filelog.setFormatter(
#                 logging.Formatter('%(message)s')
#             )
#             self.logger.addHandler(self.filelog)
#         self.outlog = logging.StreamHandler(sys.stdout)
#         self.outlog.setFormatter(logging.Formatter('%(message)s'))
#         self.logger.addHandler(self.outlog)
#         self.channels = {
#             'ERROR': [
#                 Logger.LOGLEVEL_ERROR >= log_level,
#                 Logger.LOGLEVEL_ERROR >= stdout_level,
#                 True
#             ],
#             'WARN': [
#                 Logger.LOGLEVEL_WARN >= log_level,
#                 Logger.LOGLEVEL_WARN >= stdout_level,
#                 True
#             ],
#             'INFO': [
#                 Logger.LOGLEVEL_INFO >= log_level,
#                 Logger.LOGLEVEL_INFO >= stdout_level,
#                 False
#             ],
#             'DEBUG': [
#                 Logger.LOGLEVEL_DEBUG >= log_level,
#                 Logger.LOGLEVEL_DEBUG >= stdout_level,
#                 False
#             ],
#             'DETAIL': [
#                 Logger.LOGLEVEL_DETAIL >= log_level,
#                 Logger.LOGLEVEL_DETAIL >= stdout_level,
#                 False
#             ]
#         }
#         self._shutdown = False
#         self.mutes = {}
#         self.collection = {
#             "ERROR": [],
#             "WARN": []
#         }
#
#         self._idle = False
#         if self.filelog is not None:
#             self.filelog.emit(
#                 logging.LogRecord(message='---[LOG STARTED]---')
#             )
#             self.filelog.emit(
#                 logging.LogRecord(message=header+time.strftime("  <%a %m/%d/%Y %I:%M:%S %p>"))
#             )
#
#     def log(self, message, sender="ANONYMOUS", channel="INFO"):
#         if not self._shutdown:
#             if sender not in self.mutes:
#                 formatted = "[%s] [%s] [%s] : %s" % (
#                     time.strftime("%a %m/%d/%Y %I:%M:%S %p"),
#                     channel,
#                     sender,
#                     message
#                 )
#                 print("Logging message:", formatted)
#                 self.logger.log(
#                     logging.INFO,
#                     formatted
#                 )
#                 if self.channels[channel][2]:
#                     self.collection[channel].append(formatted)
#             else:
#                 self.mutes[sender].append((message, channel))
#
#     def close(self):
#         if self._shutdown:
#             return
#         self.log(">>>>>Logger shutting down", sender="LOGGER", channel="INFO")
#         if self.filelog is not None:
#             for channel in sorted(self.collection):
#                 if len(self.collection[channel]):
#                     self.filelog.emit(
#                         logging.LogRecord(message=">>>>>Dump of channel "+channel)
#                     )
#                     for line in self.collection[channel]:
#                         self.filelog.emit(
#                             logging.LogRecord(message=line)
#                         )
#                     self.filelog.emit(
#                         logging.LogRecord(message='--------------------')
#                     )
#             self.log('---[LOG STOPPED]---', 'LOGGER', 'INFO')
#         self._shutdown = True
#         self.outlog.acquire()
#         try:
#             self.logger.removeHandler(self.outlog)
#             self.outlog.close()
#         finally:
#             self.outlog.release()
#         if self.filelog is not None:
#             self.filelog.acquire()
#             try:
#                 self.logger.remove(self.filelog)
#                 self.filelog.close()
#             finally:
#                 self.filelog.release()
#
#     def bindToSender(self, sender, can_close=True):
#
#         def output(message, channel="INFO"):
#             return self.log(message, sender, channel)
#
#         def _bindToSender(sender):
#             return self.bindToSender(sender, False)
#         output.bindToSender = _bindToSender
#         output.name = sender
#         output.close = self.close if can_close else lambda: None
#         return output
#
#     def setChannelFilters(self, channel, log, display):
#         collect = False if channel not in self.channels else (
#             self.channels[channel][2]
#         )
#         self.channels[channel] = [bool(log), bool(display), collect]
#
#     def setChannelCollection(self, channel, collect):
#         if channel in self.channels:
#             self.channels[channel][2] = bool(collect)
#             if collect and channel not in self.collection:
#                 self.collection[channel] = []
#             elif channel in self.collection and not collect:
#                 del self.collection[channel]
#
#     def mute(self, mutee, muter="ANONYMOUS"):
#         if mutee not in self.mutes:
#             self.mutes[mutee] = []
#             self.log(
#                 "Sender [%s] has been muted by [%s]" % (
#                     mutee,
#                     muter
#                 ),
#                 sender="LOGGER"
#             )
#
#     def unmute(self, mutee):
#         if mutee in self.mutes:
#             self.log("Sender [%s] has been unmuted" % mutee, sender="LOGGER")
#             if len(self.mutes[mutee]):
#                 (message, channel) = self.mutes[mutee][0]
#                 suppressed = len(self.mutes[mutee])-1
#                 del self.mutes[mutee]
#                 self.log(
#                     "%s <An additional %d messages were suppressed>" % (
#                         message,
#                         suppressed
#                     ),
#                     mutee,
#                     channel
#                 )
