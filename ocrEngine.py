import time
from operator import eq
from config import Config
from ocrAPI import OcrAPI

# TODO：目前这个类是线程不安全的，也是我想把OCR子线程常驻后台的阻碍


class OcrEngine:
    """OCR引擎，含各种操作的方法"""

    def __initVar(self):
        self.ocr = None  # OCR API对象
        self.ocrInfo = ()  # OCR参数
        self.noticeStatus(0)  # 通知关闭

    def __init__(self):
        self.__initVar()

    def noticeStatus(self, status):
        """通知进程运行状态"""
        msg = {
            0:  "已关闭",
            1:  "正在启动",
            2:  "待命",
            3:  "工作",
        }.get(status, f"未知（{status}）")
        isTkUpdate = False
        if status == 1:
            isTkUpdate = True
        Config.set("ocrProcessStatus", msg, isTkUpdate)  # 设置
        print(f'状态：{status} {msg}')

    def start(self):
        """启动引擎。若引擎已启动，且参数有更新，则重启。"""
        def updateOcrInfo():  # 更新OCR参数。若有更新(与当前不同)，返回True
            info = (
                Config.get("ocrToolPath"),  # 识别器路径
                Config.get("ocrConfig")[Config.get(
                    "ocrConfigName")]['path'],  # 配置文件路径
                Config.get("argsStr"),  # 启动参数
            )
            isUpdate = not eq(info, self.ocrInfo)
            if isUpdate:
                self.ocrInfo = info
            return isUpdate
        isUpdate = updateOcrInfo()
        if self.ocr:  # 已启动
            if not isUpdate:  # 无更新则放假
                return
            self.stop()  # 有更新则先停止OCR进程再启动
        self.noticeStatus(1)  # 通知启动中
        try:
            self.ocr = OcrAPI(*self.ocrInfo)  # 启动引擎
            self.noticeStatus(2)  # 通知待命
        except Exception as e:
            self.stop()
            raise

    def stop(self):
        """立刻终止引擎"""
        if hasattr(self.ocr, 'stop'):
            self.ocr.stop()
        del self.ocr
        self.__initVar()

    def stopByMode(self):
        """根据配置决定停止引擎"""
        n = Config.get('ocrRunModeName')
        modeDict = Config.get('ocrRunMode')
        if n in modeDict.keys():
            mode = modeDict[n]
            print(f'引擎停止策略：{mode}')
            if mode == 0:  # 按需关闭
                self.stop()

    def run(self, path):
        if not self.ocr:
            self.noticeStatus(0)  # 通知关闭
            return {'code': 404, 'data': f'引擎未在运行'}
        self.noticeStatus(3)  # 通知工作
        data = self.ocr.run(path)
        self.noticeStatus(2)  # 通知待命
        return data


OCRe = OcrEngine()  # 引擎单例