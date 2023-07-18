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
    stopping = 3  # 停止中


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
        if engFlag == EngFlag.initing:  # 启动中，刷新一下UI
            isTkUpdate = True
        Config.set('ocrProcessStatus', msg, isTkUpdate)  # 设置
        # Log.info(f'引擎 ⇒ {engFlag}')

    def getEngFlag(self):
        return self.engFlag

    def __setMsnFlag(self, msnFlag):
        '''更新任务状态并向主窗口通知'''
        self.msnFlag = msnFlag
        if self.winSetRunning:
            self.winSetRunning(msnFlag)
        # Log.info(f'任务 ⇒ {msnFlag}')

    @staticmethod
    def __tryFunc(func, *e):
        '''尝试执行func'''
        if func:
            try:
                func(*e)
            except Exception as e:
                errMsg = f'Call function {str(func)} exception: {e}'
                Log.error(errMsg)
                Config.main.panelOutput(errMsg+'\n')

    def start(self):
        '''启动引擎。若引擎已启动，且参数有更新，则重启。'''
        if self.engFlag == EngFlag.initing:  # 正在初始化中，严禁重复初始化
            return
        # 检查引擎路径
        ocrToolPath = Config.get('ocrToolPath')
        if not os.path.isfile(ocrToolPath):
            raise Exception(
                f'Engine component not found in the following path \n [{ocrToolPath}]\n\nPlease place the engine component [PaddleOCR-json] folder in the specified path!')
        # 获取静态参数
        ang = ' -cls=1 -use_angle_cls=1' if Config.get('isOcrAngle') else ''
        limit = f" -limit_type={Config.get('ocrLimitMode').get(Config.get('ocrLimitModeName'),'min')} -limit_side_len={Config.get('ocrLimitSize')}"
        staticArgs = f"{ang}{limit}\
 -cpu_threads={Config.get('ocrCpuThreads')}\
 -enable_mkldnn={Config.get('isOcrMkldnn')}\
 {Config.get('argsStr')}"  # 静态启动参数字符串。注意每个参数前面的空格
        # 整合最新OCR参数
        info = (
            ocrToolPath,  # 识别器路径
            Config.get('ocrConfig')[Config.get(
                'ocrConfigName')]['path'],  # 配置文件路径
            staticArgs,  # 启动参数
        )
        isUpdate = not eq(info, self.__ocrInfo)  # 检查是否有变化

        if self.ocr:  # OCR进程已启动
            if not isUpdate:  # 无变化则放假
                return
            self.stop(True)  # 有变化则先停止OCR进程再启动。传入T表示是在重启，无需中断任务。

        self.__ocrInfo = info  # 记录参数。必须在stop()之后，以免被覆盖。
        try:
            Log.info(f'Start the engine, parameters:{info}')
            self.__setEngFlag(EngFlag.initing)  # 通知启动中
            self.ocr = OcrAPI(*self.__ocrInfo, initTimeout=Config.get('ocrInitTimeout'))  # 启动引擎
            # 检查启动引擎这段时间里，引擎有没有被叫停
            if not self.engFlag == EngFlag.initing:  # 状态被改变过了
                Log.info(f'After initialisation, the engine was called off!{self.engFlag}')
                self.stop()
                return
            self.__setEngFlag(EngFlag.waiting)  # 通知standby
        except Exception as e:
            self.stop()
            raise

    def stop(self, isRestart=False):
        '''立刻终止引擎。isRE为T时表示这是在重启，无需中断任务。'''
        if (self.msnFlag == MsnFlag.initing or self.msnFlag == MsnFlag.running)\
                and not self.engFlag == EngFlag.none and not isRestart:
            Log.info(f'Engine STOP, stop the task!')
            self.__setMsnFlag(MsnFlag.stopping)  # 设任务需要停止
        if hasattr(self.ocr, 'stop'):
            self.ocr.stop()
        del self.ocr
        self.ocr = None
        self.__setEngFlag(EngFlag.none)  # 通知关闭
        self.__initVar()

    def stopByMode(self):
        '''根据配置模式决定是否停止引擎'''
        if self.msnFlag == MsnFlag.initing or self.msnFlag == MsnFlag.running\
                and not self.engFlag == EngFlag.none:
            self.__setMsnFlag(MsnFlag.stopping)  # 设任务需要停止
        n = Config.get('ocrRunModeName')
        modeDict = Config.get('ocrRunMode')
        if n in modeDict.keys():
            mode = modeDict[n]
            if mode == RunModeFlag.short:  # 按需关闭
                self.stop()

    def restart(self):
        '''重启引擎，释放内存'''
        self.stop(True)
        self.start()

    def run(self, path):
        '''执行单张图片识别，输入路径，返回字典'''
        if not self.ocr:
            self.__setEngFlag(EngFlag.none)  # 通知关闭
            return {'code': 404, 'data': f'The engine is not running.'}
        OcrEngRam.runBefore(ram=self.ocr.getRam())  # 内存优化·前段
        self.__setEngFlag(EngFlag.running)  # 通知job
        data = self.ocr.run(path)
        # 有可能因为提早停止任务或关闭软件，引擎被关闭，OCR.run提前出结果
        # 此时 engFlag 已经被主线程设为 none，如果再设waiting可能导致bug
        # 所以检测一下是否还是正常的状态 running ，没问题才通知standby
        if self.engFlag == EngFlag.running:
            self.__setEngFlag(EngFlag.waiting)  # 通知standby
        OcrEngRam.runAfter()  # 内存优化·后段
        return data

    def runMission(self, paths, msn):
        '''批量识别多张图片，异步。若引擎未启动，则自动启动。\n
        paths: 路径\n
        msn:   任务器对象，Msn的派生类，必须含有 onStart|onGet|onStop|onError 四个方法'''
        if not self.msnFlag == MsnFlag.none:  # 正在运行
            Log.error(f'The next round of missions was started before the existing missions were completed')
            raise Exception('Mandate outstanding')

        self.winSetRunning = Config.main.setRunning  # 设置运行状态接口
        self.__setMsnFlag(MsnFlag.initing)  # 设任务初始化

        def runLoop():  # 启动事件循环
            asyncio.set_event_loop(self.__runMissionLoop)
            self.__runMissionLoop.run_forever()

        # Create an event loop in the current thread
        self.__runMissionLoop = asyncio.new_event_loop()
        # 开启新的线程，在新线程中启动事件循环
        threading.Thread(target=runLoop).start()
        # 在新线程中事件循环不断游走执行
        asyncio.run_coroutine_threadsafe(self.__runMission(
            paths, msn
        ), self.__runMissionLoop)

    async def __runMission(self, paths, msn):
        '''新线程中批量识图。在这个线程里更新UI是安全的。'''

        num = {
            'all': len(paths),  # 全部数量
            'now': 1,  # 当前处理序号
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
                self.__runMissionLoop.stop()  # 关闭异步事件循环
            except Exception as e:
                Log.error(f'Task Thread Failed to close the task event loop:{e}')
            self.stopByMode()  # 按需关闭OCR进程
            self.__tryFunc(msn.onStop, num)
            self.__setMsnFlag(MsnFlag.none)  # 设任务停止
            Log.info(f'Task close!')

        # 启动OCR引擎，批量任务初始化 =========================
        try:
            self.start()  # 启动或刷新引擎
        except Exception as e:
            Log.error(f'The batch task startup engine failed:{e}')
            self.__tryFunc(msn.onError, num, f"Can't start the engine:{e}")
            close()
            return
        timeStart = time.time()  # 启动时间
        timeLast = timeStart  # 上一轮结束时间

        # 检查启动引擎这段时间里，任务有没有被叫停 =========================
        if self.msnFlag == MsnFlag.stopping:  # 需要停止
            close()
            return
        # 主窗UI和任务处理器初始化 =========================
        self.__setMsnFlag(MsnFlag.running)  # 设任务运行
        self.__tryFunc(msn.onStart, num)

        # 正式开始任务 =========================
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
                    # 若设置了进程按需关闭，中途停止任务会导致进程kill，本次识别失败
                    # 若设置了进程后台常驻，中途停止任务会让本次识别完再停止任务
                    # 这些都是正常的（设计中的）
                    # 但是，引擎进程意外关闭导致图片识别失败，则是不正常的；所以不检测engFlag
                    if self.msnFlag == MsnFlag.stopping:  # 失败由强制停止引擎导致引起
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


OCRe = OcrEngine()  # 引擎单例
