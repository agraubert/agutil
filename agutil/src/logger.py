import threading
import time
#Timestamp format: "[%a %m/%d/%Y %I:%M:%S %p]"

class Logger:
    LOGLEVEL_NONE = 0
    LOGLEVEL_ERRORS = 1
    LOGLEVEL_WARN = 2
    LOGLEVEL_INFO = 3
    LOGLEVEL_DEBUG = 4
    LOGLEVEL_ALL = 5
    def __init__(self, filename, header="Agutil Logger", log_level=LOGLEVEL_INFO, stdout_level=LOGLEVEL_NONE):
        self.logfile = filename
        self.unknown_channel = False
        self.channels = {
            'ERROR' : [
                Logger.LOGLEVEL_ERRORS <= log_level,
                Logger.LOGLEVEL_ERRORS <= stdout_level,
                True
            ],
            'WARN' : [
                Logger.LOGLEVEL_WARN <= log_level,
                Logger.LOGLEVEL_WARN <= stdout_level,
                True
            ],
            'INFO' : [
                Logger.LOGLEVEL_INFO <= log_level,
                Logger.LOGLEVEL_INFO <= stdout_level,
                False
            ],
            'DEBUG' : [
                Logger.LOGLEVEL_DEBUG <= log_level,
                Logger.LOGLEVEL_DEBUG <= stdout_level,
                False
            ],
            'DETAIL' : [
                Logger.LOGLEVEL_ALL <= log_level,
                Logger.LOGLEVEL_ALL <= stdout_level,
                False
            ]
        }
        self._shutdown = False
        self.mutes = {}
        self.collection = {}
        self.logqueue = []
        self.idlelock = threading.Condition()
        self._idle = False
        if self.logfile != None:
            self.logwriter = open(filename, mode='w')
            self.logwriter.write('---[LOG STARTED]---\n')
            self.logwriter.write(header+time.strftime("%a %m/%d/%Y %I:%M:%S %p\n"))
        self._logger = threading.Thread() # a Thread!
        self._logger.start()

    def log(self, message, channel="INFO", sender="ANONYMOUS"):
        if not self._shutdown:
            if sender not in self.mutes:
                self.logqueue.append((channel, sender, message))
                if self._idle:
                    self.idlelock.acquire()
                    self._idle = False
                    self.idlelock.notify_all()
                    self.idlelock.release()
            else:
                self.mutes[sender].append((message, channel))

    def setUnknownChannelBehavior(self, allow):
        self.unknown_channel = allow

    def setChannelFilters(self, channel, log, display):
        collect = False if channel not in self.channels else self.channels[channel][2]
        self.channels[channel] = [bool(log), bool(display), collect]

    def setChannelCollection(self, channel, collect):
        if channel in self.channels:
            self.channels[channel][2] = bool(collect)
            if collect and channel not in self.collection:
                self.collection[channel] = []
            elif channel in self.collection and not collect:
                del self.collection[channel]

    def mute(self, muter, mutee):
        if mutee not in self.mutes:
            self.mutes[mutee] = []
            self.log("Sender [%s] has been muted by [%s]" %(mutee, muter), sender="LOGGER")

    def unmute(self, mutee):
        if mutee in self.mutes:
            if len(self.mutes[mutee]):
                (message, channel) = self.mutes[mutee][0]
                suppressed = len(self.mutes[mutee])-1
                del self.mutes[mutee]
                self.log(message+" <An additional %d messages were suppressed>" % suppressed, channel, mutee)
            self.log("Sender [%s] has been unmuted" %mutee, sender="LOGGER")

    def _logger_worker(self):
        while not self._shutdown:
            if len(self.logqueue):
                msg_data = self.logqueue.pop(0)
                if msg_data[0] in self.channels or self.unknown_channel:
                    formatted = False
                    if self.channels[msg_data[0]][0] and self.logfile:
                        formatted = "[%s] [%s] [%s] : %s" %(
                            time.strftime("[%a %m/%d/%Y %I:%M:%S %p]"),
                            *msg_data
                        )
                        self.logwriter.write(formatted+"\n")
                        self.logwriter.flush()
                    if self.channels[msg_data[0]][1]:
                        if not formatted:
                            formatted = "[%s] [%s] [%s] : %s" %(
                                time.strftime("[%a %m/%d/%Y %I:%M:%S %p]"),
                                *msg_data
                            )
                        print(formatted)
                    if self.channels[msg_data[0]][2]:
                        self.collection[msg_data[0]].append(formatted)
            elif self._idle:
                self.idlelock.acquire()
                self.idlelock.wait(timeout=.1)
                self.idlelock.release()
            else:
                self.idlelock.acquire()
                self._idle = True
                self.idlelock.wait(timeout=.05)
                self.idlelock.release()
        self.logwriter.write(time.strftime(">>>>>Logging queue closed: %a %m/%d/%Y %I:%M:%S %p\n"))
        while len(self.logqueue):
            msg_data = self.logqueue.pop(0)
            if msg_data[0] in self.channels:
                formatted = False
                if self.channels[msg_data[0]][0] and self.logfile:
                    formatted = "[%s] [%s] [%s] : %s" %(
                        time.strftime("[%a %m/%d/%Y %I:%M:%S %p]"),
                        *msg_data
                    )
                    self.logwriter.write(formatted+"\n")
                if self.channels[msg_data[0]][1]:
                    if not formatted:
                        formatted = "[%s] [%s] [%s] : %s" %(
                            time.strftime("[%a %m/%d/%Y %I:%M:%S %p]"),
                            *msg_data
                        )
                    print(formatted)
                if self.channels[msg_data[0]][2]:
                    self.collection[msg_data[0]].append(formatted)
        if self.logfile:
            self.logwriter.write("\n\n")
            for channel in self.collection:
                self.logwriter.write(">>>>>Dump of channel %s\n"%channel)
                for line in self.collection[channel]:
                    self.logwriter.write(line+'\n')
                self.logwriter.write("--------------------\n\n")
                self.logwriter.flush()
            self.logwriter.write('---[LOG STOPPED]---')
