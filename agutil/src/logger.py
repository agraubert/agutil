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
    def __init__(self, filename, log_level=Logger.LOGLEVEL_INFO, stdout_level=Logger.LOGLEVEL_NONE):
        self.logfile = filename
        self.channels = {
            'ERROR' : [
                Logger.LOGLEVEL_ERRORS <= log_level,
                Logger.LOGLEVEL_ERRORS <= stdout_level
            ],
            'WARN' : [
                Logger.LOGLEVEL_WARN <= log_level,
                Logger.LOGLEVEL_WARN <= stdout_level
            ],
            'INFO' : [
                Logger.LOGLEVEL_INFO <= log_level,
                Logger.LOGLEVEL_INFO <= stdout_level
            ],
            'DEBUG' : [
                Logger.LOGLEVEL_DEBUG <= log_level,
                Logger.LOGLEVEL_DEBUG <= stdout_level
            ],
            'DETAIL' : [
                Logger.LOGLEVEL_ALL <= log_level,
                Logger.LOGLEVEL_ALL <= stdout_level
            ]
        }
        self._shutdown = False
        self.logqueue = []
        self.logwriter = None
        self._logger = threading.Thread() # a Thread!
        self._logger.start()

    def log(self, message, channel="INFO", sender="ANONYMOUS"):
        self.logqueue.append((channel, sender, message))

    def _logger_worker(self):
        while not self._shutdown:
            if len(self.logqueue):
                msg_data = self.logqueue.pop(0)
                if msg_data[0] in self.channels:
                    formatted = False
                    if self.channels[msg_data[0]][0]:
                        formatted = "[%s] [%s] [%s] : %s" %(
                            time.strftime("[%a %m/%d/%Y %I:%M:%S %p]"),
                            *msg_data
                        )
                        #Write to file
                    if self.channels[msg_data[0]][1]:
                        if not formatted:
                            formatted = "[%s] [%s] [%s] : %s" %(
                                time.strftime("[%a %m/%d/%Y %I:%M:%S %p]"),
                                *msg_data
                            )
                        #Print to stdout
