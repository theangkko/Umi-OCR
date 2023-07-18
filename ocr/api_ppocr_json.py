# Calling the PaddleOCR-json.exe Python Api
# Project home page:
# https://github.com/hiroi-sora/PaddleOCR-json


import os
import atexit  # Withdrawal processing
import threading
import subprocess  # Processes, Pipes
from psutil import Process as psutilProcess  # Memory Monitoring
from sys import platform as sysPlatform  # popen静默模式
from json import loads as jsonLoads, dumps as jsonDumps

class OcrAPI:
    """Calling OCR"""

    def __init__(self, exePath, configPath="", argsStr="", initTimeout=20):
        """Initialize the recognizer. \n
        :exePath: Path to the recognizer `PaddleOCR_json.exe`. \n
        :configPath: Path to configuration file `PaddleOCR_json_config_XXXX.txt`. \n
        :argument: Startup argument, string. See \n for parameter description
        :initTimeout: Initialization timeout, seconds \n
        `https://github.com/hiroi-sora/PaddleOCR-json#5-%E9%85%8D%E7%BD%AE%E4%BF%A1%E6%81%AF%E8%AF%B4%E6%98%8E`\n
        """
        cwd = os.path.abspath(os.path.join(exePath, os.pardir))  # 获取exe父文件夹
        # Handling startup parameters
        args = ' '
        if argsStr:  # Add user-specified startup parameters
            args += f' {argsStr}'
        if configPath and 'config_path' not in args:  # Specifying configuration files
            args += f' --config_path="{configPath}"'
        if 'use_debug' not in args:  # Turn off debug mod
            args += ' --use_debug=0'
        # Set the child process to enable silent mode and not show the console window
        startupinfo = None
        if 'win32' in str(sysPlatform).lower():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        self.ret = subprocess.Popen(  # 打开管道
            exePath+args, cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            startupinfo=startupinfo  # 开启静默模式
        )
        atexit.register(self.stop)  # Performs a forced stop of the child process when the registered program terminates
        self.psutilProcess = psutilProcess(self.ret.pid)  # 进程监控对象

        self.initErrorMsg = f'OCR init fail.\nEngine Path:{exePath}\nStartup Parameters:{args}'

        # Subthread check timeout
        def cancelTimeout():
            checkTimer.cancel()

        def checkTimeout():
            self.initErrorMsg = f'OCR init timeout: {initTimeout}s.\n{exePath}'
            self.ret.kill()  # 关闭子进程
        checkTimer = threading.Timer(initTimeout, checkTimeout)
        checkTimer.start()

        # Cycle through the reads, checking for success flags
        while True:
            if not self.ret.poll() == None:  # 子进程已退出，初始化失败
                cancelTimeout()
                raise Exception(self.initErrorMsg)
            # 必须按行读，所以不能使用communicate()来规避超时问题
            initStr = self.ret.stdout.readline().decode('ascii', errors='ignore')
            if 'OCR init completed.' in initStr:  # 初始化成功
                break
        cancelTimeout()

    def run(self, imgPath):
        """Text recognition for a picture. \n
        :exePath: Path of the image. \n
        :return: {'code': Recognition code, 'data': Content list or error message string}\n """
        if not self.ret.poll() == None:
            return {'code': 400, 'data': f'The subprocess is terminated.'}
        # wirteStr = imgPath if imgPath[-1] == '\n' else imgPath + '\n'
        writeDict = {'image_dir': imgPath}
        try:  # 输入地址转为ascii转义的json字符串，规避编码问题
            wirteStr = jsonDumps(
                writeDict, ensure_ascii=True, indent=None)+"\n"
        except Exception as e:
            return {'code': 403, 'data': f'Input dictionary to json failed. Dictionary:{writeDict} || report an error：[{e}]'}
        # 输入路径
        try:
            self.ret.stdin.write(wirteStr.encode('ascii'))
            self.ret.stdin.flush()
        except Exception as e:
            return {'code': 400, 'data': f'Failed to write image address to recogniser process, suspected child process has crashed.{e}'}
        if imgPath[-1] == '\n':
            imgPath = imgPath[:-1]
        # 获取返回值
        try:
            getStr = self.ret.stdout.readline().decode('utf-8', errors='ignore')
        except Exception as e:
            return {'code': 401, 'data': f'Failed to read the output of the recogniser process, suspected to have passed in a non-existent or unrecognisable image \"{imgPath}\" 。{e}'}
        try:
            return jsonLoads(getStr)
        except Exception as e:
            return {'code': 402, 'data': f'Failed to deserialise JSON from recogniser output value, suspected to be passing in non-existent or unrecognisable images \"{imgPath}\" . Exception message: {e}. Original content：{getStr}'}

    def stop(self):
        self.ret.kill()  # Shut down the child process. Mistakenly repeating a call doesn't seem to have a bad effect

    def getRam(self):
        """Returns the memory footprint, in numbers, in MB"""
        try:
            return int(self.psutilProcess.memory_info().rss/1048576)
        except Exception as e:
            return -1

    def __del__(self):
        self.stop()
        atexit.unregister(self.stop)  # Remove exit processing
