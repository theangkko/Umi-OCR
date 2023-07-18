# Batch Path Task Processor

from utils.config import Config
from ui.win_notify import Notify  # notification pop-up
from ocr.engine import MsnFlag
from ocr.msn import Msn
# exporter
from ocr.output_panel import OutputPanel
from ocr.output_txt import OutputTxt
from ocr.output_separate_txt import OutputSeparateTxt
from ocr.output_md import OutputMD
from ocr.output_jsonl import OutputJsonl
# text block processor
from ocr.tbpu.ignore_area import TbpuIgnoreArea

import time
import os

from utils.logger import GetLog
Log = GetLog()


class MsnBatch(Msn):

    # __init__ 在主线程内初始化，其余方法在子线程内被调用
    def __init__(self):
        # 获取接口
        self.progressbar = Config.main.progressbar  # 进度条组件
        self.batList = Config.main.batList  # 图片列表
        self.setTableItem = Config.main.setTableItem  # 设置主表接口
        self.setRunning = Config.main.setRunning  # 设置运行状态接口
        self.clearTableItem = Config.main.clearTableItem  # 清理主表接口
        # 获取值
        self.isDebug = Config.get('isDebug')  # 是否输出调试
        self.isIgnoreNoText = Config.get("isIgnoreNoText")  # 是否忽略无字图片
        self.areaInfo = Config.get("ignoreArea")  # 忽略区域
        self.ocrToolPath = Config.get("ocrToolPath")  # 识别器路径
        self.configPath = Config.get("ocrConfig")[Config.get(  # 配置文件路径
            "ocrConfigName")]['path']
        self.argsStr = Config.get("argsStr")  # 启动参数
        # 初始化输出器
        outputPanel = OutputPanel()  # 输出到面板
        self.outputList = [outputPanel]
        if Config.get("isOutputTxt"):  # 输出到txt
            self.outputList.append(OutputTxt())
        if Config.get("isOutputMD"):  # 输出到markdown
            self.outputList.append(OutputMD())
        if Config.get("isOutputJsonl"):  # 输出到jsonl
            self.outputList.append(OutputJsonl())
        if Config.get("isOutputSeparateTxt"):  # 输出到单独txt
            self.outputList.append(OutputSeparateTxt())
        # 初始化文块处理器
        self.procList = []
        if Config.get("ignoreArea"):  # 忽略区域
            self.procList.append(TbpuIgnoreArea())
        tbpuClass = Config.get('tbpu').get(  # 其它文本块处理器
            Config.get('tbpuName'), None)
        if tbpuClass:
            self.procList.append(tbpuClass())

        Log.info(f'The batch text processor is initialised!')

    def __output(self,  type_, *data):  # output string
        ''' type_ Optional value:
        none ：No modification
        img ：Image result
        text ：text
        debug ：Debug information
        '''
        for output in self.outputList:
            if type_ == 'none':
                output.print(*data)
            elif type_ == 'img':
                output.img(*data)
            elif type_ == 'text':
                output.text(*data)
            elif type_ == 'debug':
                output.debug(*data)

    def onStart(self, num):
        Log.info('msnB: onStart')
        # 重置进度提示
        self.progressbar["maximum"] = num['all']
        self.progressbar["value"] = 0
        Config.set('tipsTop1', f'0s  0/{num["all"]}')
        Config.set('tipsTop2', f'0%')
        Config.main.win.update()  # 刷新进度
        self.clearTableItem()  # 清空表格参数
        # 输出初始信息
        startStr = f"\nTask start time:{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}\n\n"
        self.__output('text', startStr)
        # 输出各个文块处理器的debug信息
        if self.isDebug:
            debugStr = f'Output debugging information is enabled. \n engine path:[{self.ocrToolPath}]\nConfiguration file path:[{self.configPath}]\n启动参数：[{self.argsStr}]\n'
            if self.procList:
                for proc in self.procList:
                    debugStr += proc.getInitInfo()
                debugStr += '\n'
            else:
                debugStr += 'No text block post-processing added\n'
            self.__output('debug', debugStr)
        self.setRunning(MsnFlag.running)

    def onGet(self, numData, ocrData):
        # ==================== analysis block ====================
        textBlockList = []  # List of text blocks
        textDebug = ''  # 调试信息
        textScore = ''  # 置信度信息
        imgInfo = self.batList.get(index=numData['index'])  # Get picture information
        flagNoOut = False
        if ocrData['code'] == 100:  # 成功
            textBlockList = ocrData['data']  # 获取文块
            # 将文块组导入每一个文块处理器，获取输出文块组
            for proc in self.procList:
                textBlockList, textD = proc.run(textBlockList, imgInfo)
                if textD:
                    textDebug += f'{textD}\n'
            if textBlockList:  # 结果有文字
                # 计算置信度
                score = 0
                scoreNum = 0
                for tb in textBlockList:
                    score += tb['score']
                    scoreNum += 1
                if scoreNum > 0:
                    score /= scoreNum
                textScore = str(score)
                textDebug += f'total time consumption：{numData["timeNow"]}s  confidence level ：{textScore}\n'
            else:
                textScore = '无文字'
                textDebug += f'total time consumption：{numData["timeNow"]}s  All text ignored\n'
                flagNoOut = True
        elif ocrData['code'] == 101:  # 无文字
            textScore = '无文字'
            textDebug += f'total time consumption：{numData["timeNow"]}s  图中未发现文字\n'
            flagNoOut = True
        else:  # Error message recognition failure
            # 将错误信息写入第一个文块
            textBlockList = [{'box': [0, 0, 0, 0, 0, 0, 0, 0], 'score': 0,
                              'text':f'Error message recognition failure，error code：{ocrData["code"]}\nerror message：{str(ocrData["data"])}\n'}]
            textDebug += f'total time consumption：{numData["timeNow"]}s  Error message recognition failure\n'
            textScore = '错误'
        # ==================== 输出 ====================
        if self.isIgnoreNoText and flagNoOut:
            pass  # 设置了不输出无文字的图片
        else:
            Log.info(textDebug)
            self.__output('img', textBlockList, imgInfo, numData, textDebug)
        # ==================== 刷新UI ====================
        # 刷新进度
        self.progressbar["value"] = numData['now']
        Config.set(
            'tipsTop2', f'{round((numData["now"]/numData["all"])*100)}%')
        Config.set(
            'tipsTop1', f'{round(numData["time"], 2)}s  {numData["now"]}/{numData["all"]}')
        # 刷新表格
        self.setTableItem(time=str(numData['timeNow'])[:4],
                          score=textScore[:4], index=numData['index'])

    def onStop(self, num):
        stopStr = f"\nEnd of mandate：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}\n\n"
        self.__output('text', stopStr)
        if Config.get('isOpenExplorer'):  # 打开输出文件夹
            self.outputList[0].openOutputFile()
        if Config.get('isOpenOutputFile'):  # 打开输出文件
            l = len(self.outputList)
            for i in range(1, l):
                self.outputList[i].openOutputFile()
        if Config.get('isNotify'):  # 通知弹窗
            title = f'Recognition complete, total {num["all"]} images'
            msg = 'The results are not saved to a local file, please view them in the software panel'
            if Config.get('isOutputTxt') or Config.get('isOutputSeparateTxt') or Config.get('isOutputMD') or Config.get('isOutputJsonl'):
                msg = f'The results are saved to the：{Config.get("outputFilePath")}'
            Notify(title, msg)
        if Config.get("isOkMission"):  # 计划任务
            Config.set("isOkMission", False)  # 一次性，设回false
            omName = Config.get('okMissionName')
            okMission = Config.get('okMission')
            if omName in okMission.keys() and 'code' in okMission[omName].keys():
                os.system(okMission[omName]['code'])  # 执行cmd语句
        Log.info('msnB: onClose')
        self.setRunning(MsnFlag.none)
        Config.main.gotoTop()
