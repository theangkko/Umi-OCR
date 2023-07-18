from utils.logger import GetLog
from utils.config import Config, RunModeFlag
from ocr.api_ppocr_json import OcrAPI
from ocr.engine_ram_optimization import OcrEngRam

import os
import time
import asyncio
import threading
from operator import eq
from enum import Enum

Log = GetLog()


class EngFlag(Enum):
    '''Engine Running Status Flag'''
    none = 0  # not in operation
    initing = 1  # Starting up.
    waiting = 2  # standby
    running = 3  # at work


class MsnFlag(Enum):
    '''Batch task status flags'''
    none = 0  # not in operation
    initing = 1  # Starting up.
    running = 2  # at work
    stopping = 3  # inactive


class OcrEngine:
    '''OCR engine with methods for various operations'''

    def __init__(self):
        # self.__initVar() # Can't use __initVar, can't call self.setEngFlag() because there's no guarantee that the main tk has started the event loop
        self.__ocrInfo = ()  # Record the previous OCR parameters
        self.__ramTips = ''  # Memory Usage Alert
        self.__runMissionLoop = None  # Event loop for batch recognition
        self.ocr = None  # OCR API Objects
        self.winSetRunning = None
        self.engFlag = EngFlag.none
        self.msnFlag = MsnFlag.none
        OcrEngRam.init(self.restart, self.getEngFlag, EngFlag)  # 内存优化·初始化，传入接口

    def __initVar(self):
        self.__ocrInfo = ()  # Record the previous OCR parameters
        self.__ramTips = ''  # Memory Usage Alert
        self.ocr = None  # OCR API Objects
        # self.msnFlag = MsnFlag.none # Task status can't be changed here, maybe the engine has shut down and the task thread is still going on

    def __setEngFlag(self, engFlag):
        '''Update engine status and notify main window'''
        self.engFlag = engFlag
        if self.ocr and Config.get('isDebug'):
            if engFlag == EngFlag.waiting:  # Refresh memory footprint
                self.__ramTips = f'（RAM)：{self.ocr.getRam()}MB）'
        msg = {
            EngFlag.none:  'Closed',
            EngFlag.initing:  'Starting up.',
            EngFlag.waiting:  f'standby{self.__ramTips}',
            EngFlag.running:  f'job{self.__ramTips}',
        }.get(engFlag, f'uncharted（{engFlag}）')
        isTkUpdate = False
        if engFlag == EngFlag.initing:  # On startup, refresh the UI
            isTkUpdate = True
        Config.set('ocrProcessStatus', msg, isTkUpdate)  # 设置
        # Log.info(f'引擎 ⇒ {engFlag}')

    def getEngFlag(self):
        return self.engFlag

    def __setMsnFlag(self, msnFlag):
        '''Update task status and notify the main window'''
        self.msnFlag = msnFlag
        if self.winSetRunning:
            self.winSetRunning(msnFlag)
        # Log.info(f'任务 ⇒ {msnFlag}')

    @staticmethod
    def __tryFunc(func, *e):
        '''Trying to execute func'''
        if func:
            try:
                func(*e)
            except Exception as e:
                errMsg = f'Call function {str(func)} exception: {e}'
                Log.error(errMsg)
                Config.main.panelOutput(errMsg+'\n')

    def start(self):
        '''Start the engine. If the engine has been started and the parameters have been updated, restart it.'''
        if self.engFlag == EngFlag.initing:  # Initialisation is in progress, repeat initialisation is strictly prohibited.
            return
        # Check Engine Path
        ocrToolPath = Config.get('ocrToolPath')
        if not os.path.isfile(ocrToolPath):
            raise Exception(
                f'Engine component not found in the following path \n [{ocrToolPath}]\n\nPlease place the engine component [PaddleOCR-json] folder in the specified path!')
        # Getting static parameters
        ang = ' -cls=1 -use_angle_cls=1' if Config.get('isOcrAngle') else ''
        limit = f" -limit_type={Config.get('ocrLimitMode').get(Config.get('ocrLimitModeName'),'min')} -limit_side_len={Config.get('ocrLimitSize')}"
        staticArgs = f"{ang}{limit}\
 -cpu_threads={Config.get('ocrCpuThreads')}\
 -enable_mkldnn={Config.get('isOcrMkldnn')}\
 {Config.get('argsStr')}"  # Static startup parameter string. Note the spaces in front of each parameter
        # Integration of the latest OCR parameters
        info = (
            ocrToolPath,  # Identifier Path
            Config.get('ocrConfig')[Config.get(
                'ocrConfigName')]['path'],  # Configuration file path
            staticArgs,  # priming parameter
        )
        isUpdate = not eq(info, self.__ocrInfo)  # Check for changes

        if self.ocr:  # OCR process started
            if not isUpdate:  # Holiday if no change
                return
            self.stop(True)  # A change stops the OCR process before starting it. Passing in T indicates that it is restarting without interrupting the task.

        self.__ocrInfo = info  # Record the parameters. Must come after stop() to avoid being overwritten.
        try:
            Log.info(f'Start the engine, parameters:{info}')
            self.__setEngFlag(EngFlag.initing)  # Notification in progress
            self.ocr = OcrAPI(*self.__ocrInfo, initTimeout=Config.get('ocrInitTimeout'))  # priming engine
            # Check that the engine has not been stopped during the time it was started.
            if not self.engFlag == EngFlag.initing:  # The status has been changed
                Log.info(f'After initialisation, the engine was called off!{self.engFlag}')
                self.stop()
                return
            self.__setEngFlag(EngFlag.waiting)  # Notification of standby
        except Exception as e:
            self.stop()
            raise

    def stop(self, isRestart=False):
        '''Terminate the engine immediately. isRE of T indicates that this is a restart without interrupting the task.'''
        if (self.msnFlag == MsnFlag.initing or self.msnFlag == MsnFlag.running)\
                and not self.engFlag == EngFlag.none and not isRestart:
            Log.info(f'Engine STOP, stop the task!')
            self.__setMsnFlag(MsnFlag.stopping)  # The mandate needs to be discontinued
        if hasattr(self.ocr, 'stop'):
            self.ocr.stop()
        del self.ocr
        self.ocr = None
        self.__setEngFlag(EngFlag.none)  # Notification of closure
        self.__initVar()

    def stopByMode(self):
        '''Decide whether to stop the engine based on the configuration mode'''
        if self.msnFlag == MsnFlag.initing or self.msnFlag == MsnFlag.running\
                and not self.engFlag == EngFlag.none:
            self.__setMsnFlag(MsnFlag.stopping)  # The mandate needs to be discontinued
        n = Config.get('ocrRunModeName')
        modeDict = Config.get('ocrRunMode')
        if n in modeDict.keys():
            mode = modeDict[n]
            if mode == RunModeFlag.short:  # close on demand
                self.stop()

    def restart(self):
        '''Restart the engine and free up memory'''
        self.stop(True)
        self.start()

    def run(self, path):
        '''Perform single image recognition, enter path, return dictionary'''
        if not self.ocr:
            self.__setEngFlag(EngFlag.none)  # Notification of closure
            return {'code': 404, 'data': f'The engine is not running.'}
        OcrEngRam.runBefore(ram=self.ocr.getRam())  # 内存优化·前段
        self.__setEngFlag(EngFlag.running)  # Notify Job
        data = self.ocr.run(path)
        # It is possible that the engine is shut down due to stopping the task or shutting down the software early, and OCR.run produces the result early.
        # At this time, engFlag has been set to none by the main thread, if it is set to waiting again, it may lead to bugs.
        # So check if it's still running in normal state, and notify standby if there's no problem.
        if self.engFlag == EngFlag.running:
            self.__setEngFlag(EngFlag.waiting)  # 通知standby
        OcrEngRam.runAfter()  # 内存优化·后段
        return data

    def runMission(self, paths, msn):
        '''Batch recognition of multiple images, asynchronous. If the engine is not started, it is started automatically.\n
        paths: trails\n
        msn:   Tasker object, a derived class of Msn, must contain the onStart|onGet|onStop|onError methods.'''
        if not self.msnFlag == MsnFlag.none:  # 正在运行
            Log.error(f'The next round of missions was started before the existing missions were completed')
            raise Exception('Mandate outstanding')

        self.winSetRunning = Config.main.setRunning  # Setting the Operational Status Interface
        self.__setMsnFlag(MsnFlag.initing)  # Set task initialization

        def runLoop():  # Start event loop
            asyncio.set_event_loop(self.__runMissionLoop)
            self.__runMissionLoop.run_forever()

        # Create an event loop in the current thread
        self.__runMissionLoop = asyncio.new_event_loop()
        # Open a new thread and start the event loop in the new thread
        threading.Thread(target=runLoop).start()
        # The event loop keeps wandering in a new thread.
        asyncio.run_coroutine_threadsafe(self.__runMission(
            paths, msn
        ), self.__runMissionLoop)

    async def __runMission(self, paths, msn):
        '''新线程中批量识图。在这个线程里更新UI是安全的。'''

        num = {
            'all': len(paths),  # Total number
            'now': 1,  # Current processing number
            'index': 0,  # 当前下标
            'succ': 0,  # 成功个数
            'err': 0,  # 失败个数
            'exist': 0,  # 成功里面有文字的个数
            'none': 0,  # 成功里面无文字的个数
            'time': 0,  # 执行至今的总时间
            'timeNow': 0,  # 这一轮的耗时
        }

        def close():  # 停止
            try:
                self.__runMissionLoop.stop()  # Closing the asynchronous event loop
            except Exception as e:
                Log.error(f'Task Thread Failed to close the task event loop:{e}')
            self.stopByMode()  # 按需关闭OCR进程
            self.__tryFunc(msn.onStop, num)
            self.__setMsnFlag(MsnFlag.none)  # 设任务停止
            Log.info(f'Task close!')

        # Start OCR engine, batch task initialisation =========================
        try:
            self.start()  # 启动或刷新引擎
        except Exception as e:
            Log.error(f'The batch task startup engine failed:{e}')
            self.__tryFunc(msn.onError, num, f"Can't start the engine:{e}")
            close()
            return
        timeStart = time.time()  # start-up time
        timeLast = timeStart  # End of previous round

        # Check that the task has not been called off during the time it took to start the engine =========================
        if self.msnFlag == MsnFlag.stopping:  # 需要停止
            close()
            return
        # Main window UI and task processor initialization=========================
        self.__setMsnFlag(MsnFlag.running)  # 设任务运行
        self.__tryFunc(msn.onStart, num)

        # Formal commencement of the mission =========================
        for path in paths:
            if self.msnFlag == MsnFlag.stopping:  # 需要停止
                close()
                return
            isAddErr = False
            try:
                data = self.run(path)  # 调用图片识别
                # 刷新时间
                timeNow = time.time()  # 本轮结束时间
                num['time'] = timeNow-timeStart
                num['timeNow'] = timeNow-timeLast
                timeLast = timeNow
                # 刷新量
                if data['code'] == 100:
                    num['succ'] += 1
                    num['exist'] += 1
                elif data['code'] == 101:
                    num['succ'] += 1
                    num['none'] += 1
                else:
                    num['err'] += 1
                    isAddErr = True
                    # If you set the process to shut down on demand, stopping the task in the middle of the process will cause the process to kill and the current identification will fail.
                    # If the process is set to be resident in the background, stopping the task in the middle of the process will cause the process to kill and stop the task after the current identification.
                    # All of this is normal (by design)
                    # However, it is not normal for an engine process to shut down unexpectedly and cause the image to fail; therefore, engFlag is not detected.
                    if self.msnFlag == MsnFlag.stopping:  # Failure caused by forced engine stop
                        data['data'] = 'This is a normal situation. Stopping the task and shutting down the engine in the middle of the process caused this image to not be recognised all the way through.'
                # 调用取得事件
                self.__tryFunc(msn.onGet, num, data)
            except Exception as e:
                Log.error(f'Task thread OCR failed: {e}')
                if not isAddErr:
                    num['err'] += 1
                continue
            finally:
                num['now'] += 1
                num['index'] += 1

        close()


OCRe = OcrEngine()  # engine singleton 
