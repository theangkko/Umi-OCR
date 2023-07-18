# Base class for outputters. Outputs incoming text to the specified place in the specified format.

from utils.logger import GetLog

import os

Log = GetLog()


class Output:
    def __init__(self):
        self.outputPath = ''  # output path

    def print(self, text):
        '''Direct Text Output'''
        Log.info(f'exports: {text}')

    def openOutputFile(self):
        '''Open output file (folder)'''
        if self.outputPath and os.path.exists(self.outputPath):
            os.startfile(self.outputPath)
