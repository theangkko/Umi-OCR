import logging

LogName = 'Umi-OCR_log'
LogFileName = 'Umi-OCR_debug.log'


class Logger:

    def __init__(self):
        self.initLogger()

    def initLogger(self):
        '''Initialisation log'''

        # 日志
        self.logger = logging.getLogger(LogName)
        self.logger.setLevel(logging.DEBUG)

        # 控制台
        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(logging.DEBUG)
        formatPrint = logging.Formatter(
            '【%(levelname)s】 %(message)s')
        streamHandler.setFormatter(formatPrint)
        # self.logger.addHandler(streamHandler)

        return
        # log file
        fileHandler = logging.FileHandler(LogFileName)
        fileHandler.setLevel(logging.ERROR)
        formatFile = logging.Formatter(
            '''
【%(levelname)s】 %(asctime)s
%(message)s
    papers：%(module)s | function：%(funcName)s | line number：%(lineno)d
    threads id：%(thread)d | thread name：%(thread)s''')
        fileHandler.setFormatter(formatFile)
        self.logger.addHandler(fileHandler)


LOG = Logger()


def GetLog():
    return LOG.logger
