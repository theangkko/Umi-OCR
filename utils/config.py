from utils.logger import GetLog

import os
import sys
import psutil  # 进程检查
import json
from enum import Enum
import tkinter as tk
import tkinter.messagebox
from locale import getdefaultlocale

Log = GetLog()


# 项目属性
class Umi:
    name = None  # 带版本号的名称
    pname = None  # 纯名称，固定
    ver = None  # 版本号
    website = None  # 主页
    about = None  # 简介
    path = os.path.realpath(sys.argv[0])  # 当前入口文件的路径
    cwd = os.path.dirname(path)  # 当前应设的工作目录


# 重设工作目录，防止开机自启丢失工作目录。此行代码必须比asset.py等模块优先执行
os.chdir(Umi.cwd)


# 枚举
class RunModeFlag(Enum):
    '''进程管理模式标志'''
    short = 0  # 按需关闭（减少空闲时内存占用）
    long = 1  # 后台常驻（大幅加快任务启动速度）


class ScsModeFlag(Enum):
    '''截屏模式标志'''
    multi = 0  # 多屏幕模式，目前仅能适配缩放比相同的多个屏幕
    system = 1  # 系统截屏模式


class ClickTrayModeFlag(Enum):
    '''点击托盘时模式标志'''
    show = 0  # 显示主面板
    screenshot = 1  # 截屏
    clipboard = 2  # 粘贴图片


class WindowTopModeFlag():
    '''窗口置顶模式标志'''
    # 不继承枚举
    never = 0  # 永不，静默模式
    finish = 1  # 任务完成时置顶


# 配置文件路径
ConfigJsonFile = 'Umi-OCR_config.json'

# 配置项
_ConfigDict = {
    # 软件设置
    'isDebug': {  # T时Debug模式
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isAdvanced': {  # T时高级模式，显示额外的设置项
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isTray': {  # T时展示托盘图标
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isBackground': {  # T时点关闭进入后台运行
        'default': True,
        'isSave': True,
        'isTK': True,
    },
    'clickTrayModeName': {  # 当前选择的点击托盘图标模式名称
        'default': '',
        'isSave': True,
        'isTK': True,
    },
    'clickTrayMode': {  # 点击托盘图标模式
        'default': {
            'display panel': ClickTrayModeFlag.show,
            'screenshot': ClickTrayModeFlag.screenshot,
            'Paste Pictures': ClickTrayModeFlag.clipboard,
        },
        'isSave': False,
        'isTK': False,
    },
    'textpanelFontFamily': {  # 主输出面板字体
        'default': 'Malgun Gothic',
        'isSave': True,
        'isTK': True,
    },
    'textpanelFontSize': {  # 主输出面板字体大小
        'default': 11,
        'isSave': True,
        'isTK': True,
    },
    'isTextpanelFontBold': {  # T时主输出面板字体加粗
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isWindowTop': {  # T时窗口置顶
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'WindowTopMode': {  # 窗口置顶模式
        'default': WindowTopModeFlag.finish,
        'isSave': True,
        'isTK': True,
    },
    'isNotify': {  # T时启用消息弹窗
        'default': True,
        'isSave': True,
        'isTK': True,
    },
    'isAutoStartup': {  # T时已添加开机自启
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isStartMenu': {  # T时已添加开始菜单
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isDesktop': {  # T时已添加桌面快捷方式
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    # 快捷识图设置
    'isHotkeyClipboard': {  # T时启用读剪贴板快捷键
        'default': True,
        'isSave': True,
        'isTK': True,
    },
    'hotkeyClipboard': {  # 读剪贴板快捷键，字符串
        'default': 'win+alt+v',
        'isSave': True,
        'isTK': True,
    },
    'isHotkeyScreenshot': {  # T时启用截屏快捷键
        'default': True,
        'isSave': True,
        'isTK': True,
    },
    'isScreenshotHideWindow': {  # T时截屏前隐藏窗口
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'screenshotHideWindowWaitTime': {  # 截屏隐藏窗口前等待时间
        'default': 200,
        'isSave': True,
        'isTK': False,
    },
    'hotkeyScreenshot': {  # 截屏快捷键，字符串
        'default': 'win+alt+c',
        'isSave': True,
        'isTK': True,
    },
    'hotkeyMaxTtl': {  # 组合键最长TTL（生存时间）
        'default': 2.0,
        'isSave': True,
        'isTK': True,
    },
    'isHotkeyStrict': {  # T时组合键严格判定
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'scsModeName': {  # 当前选择的截屏模式名称
        'default': '',
        'isSave': True,
        'isTK': True,
    },
    'scsMode': {  # 截屏模式
        'default': {
            'Windows System Screenshot': ScsModeFlag.system,
            'Umi-OCR Software screenshots': ScsModeFlag.multi,
        },
        'isSave': False,
        'isTK': False,
    },
    'scsColorLine': {  # 截屏瞄准线颜色
        'default': '#3366ff',
        'isSave': True,
        'isTK': True,
    },
    'scsColorBoxUp': {  # 截屏瞄准盒上层颜色
        'default': '#000000',
        'isSave': True,
        'isTK': True,
    },
    'scsColorBoxDown': {  # 截屏瞄准盒下层颜色
        'default': '#ffffff',
        'isSave': True,
        'isTK': True,
    },
    'isNeedCopy': {  # T时识别完成后自动复制文字
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isNeedClear': {  # T时输出前清空面板
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isShowImage': {  # T时截图后展示窗口，F时直接识别
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isHotkeyFinishSend': {  # T时启用联动识别，复制文本、发送按键
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'hotkeyFinishSend': {  # 联动识别快捷键
        'default': 'win+alt+x',
        'isSave': True,
        'isTK': True,
    },
    'isHotkeyFinishSend2': {  # 占位，无意义
        'default': False,
        'isSave': False,
        'isTK': True,
    },
    'hotkeyFinishSend2': {  # 联动识别的发送的按键
        'default': 'ctrl+c',
        'isSave': True,
        'isTK': True,
    },
    'hotkeyFinishSendNumber': {  # 发送按键的次数
        'default': 2,
        'isSave': True,
        'isTK': True,
    },
    'hotkeyFinishSendBetween': {  # 重复发送按键的间隔时间，秒
        'default': 0.2,
        'isSave': True,
        'isTK': True,
    },
    'isFinishSend': {  # 为T时本次任务需要发送快捷键
        'default': False,
        'isSave': False,
        'isTK': False,
    },
    # 计划任务设置
    'isOpenExplorer': {   # T时任务完成后打开资源管理器到输出目录
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isOpenOutputFile': {  # T时任务完成后打开输出文件
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isOkMission': {  # T时本次任务完成后执行指定计划任务。
        'default': False,
        'isSave': False,
        'isTK': True,
    },
    'okMissionName': {  # 当前选择的计划任务的name。
        'default': '',
        'isSave': True,
        'isTK': True,
    },
    'okMission': {  # 计划任务事件，code为cmd代码
        'default': {
            'turn off':  # 取消：shutdown /a
            {'code': r'msg %username% /time:25 "Umi-OCR task is completed and will switch off after 30s" & echo Close this window to cancel the shutdown & choice /t 30 /d y /n >nul & shutdown /f /s /t 0'},
            'sleep':  # 用choice实现延时
            {'code': r'msg %username% /time:25 "Umi-OCR task completed, will hibernate after 30s" & echo Close this window to cancel hibernation & choice /t 30 /d y /n >nul & shutdown /f /h'},
        },
        'isSave': True,
        'isTK': False,
    },
    # 输入文件设置
    'isRecursiveSearch': {  # T时导入文件夹将递归查找子文件夹中所有图片
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    # 输出文件设置
    'isOutputTxt': {  # T时输出内容写入txt文件
        'default': True,
        'isSave': True,
        'isTK': True,
    },
    'isOutputSeparateTxt': {  # T时输出内容写入每个图片同名的单独txt文件
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isOutputMD': {  # T时输出内容写入md文件
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isOutputJsonl': {  # T时输出内容写入jsonl文件
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'outputFilePath': {  # 输出文件目录
        'default': '',
        'isSave': False,
        'isTK': True,
    },
    'outputFileName': {  # 输出文件名称
        'default': '',
        'isSave': False,
        'isTK': True,
    },
    # 输出格式设置
    'isIgnoreNoText': {  # T时忽略(不输出)没有文字的图片信息
        'default': True,
        'isSave': True,
        'isTK': True,
    },
    # 文块后处理
    'tbpuName': {  # 当前选择的文块后处理
        'default': '',
        'isSave': True,
        'isTK': True,
    },
    'tbpu': {  # 文块后处理。这个参数通过 ocr\tbpu\__init__.py 导入，避免循环引用
        'default': {
            'common': None,
        },
        'isSave': False,
        'isTK': False,
    },
    'isAreaWinAutoTbpu': {  # T时忽略区域编辑器预览文本块后处理
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    # 引擎设置
    'ocrToolPath': {  # 引擎路径
        'default': 'PaddleOCR-json/PaddleOCR_json.exe',
        'isSave': True,
        'isTK': False,
    },
    'ocrRunModeName': {  # 当前选择的进程管理策略
        'default': '',
        'isSave': True,
        'isTK': True,
    },
    'ocrRunMode': {  # 进程管理策略
        'default': {
            'Background resident (dramatically speeds up task startup) ': RunModeFlag.long,
            'On-demand shutdown (reduces memory footprint at idle)': RunModeFlag.short,
        },
        'isSave': False,
        'isTK': False,
    },
    'ocrProcessStatus': {  # 进程运行状态字符串，由引擎单例传到tk窗口
        'default': 'inactive',
        'isSave': False,
        'isTK': True,
    },
    'ocrConfigName': {  # 当前选择的配置文件的name
        'default': '',
        'isSave': True,
        'isTK': True,
    },
    'ocrConfig': {  # Configuration file information
        'default': {  # Configuration file information
            'simplified Chinese': {
                'path': 'PaddleOCR_json_config_ch.txt'
            }
        },
        'isSave': True,
        'isTK': False,
    },
    'argsStr': {  # 启动参数字符串
        'default': '',
        'isSave': True,
        'isTK': True,
    },
    'isOcrAngle': {  # T时启用cls
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'ocrCpuThreads': {  # CPU线程数
        'default': 10,
        'isSave': True,
        'isTK': True,
    },
    'isOcrMkldnn': {  # Enable mkldnn acceleration
        'default': True,
        'isSave': True,
        'isTK': True,
    },
    'ocrLimitModeName': {  # 当前选择的压缩限制模式的name
        'default': '',
        'isSave': True,
        'isTK': True,
    },
    'ocrLimitMode': {  # 压缩限制模式
        'default': {
            'Long-edge compression mode': 'max',
            'short-edge expanding mode': 'min',
        },
        'isSave': False,
        'isTK': False,
    },
    'ocrLimitSize': {  # 压缩阈值
        'default': 960,
        'isSave': True,
        'isTK': True,
    },
    'ocrRamMaxFootprint': {  # 内存占用容量上限
        'default': 0,
        'isSave': True,
        'isTK': True,
    },
    'ocrRamMaxTime': {  # 内存占用时间上限
        'default': 30,
        'isSave': True,
        'isTK': True,
    },
    'ocrInitTimeout': {  # 初始化超时时间，秒
        'default': 20.0,
        'isSave': True,
        'isTK': True,
    },
    'imageSuffix': {  # 图片后缀
        'default': '.jpg .jpe .jpeg .jfif .png .webp .bmp .tif .tiff',
        'isSave': True,
        'isTK': True,
    },
    # 更改语言窗口
    'isLanguageWinAutoExit': {  # T,The language window closes automatically at T
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    'isLanguageWinAutoOcr': {  # T,Repeat task after T-time language window modification
        'default': False,
        'isSave': True,
        'isTK': True,
    },
    # 防止多开相关
    'processID':  {  # 正在运行的进程的PID
        'default': -1,
        'isSave': True,
        'isTK': False,
    },
    'processKey':  {  # 可标识一个进程的信息，如进程名或路径
        'default': '',
        'isSave': True,
        'isTK': False,
    },

    # 记录不再提示
    'promptScreenshotScale':  {  # 截图时比例不对
        'default': True,
        'isSave': True,
        'isTK': False,
    },
    'promptMultiOpen':  {  # 多开提示
        'default': True,
        'isSave': True,
        'isTK': False,
    },

    # 不同模块交流的接口
    'ignoreArea':  {  # 忽略区域
        'default': None,
        'isSave': False,
        'isTK': False,
    },
    'tipsTop1': {  # 主窗口顶部进度条上方的label，左侧
        'default': '',
        'isTK': True,
    },
    'tipsTop2': {  # 主窗口顶部进度条上方的label，右侧
        'default': 'Drag in an image or take a quick screenshot',
        'isTK': True,
    },
}


class ConfigModule:
    # ↓ In these encodings can use all functions, other encodings are not guaranteed to work, such as dragging in pictures with Chinese paths.
    # ↓ But the map function works fine.
    __sysEncodingSafe = ['cp936', 'cp65001']

    __tkSaveTime = 200  # How long after the tk variable changes is written locally. Milliseconds

    _initFlag = False  # Marking the initialisation of the program as complete and ready to pick up passengers as normal

    # ==================== initialisation ====================

    def __init__(self):
        self.main = None  # The self of win_main can be used to get the main it to refresh the interface or create a timer.
        self.sysEncoding = 'ascii'  # 系统编码。初始化时获取
        self.__saveTimer = None  # 计时器，用来更新tk变量一段时间后写入本地
        self.__optDict = {}  # 配置项的数据
        self.__tkDict = {}  # tk绑定变量
        self.__saveList = []  # 需要保存的项
        self.__traceDict = {}  # 跟踪值改变
        # 将配置项加载到self
        for key in _ConfigDict:
            value = _ConfigDict[key]
            self.__optDict[key] = value['default']
            if value.get('isSave', False):
                self.__saveList.append(key)
            if value.get('isTK', False):
                self.__tkDict[key] = None

    def isInit(self):
        '''查询程序是否初始化完成'''
        return self._initFlag

    def initOK(self):
        self._initFlag = True

    def initTK(self, main):
        '''初始化tk变量'''
        self.main = main  # 主窗口

        def toSaveConfig():  # 保存值的事件
            self.save()
            self.__saveTimer = None

        def onTkVarChange(key):  # 值改变的事件
            self.update(key)  # 更新配置项
            if key in self.__saveList:  # 需要保存
                if self.__saveTimer:  # 计时器已存在，则停止已存在的
                    self.main.win.after_cancel(self.__saveTimer)  # 取消计时
                    self.__saveTimer = None
                self.__saveTimer = self.main.win.after(  # 重新计时
                    self.__tkSaveTime, toSaveConfig)

        for key in self.__tkDict:
            if isinstance(self.__optDict[key], bool):  # 布尔最优先，以免被int覆盖
                self.__tkDict[key] = tk.BooleanVar()
            elif isinstance(self.__optDict[key], str):
                self.__tkDict[key] = tk.StringVar()
            elif isinstance(self.__optDict[key], float):
                self.__tkDict[key] = tk.DoubleVar()
            elif isinstance(self.__optDict[key], int):
                self.__tkDict[key] = tk.IntVar()
            else:  # 给开发者提醒
                raise Exception(f'The configuration item {key} is to generate a tk variable, but the type is not legal!')
            # 赋予初值
            self.__tkDict[key].set(self.__optDict[key])
            # 跟踪值改变事件
            self.__tkDict[key].trace(
                "w", lambda *e, key=key: onTkVarChange(key))

    # ==================== 读写本地文件 ====================

    def load(self):
        '''从本地json文件读取配置。必须在initTK后执行'''

        # 初始化编码，获取系统编码
        # https://docs.python.org/zh-cn/3.8/library/locale.html#locale.getdefaultlocale
        # https://docs.python.org/zh-cn/3.8/library/codecs.html#standard-encodings
        syse = getdefaultlocale()[1]
        if syse:
            self.sysEncoding = syse

        try:
            with open(ConfigJsonFile, 'r', encoding='utf8')as fp:
                jsonData = json.load(fp)  # 读取json文件
                for key in jsonData:
                    if key in self.__optDict:
                        self.set(key, jsonData[key])
        except json.JSONDecodeError:  # 反序列化json错误
            if tk.messagebox.askyesno(
                'Had a little problem.',
                    f'Configuration file {ConfigJsonFile} is in the wrong format. \n\n [Yes] Reset the file \n [No] Exit this run'):
                self.save()
            else:
                os._exit(0)
        except FileNotFoundError:  # 无配置文件
            # 当成是首次启动软件，提示
            if self.sysEncoding not in self.__sysEncodingSafe:  # 不安全的地区
                tk.messagebox.showwarning(
                    'warnings',
                    f'Your system locale encoding of [{self.sysEncoding}] may cause the function of dragging in images to be abnormal, so it is recommended to use the browse button to import images. Other functions are not affected.')
            self.save()

    def checkMultiOpen(self):
        '''检查多开'''
        def isMultiOpen():
            '''主进程多开时返回T'''
            def getProcessKey(pid):
                # 区分不同时间和空间上同一个进程的识别信息
                try:
                    return str(psutil.Process(pid).create_time())
                except psutil.NoSuchProcess as e:  # 虽然psutil.pid_exists验证pid存在，但 Process 无法生成对象
                    return ''
            # 检查上次记录的pid和key是否还在运行
            lastPID = self.get('processID')
            lastKey = self.get('processKey')
            if psutil.pid_exists(lastPID):  # 上次记录的pid如今存在
                runningKey = getProcessKey(lastPID)
                if lastKey == runningKey:  # 上次记录的key与它pid当前key对应，则证实多开
                    Log.info(f'Check that the process is already running. pid：{lastPID}，key：{lastKey}')
                    if tk.messagebox.askyesno(
                        'draw attention to sth.',
                            f'Umi-OCR is already running. \n\n [Yes] Exit this run \n [No] Multi-open software'):
                        os._exit(0)
                    else:  # 忽视warnings继续多开，不记录当前信息
                        return
            # 本次为唯一的进程，记录当前进程信息
            nowPid = os.getpid()
            nowKey = getProcessKey(nowPid)
            self.set('processID', nowPid)
            self.set('processKey', nowKey, isSave=True)
        if self.get('promptMultiOpen'):
            isMultiOpen()

    def save(self):
        '''保存配置到本地json文件'''
        saveDict = {}  # 提取需要保存的项
        for key in self.__saveList:
            saveDict[key] = self.__optDict[key]
        try:
            with open(ConfigJsonFile, 'w', encoding='utf8')as fp:
                fp.write(json.dumps(saveDict, indent=4, ensure_ascii=False))
        except Exception as e:
            tk.messagebox.showerror(
                'warnings',
                f'Cannot save configuration file, please check if you have enough permissions\n{e}')

    # ==================== 操作变量 ====================

    def update(self, key):
        '''更新某个值，从tk变量读取到配置项'''
        try:
            self.__optDict[key] = self.__tkDict[key].get()
        except Exception as err:
            Log.error(f'Failed to refresh set item {key}.：\n{err}')
        if key in self.__traceDict:
            try:
                self.__traceDict[key]()
            except Exception as err:
                Log.error(f'Setting item {key} tracking event call failure：\n{err}')

    def get(self, key):
        '''获取一个配置项的值'''
        return self.__optDict[key]

    def set(self, key, value, isUpdateTK=False, isSave=False):
        '''设置一个配置项的值。isSave表示非tk配置项立刻保存本地（需要先在_ConfigDict里设）'''
        if key in self.__tkDict:  # 若是tk，则通过tk的update事件去更新optDict值
            self.__tkDict[key].set(value)
            if isUpdateTK:  # 需要刷新界面
                self.main.win.update()
        else:  # 不是tk，直接更新optDict
            self.__optDict[key] = value
            if isSave and _ConfigDict[key].get('isSave', False):
                self.save()  # 保存本地

    def getTK(self, key):
        '''获取一个TK变量'''
        return self.__tkDict[key]

    def addTrace(self, key, func):
        '''跟踪一个变量，值改变时调用函数。同一个值只能注册一个函数'''
        self.__traceDict[key] = func


Config = ConfigModule()  # 设置模块 单例
