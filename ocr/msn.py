# msn == Mission
# Base class for the tasker. When the engine executes the pipeline __runMission once, it calls the tasker's method

import tkinter as tk
import tkinter.messagebox

from utils.logger import GetLog
Log = GetLog()


class Msn:

    '''任务器必须有四个公有方法：onStart onGet onStop onError
    每个方法必有一个传入值：num。定义如下：
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
        }'''

    def onStart(self, num):
        '''流水线初始化完毕时调用'''
        Log.info(f'Msn onStart Not rewritten!\nnum: {num}')

    def onGet(self, num, data):
        '''流水线获取到一次OCR结果时调用\n
        data: OCR结果，字典'''
        Log.info(f'Msn onGet Not rewritten!\nnum: {num}\ndata: {data}')

    def onStop(self, num):
        '''流水线结束任务时调用。可通过之前onError有没有被调用过，来判断是否正常结束'''
        Log.info(f'Msn onStop Not rewritten!\nnum: {num}')

    def onError(self, num, err):
        '''流水线出现严重异常，无法继续工作，必须退出时调用。紧接着会调用onStop\n
        只是想弹出提示框的话，这个方法可以不用重写\n
        err: 错误信息，字符串'''
        tk.messagebox.showerror(
            'There is a billion little problems.',
            f'mission failure：{err}')
