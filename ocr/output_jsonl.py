# 输出到json文件
from utils.config import Config
from ocr.output import Output
from utils.logger import GetLog

import os
import json

Log = GetLog()


class OutputJsonl(Output):

    def __init__(self):
        outputDir = Config.get('outputFilePath')  # 输出路径（文件夹）
        outputName = Config.get("outputFileName")  # 文件名
        self.outputPath = f'{outputDir}/{outputName}.jsonl'  # 输出路径
        self.isDebug = Config.get('isDebug')  # 是否输出调试
        # 创建输出文件
        try:
            if os.path.exists(self.outputPath):  # 文件存在
                os.remove(self.outputPath)  # 删除文件
            open(self.outputPath, 'w').close()  # 创建文件
        except FileNotFoundError:
            raise Exception(f'Failed to create jsonl file. Please check if the following address is correct.\n{self.outputPath}')
        except Exception as e:
            raise Exception(
                f'Failed to create jsonl file. File address:\n{self.outputPath}\n\nerror message：\n{e}')

    def print(self, text):
        if self.outputPath:
            with open(self.outputPath, "a", encoding='utf-8') as f:  # 追加写入本地文件
                f.write(text)

    def debug(self, text):
        '''输出调试信息'''
        pass

    def text(self, text):
        '''输出正文'''
        pass

    def img(self, textBlockList, imgInfo, numData, textDebug):
        '''输出图片结果'''
        # 标题和debug信息
        outData = {
            'imgInfo': imgInfo,
            'textBlockList': textBlockList,
            'numData': numData,
            'textDebug': textDebug,
        }
        # print(f'输出json：\n{textBlockList}\n{imgInfo}\n{numData}\n{textDebug}')
        self.print(json.dumps(outData, ensure_ascii=False)+'\n')
