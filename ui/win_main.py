from utils.config import Config, Umi, ScsModeFlag, WindowTopModeFlag  # 最先加载配置
from utils.logger import GetLog
from utils.asset import *  # 资源
from utils.data_structure import KeyList
from utils.tool import Tool
from utils.startup import Startup  # 启动方式
from utils.hotkey import Hotkey  # 快捷键
from utils.command_arg import Parse, Mission  # 启动参数分析
from ui.win_notify import Notify  # 通知弹窗
from ui.win_screenshot import ScreenshotCopy  # 截屏
from ui.win_select_area import IgnoreAreaWin  # 子窗口
from ui.win_ocr_language import ChangeOcrLanguage  # 更改语言
from ui.widget import Widget  # 控件
from ui.pmw.PmwBalloon import Balloon  # 气泡提示
from ui.tray import SysTray
from ocr.engine import OCRe, MsnFlag, EngFlag  # 引擎
# 识图任务处理器
from ocr.msn_batch_paths import MsnBatch
from ocr.msn_quick import MsnQuick

import os
import ctypes
from sys import argv
from PIL import Image  # 图像
import tkinter as tk
import tkinter.font
import tkinter.filedialog
import tkinter.colorchooser
from tkinter import ttk
from windnd import hook_dropfiles  # 文件拖拽
from webbrowser import open as webOpen  # “关于”面板打开项目网址
from argparse import ArgumentParser  # 启动参数

Log = GetLog()


class MainWin:
    def __init__(self):
        self.batList = KeyList()  # 管理批量photograph的信息及表格id的列表
        self.tableKeyList = []  # 顺序存放self.imgDict
        self.lockWidget = []  # 需要运行时锁定的组件

        # 1.initialisation主窗口
        self.win = tk.Tk()
        self.win.withdraw()  # 隐藏窗口，等initialisation完毕再考虑是否显示
        self.balloon = Balloon(self.win)  # 气泡框

        def initStyle():  # initialisation样式
            style = ttk.Style()
            # winnative clam alt default classic vista xpnative
            # style.theme_use('default')
            style.configure('icon.TButton', padding=(12, 0))
            style.configure('go.TButton', font=('Microsoft YaHei', '12', ''),  # bold
                            width=9)
            style.configure('gray.TCheckbutton', foreground='gray')
        initStyle()

        def initDPI():
            # 调用api设置成由应用程序缩放
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            # 调用api获得当前的缩放因子
            ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
            # 设置缩放因子
            self.win.tk.call('tk', 'scaling', ScaleFactor/100)
        # initDPI()

        def initWin():
            self.win.title(Umi.name)
            # Window size and position
            w, h = 360, 500  # Initial and minimum window size
            ws, hs = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
            x, y = round(ws/2 - w/2), round(hs/2 - h/2)  # Initial position, centre of screen
            self.win.minsize(w, h)  # 最小大小
            self.win.geometry(f"{w}x{h}+{x}+{y}")  # 初始大小与位置
            self.win.protocol("WM_DELETE_WINDOW", self.onClose)  # 窗口关闭
            # 注册文件拖入，整个主窗口内有效
            # 改成延迟一段时间后生效，减少产生异常的概率
            # Fatal Python error: PyEval_RestoreThread: NULL tstate
            # hook_dropfiles(self.win, func=self.draggedImages)
            hook_dropfiles(self.win, func=lambda e: self.win.after(
                80, lambda: self.draggedImages(e)))
            # 图标
            Asset.initRelease()  # 释放base64资源到本地
            Asset.initTK()  # initialisationtkphotograph
            self.win.iconphoto(False, Asset.getImgTK('umiocr24'))  # 设置窗口图标
        initWin()

        # 2.Initialising configuration items
        self.win.bind('<<QuitEvent>>', lambda *e: self.onClose())  # exit event
        Config.initTK(self)  # initialisation设置项
        Config.load()  # 加载本地文件
        Config.checkMultiOpen()  # 检查多开

        # 3.Initialising components
        def initTop():  # top button
            tk.Frame(self.win, height=5).pack(side='top')
            fr = tk.Frame(self.win)
            fr.pack(side='top', fill="x", padx=5)
            # right button
            self.btnRun = ttk.Button(fr, command=self.run, text='Commencement of mission',
                                     style='go.TButton')
            self.btnRun.pack(side='right', fill='y')
            # Left side text and progress bar
            vFrame2 = tk.Frame(fr)
            vFrame2.pack(side='top', fill='x')
            # top of the progress bar
            wid = ttk.Checkbutton(vFrame2, variable=Config.getTK('isWindowTop'),
                                  text='window topping', style='gray.TCheckbutton')
            wid.pack(side='left')
            self.balloon.bind(
                wid, 'Window locked at the top of the system\n\nWhen enabled, the mouse hover alert box within the software will be hidden')
            tk.Label(vFrame2, textvariable=Config.getTK('tipsTop2')).pack(
                side='right', padx=2)
            tk.Label(vFrame2, textvariable=Config.getTK('tipsTop1')).pack(
                side='right', padx=2)
            self.progressbar = ttk.Progressbar(fr)
            self.progressbar.pack(side='top', padx=2, pady=2, fill="x")
        initTop()

        self.notebook = ttk.Notebook(self.win)  # Initialising the tab component
        self.notebook.pack(expand=True, fill=tk.BOTH)  # Fill parent component
        self.notebookTab = []

        def initTab1():  # form card
            tabFrameTable = tk.Frame(self.notebook)  # Tab Master Container
            self.notebookTab.append(tabFrameTable)
            self.notebook.add(tabFrameTable, text=f'{"batch file": ^10s}')
            # parapet
            fr1 = tk.Frame(tabFrameTable)
            fr1.pack(side='top', fill='x', padx=1, pady=1)
            # 左
            btn = ttk.Button(fr1, image=Asset.getImgTK('screenshot24'),  # 截图按钮
                             command=self.openScreenshot,
                             style='icon.TButton',  takefocus=0,)
            self.balloon.bind(
                btn, 'Screenshot Description\nLeft Drag: Boxed Area\nRight Click: Unboxing\n　　 Esc：Exit Screenshot')
            btn.pack(side='left')
            self.lockWidget.append(btn)
            btn = ttk.Button(fr1, image=Asset.getImgTK('paste24'),  # 剪贴板按钮
                             command=self.runClipboard,
                             style='icon.TButton',  takefocus=0,)
            self.balloon.bind(btn, 'Paste Pictures')
            btn.pack(side='left')
            self.lockWidget.append(btn)
            btn = ttk.Button(fr1, image=Asset.getImgTK('language24'),  # 语言按钮
                             command=ChangeOcrLanguage,
                             style='icon.TButton',  takefocus=0)
            self.balloon.bind(btn, 'Change OCR language')
            btn.pack(side='left')
            self.lockWidget.append(btn)
            # 右
            btn = ttk.Button(fr1, image=Asset.getImgTK('clear24'),  # 清空按钮
                             command=self.clearTable,
                             style='icon.TButton',  takefocus=0,)
            self.balloon.bind(btn, 'Empty the form')
            btn.pack(side='right')
            self.lockWidget.append(btn)
            btn = ttk.Button(fr1, image=Asset.getImgTK('delete24'),  # 删除按钮
                             command=self.delImgList,
                             style='icon.TButton',  takefocus=0,)
            self.balloon.bind(btn, 'Remove selected files \n hold Shift orCtrl，Left click to select multiple files')
            btn.pack(side='right')
            self.lockWidget.append(btn)
            btn = ttk.Button(fr1, image=Asset.getImgTK('openfile24'),  # 打开文件按钮
                             command=self.openFileWin,
                             style='icon.TButton',  takefocus=0,)
            self.balloon.bind(btn, 'Browse Documents')
            btn.pack(side='right')
            self.lockWidget.append(btn)
            # body of the form
            fr2 = tk.Frame(tabFrameTable)
            fr2.pack(side='top', fill='both')
            self.table = ttk.Treeview(
                master=fr2,  # 父容器
                height=50,  # 表格显示的行数,height行
                columns=['name', 'time', 'score'],  # 显示的列
                show='headings',  # 隐藏首列
            )
            self.table.pack(expand=True, side="left", fill='both')
            self.table.heading('name', text='Name of the document')
            self.table.heading('time', text='take a period of ')
            self.table.heading('score', text='confidence level ')
            self.table.column('name', minwidth=40)
            self.table.column('time', width=20, minwidth=20)
            self.table.column('score', width=30, minwidth=30)
            vbar = tk.Scrollbar(  # Binding scrollbars
                fr2, orient='vertical', command=self.table.yview)
            vbar.pack(side="left", fill='y')
            self.table["yscrollcommand"] = vbar.set
        initTab1()

        def initTab2():  # 输出卡
            tabFrameOutput = tk.Frame(self.notebook)  # 选项卡主容器
            self.notebookTab.append(tabFrameOutput)
            self.notebook.add(tabFrameOutput, text=f'{"Content": ^10s}')
            fr1 = tk.Frame(tabFrameOutput)
            fr1.pack(side='top', fill='x', padx=1, pady=1)
            self.isAutoRoll = tk.IntVar()
            self.isAutoRoll.set(1)
            # 左
            btn = ttk.Button(fr1, image=Asset.getImgTK('screenshot24'),  # 截图按钮
                             command=self.openScreenshot,
                             style='icon.TButton',  takefocus=0,)
            self.balloon.bind(
                btn, 'Screenshot Description\nLeft Drag: Boxed Area\nRight Click: Unboxing\n　　 Esc：Exit Screenshot')
            btn.pack(side='left')
            self.lockWidget.append(btn)
            btn = ttk.Button(fr1, image=Asset.getImgTK('paste24'),  # 剪贴板按钮
                             command=self.runClipboard,
                             style='icon.TButton',  takefocus=0,)
            self.balloon.bind(btn, 'Paste Pictures')
            btn.pack(side='left')
            self.lockWidget.append(btn)
            btn = ttk.Button(fr1, image=Asset.getImgTK('language24'),  # 语言按钮
                             command=ChangeOcrLanguage,
                             style='icon.TButton',  takefocus=0)
            self.balloon.bind(btn, 'Change OCR language')
            btn.pack(side='left')
            self.lockWidget.append(btn)

            # 右
            btn = ttk.Button(fr1, image=Asset.getImgTK('clear24'),  # 清空按钮
                             command=self.panelClear,
                             style='icon.TButton',  takefocus=0,)
            self.balloon.bind(btn, 'Empty the output panel \n [Settings→Quick Graphics] to enable the automatic clearing of the panel')
            btn.pack(side='right')

            ttk.Checkbutton(fr1, variable=self.isAutoRoll, text="autoscrolling",
                            takefocus=0,).pack(side='right')
            tf = tk.Label(fr1, text='calligraphic style', fg='gray', cursor='hand2')
            tf.pack(side='right', padx=10)
            tf.bind(
                '<Button-1>', lambda *e: self.notebook.select(self.notebookTab[2]))  # 转到设置卡
            self.balloon.bind(tf, 'Changing the font of the output panel in the [Settings] tab')

            fr2 = tk.Frame(tabFrameOutput)
            fr2.pack(side='top', fill='both')
            vbar = tk.Scrollbar(fr2, orient='vertical')  # 滚动条
            vbar.pack(side="right", fill='y')
            self.textOutput = tk.Text(fr2, height=500, width=500)
            self.textOutput.pack(fill='both', side="left")
            self.textOutput.tag_config(  # Adding Highlighted Tags
                'blue', foreground='blue')
            self.textOutput.tag_config(  # Adding Highlighted Tags
                'red', foreground='red')
            vbar["command"] = self.textOutput.yview
            self.textOutput["yscrollcommand"] = vbar.set
        initTab2()

        def initTab3():  # setup card
            tabFrameConfig = tk.Frame(self.notebook)  # 选项卡主容器
            self.notebookTab.append(tabFrameConfig)
            self.notebook.add(tabFrameConfig, text=f'{"set up": ^10s}')

            def initOptFrame():  # initialisation可滚动画布 及 内嵌框架
                optVbar = tk.Scrollbar(
                    tabFrameConfig, orient="vertical")  # 创建滚动条
                optVbar.pack(side="right", fill="y")
                self.optCanvas = tk.Canvas(
                    tabFrameConfig, highlightthickness=0)  # 创建画布，用于承载框架。highlightthickness取消高亮边框
                self.optCanvas.pack(side="left", fill="both",
                                    expand="yes")  # 填满父窗口
                self.optCanvas["yscrollcommand"] = optVbar.set  # 绑定滚动条
                optVbar["command"] = self.optCanvas.yview
                self.optFrame = tk.Frame(self.optCanvas)  # 容纳设置项的框架
                self.optFrame.pack()
                self.optCanvas.create_window(  # 框架塞进画布
                    (0, 0), window=self.optFrame, anchor="nw")
            initOptFrame()

            LabelFramePadY = 3  # 每个区域上下间距

            def initTopTips():  # 顶部提示
                fTips = tk.Frame(self.optFrame)
                fTips.pack(side='top')
                tipsLab = tk.Label(
                    fTips, fg='red',
                    text='Close the top of the window to show the mouse hover box.')
                if Config.get('isWindowTop'):
                    tipsLab.pack(side='top')
                tk.Frame(fTips).pack(side='top')  # 空框架，用于自动调整高度的占位

                def changeIsWinTop():
                    if Config.get('isWindowTop'):  # 启用置顶
                        tipsLab.pack(side='top')
                    else:  # 取消置顶
                        tipsLab.pack_forget()
                    self.gotoTop()
                Config.addTrace('isWindowTop', changeIsWinTop)

            initTopTips()

            def initSoftwareFrame():  # 软件行为设置
                fSoft = tk.LabelFrame(
                    self.optFrame, text='General Settings')
                fSoft.pack(side='top', fill='x',
                           ipady=2, pady=LabelFramePadY, padx=4)

                # 主面板字体设置
                fr3 = tk.Frame(fSoft)
                fr3.pack(side='top', fill='x', pady=2, padx=5)
                fr3.grid_columnconfigure(1, weight=1)
                self.balloon.bind(fr3, 'Adjusting the font style of the output panel in the [Identify Content] tab')
                tk.Label(fr3, text='Output Panel Fonts').grid(column=0, row=0, sticky='w')
                ff = tk.font.families()  # 获取系统字体
                fontFamilies = []
                fontFamiliesABC = []
                for i in ff:
                    if not i[0] == '@':  # 排除竖版
                        if '\u4e00' <= i[0] <= '\u9fff':  # 中文开头的优先
                            fontFamilies.append(i)
                        else:
                            fontFamiliesABC.append(i)
                fontFamilies += fontFamiliesABC
                cbox = ttk.Combobox(fr3, state='readonly', takefocus=0,
                                    textvariable=Config.getTK('textpanelFontFamily'), value=fontFamilies)
                cbox.grid(column=1, row=0, sticky='ew')
                self.balloon.bind(cbox, 'Do not use the scroll wheel. \nPlease use the up and down arrow keys or pull the scroll bar to navigate the list')
                tk.Label(fr3, text='font size').grid(column=2, row=0, sticky='w')
                tk.Entry(fr3, textvariable=Config.getTK('textpanelFontSize'),
                         width=4, takefocus=0).grid(column=3, row=0, sticky='w')
                tk.Label(fr3, text=' ').grid(column=4, row=0, sticky='w')
                ttk.Checkbutton(fr3, text='thicken',
                                variable=Config.getTK('isTextpanelFontBold')).grid(column=5, row=0, sticky='w')
                # 检查当前配置字体是否存在
                f = Config.get('textpanelFontFamily')
                if f and f not in fontFamilies:
                    Log.error(f'Configuring Output Panel Fonts【{f}】Does not exist. Reset to empty')
                    Config.set('textpanelFontFamily', '')

                def updateTextpanel():
                    f = Config.get('textpanelFontFamily')
                    s = Config.get('textpanelFontSize')
                    b = Config.get('isTextpanelFontBold')
                    font = (f, s, 'bold' if b else 'normal')
                    self.textOutput['font'] = font
                Config.addTrace('textpanelFontFamily', updateTextpanel)
                Config.addTrace('textpanelFontSize', updateTextpanel)
                Config.addTrace('isTextpanelFontBold', updateTextpanel)
                updateTextpanel()

                fr1 = tk.Frame(fSoft)
                fr1.pack(side='top', fill='x', pady=2, padx=5)
                fr1.grid_columnconfigure(1, weight=1)
                self.balloon.bind(
                    fr1, 'You can turn off/on the system tray icon, modify the function triggered when you double-click the icon \n the item is modified, the next time you open the software to take effect')
                wid = ttk.Checkbutton(fr1, text='Show system tray icon',
                                      variable=Config.getTK('isTray'))
                wid.grid(column=0, row=0, sticky='w')
                Widget.comboboxFrame(fr1, '，double-click icon', 'clickTrayMode', width=12).grid(
                    column=1, row=0, sticky='w')

                fr2 = tk.Frame(fSoft)
                fr2.pack(side='top', fill='x', pady=2, padx=5)
                tk.Label(fr2, text='Main window closed：').pack(side='left', padx=2)
                ttk.Radiobutton(fr2, text='Exiting the software',
                                variable=Config.getTK('isBackground'), value=False).pack(side='left')
                wid = ttk.Radiobutton(fr2, text='Minimise to tray',
                                      variable=Config.getTK('isBackground'), value=True)
                wid.pack(side='left', padx=15)
                self.balloon.bind(wid, 'This option is available when the system tray icon is displayed')

                # 弹出方式设置
                fr3 = tk.Frame(fSoft)
                fr3.pack(side='top', fill='x', pady=2, padx=5)
                tk.Label(fr3, text='main window pop-up：').pack(side='left', padx=2)
                wid = ttk.Radiobutton(fr3, text='pop-up automatically',
                                      variable=Config.getTK('WindowTopMode'), value=WindowTopModeFlag.finish)
                wid.pack(side='left')
                self.balloon.bind(
                    wid, 'Evokes a pop-up window when a quick map, or a batch task is completed.')
                wid = ttk.Radiobutton(fr3, text='silent mode',
                                      variable=Config.getTK('WindowTopMode'), value=WindowTopModeFlag.never)
                wid.pack(side='left', padx=15)
                self.balloon.bind(
                    wid, 'No active pop-ups\n Recommended to enable notification pop-ups')

                # 消息弹窗设置
                def changeNotify():
                    if Config.get('isNotify'):
                        Notify('Welcome to Umi-OCR', 'Notification popups are enabled!')
                Config.addTrace('isNotify', changeNotify)
                fr4 = tk.Frame(fSoft)
                fr4.pack(side='top', fill='x', pady=2, padx=5)
                ttk.Checkbutton(
                    fr4, variable=Config.getTK('isNotify'), text='Enable notification pop-ups').pack(side='left')

                # 启动方式设置
                fr5 = tk.Frame(fSoft)
                fr5.pack(side='top', fill='x', pady=2, padx=5)
                self.balloon.bind(
                    fr5, 'Can be set to start silently, stowed in the system tray, without displaying the main window')
                ttk.Checkbutton(fr5, variable=Config.getTK('isAutoStartup'),
                                text='boot up (computer)', command=Startup.switchAutoStartup).pack(side='left')
                ttk.Checkbutton(fr5, variable=Config.getTK('isStartMenu'),
                                text='Start menu item', command=Startup.switchStartMenu).pack(side='left', padx=20)
                ttk.Checkbutton(fr5, variable=Config.getTK('isDesktop'),
                                text='desktop shortcut', command=Startup.switchDesktop).pack(side='left')
            initSoftwareFrame()

            def quickOCR():  # Quick Map Settings
                fQuick = tk.LabelFrame(
                    self.optFrame, text='fast map recognition')
                fQuick.pack(side='top', fill='x',
                            ipady=2, pady=LabelFramePadY, padx=4)
                # 截图快捷键触发时，子线程向主线程发送事件，在主线程中启动截图窗口
                # 避免子线程直接唤起截图窗导致的窗口闪烁现象
                self.win.bind('<<ScreenshotEvent>>',
                              self.openScreenshot)  # 绑定截图事件
                cbox = Widget.comboboxFrame(fQuick, 'Screenshot Module：', 'scsMode')
                cbox.pack(side='top', fill='x', padx=4)
                self.balloon.bind(
                    cbox, 'Switch screenshot work module\n\n [Umi-OCR software screenshot] convenient, accurate\n [Windows system screenshot] compatibility better')
                frss = tk.Frame(fQuick)
                frss.pack(side='top', fill='x')
                fhkUmi = tk.Frame(frss)
                fhkUmi.pack(side='top', fill='x')
                fhkU0 = tk.Frame(fhkUmi)
                fhkU0.pack(side='top', fill='x', pady=2)
                tk.Label(fhkU0, text='Indicator Colour：').pack(side='left')
                self.balloon.bind(fhkU0, 'Modify the colour of the indicator when taking a screenshot \n After modifying this item, it will take effect the next time you open the software.')

                def changeColor(configName, title=None):
                    initColor = Config.get(configName)
                    color = tk.colorchooser.askcolor(
                        color=initColor, title=title)
                    if color[1]:
                        Config.set(configName, color[1])
                lab1 = tk.Label(fhkU0, text='crosshairs', cursor='hand2', fg='blue')
                lab1.pack(side='left', padx=9)
                lab1.bind(
                    '<Button-1>', lambda *e: changeColor('scsColorLine', 'Screenshot crosshair colour'))
                lab2 = tk.Label(fhkU0, text='dotted line box surface', cursor='hand2', fg='blue')
                lab2.pack(side='left', padx=9)
                lab2.bind(
                    '<Button-1>', lambda *e: changeColor('scsColorBoxUp', 'Screenshot Rectangular Box Dashed Layer Colour'))
                lab3 = tk.Label(fhkU0, text='Bottom of the dotted line box', cursor='hand2', fg='blue')
                lab3.pack(side='left', padx=9)
                lab3.bind(
                    '<Button-1>', lambda *e: changeColor('scsColorBoxDown', 'Screenshot Rectangle Dashed Underline Colour'))
                wid = Widget.hotkeyFrame(fhkUmi, 'Screenshot Recognition Shortcut', 'Screenshot',
                                         lambda *e: self.win.event_generate(
                                             '<<ScreenshotEvent>>'), isAutoBind=False)
                wid.pack(side='top', fill='x')
                self.balloon.bind(
                    wid, 'After closing the shortcut key, you can still call the screenshot via the button on the panel or the small tray icon \n Click [Modify] to set the custom shortcut key.')

                syssscom = 'win+shift+s'
                fhkSys = Widget.hotkeyFrame(frss, 'System Screenshot Shortcut', 'Screenshot',
                                            lambda *e: self.win.event_generate(
                                                '<<ScreenshotEvent>>'), True, syssscom, isAutoBind=False)
                self.balloon.bind(
                    fhkSys, 'Listen to the system screenshot and call OCR\n\nIf the software does not respond after the screenshot, please ensure that the windows system comes with \n [Screenshots and Sketches] in the [Auto Copy to Clipboard] switch is on!')

                wid = Widget.hotkeyFrame(
                    fQuick, 'Paste Picture Shortcut', 'Clipboard', self.runClipboard, isAutoBind=True)
                wid.pack(side='top', fill='x', padx=4)
                self.balloon.bind(wid, 'Try to read the clipboard, if there is a picture then call OCR\n Click [Modify] to set a custom shortcut key')
                if Config.get('isAdvanced'):  # Hidden Advanced Options: Key Combination Determination Adjustment
                    fr1 = tk.Frame(fQuick)
                    fr1.pack(side='top', fill='x', pady=2, padx=5)
                    tk.Label(fr1, text=' key combination：').pack(side='left')
                    fr11 = tk.Frame(fr1)
                    fr11.pack(side='left')
                    self.balloon.bind(
                        fr11, 'Lax: the currently pressed key can be triggered as long as it contains the set key combination \n Strict: the currently pressed key must match the set combination in order to be triggered')
                    tk.Label(fr11, text='Trigger judgement').pack(side='left')
                    ttk.Radiobutton(fr11, text='liberally',
                                    variable=Config.getTK('isHotkeyStrict'), value=False).pack(side='left')
                    ttk.Radiobutton(fr11, text='severity',
                                    variable=Config.getTK('isHotkeyStrict'), value=True).pack(side='left')
                    fr12 = tk.Frame(fr1)
                    fr12.pack(side='left')
                    self.balloon.bind(fr12, 'All keys in the combination must be pressed consecutively within that time \n order to trigger the')
                    tk.Label(fr12, text='，time limit：').pack(side='left')
                    tk.Entry(fr12,
                             textvariable=Config.getTK('hotkeyMaxTtl'), width=4).pack(side='left')
                    tk.Label(fr12, text='秒').pack(side='left')

                fr2 = tk.Frame(fQuick)
                fr2.pack(side='top', fill='x', pady=2, padx=5)
                fr2.grid_columnconfigure(1, minsize=20)
                wid = ttk.Checkbutton(fr2, variable=Config.getTK('isScreenshotHideWindow'),
                                      text='Hide main window')
                wid.grid(column=0, row=0, sticky='w')
                self.balloon.bind(
                    wid, f'Hide main window before screenshot \n will delay {Config.get("screenshotHideWindowWaitTime")} milliseconds to wait for the window animation')
                wid = ttk.Checkbutton(fr2, variable=Config.getTK('isShowImage'),
                                      text='Screenshot preview window')
                wid.grid(column=2, row=0)
                self.balloon.bind(
                    wid, f'Unchecked: OCR immediately after the screenshot \n Ticked: after the screenshot to show the photograph, can be recognised later or save the photographic')
                wid = ttk.Checkbutton(fr2, variable=Config.getTK('isNeedCopy'),
                                      text='Automatic copying of results')
                wid.grid(column=0, row=1)
                self.balloon.bind(wid, 'After fast map recognition is complete, copy the resulting text to the clipboard')
                wid = ttk.Checkbutton(fr2, variable=Config.getTK('isNeedClear'),
                                      text='Auto Empty Panel')
                wid.grid(column=2, row=1)
                self.balloon.bind(wid, f'Each fast map recognition will empty the recognition content panel and omit information such as time.')

                if Config.get('isAdvanced'):  # 隐藏高级选项：截图联动
                    frSend = tk.Frame(fQuick)
                    frSend.pack(side='top', fill='x', pady=2, padx=4)
                    frSend.grid_columnconfigure(0, weight=1)
                    self.balloon.bind(frSend, 'Screenshot Linkage: Press the shortcut key to perform screenshot OCR and copy the result to the clipboard, \n then send the specified keyboard keystrokes \n can be used to linkage to evoke tools such as translator or AHK \n times: the number of times to repeat the sending of the keystrokes, e.g. 2 for a double tap')
                    wid = Widget.hotkeyFrame(
                        frSend, 'Screenshot linkage Shortcut', 'FinishSend', func=self.openLinkageScreenshot, isAutoBind=True)
                    wid.grid(column=0, row=0, sticky="nsew")
                    wid = Widget.hotkeyFrame(
                        frSend, 'Linkage send button', 'FinishSend2', isAutoBind=False, isCheckBtn=False)
                    wid.grid(column=0, row=1, sticky="nsew")
                    tk.Entry(frSend, width=2, textvariable=Config.getTK('hotkeyFinishSendNumber')
                            ).grid(column=1, row=1)
                    tk.Label(frSend, text='the second (day, time etc)').grid(column=2, row=1)

                # 切换截图模式
                def onModeChange():
                    isHotkey = Config.get('isHotkeyScreenshot')
                    scsName = Config.get('scsModeName')
                    umihk = Config.get('hotkeyScreenshot')
                    scsMode = Config.get('scsMode').get(
                        scsName, ScsModeFlag.multi)  # 当前截屏模式
                    if scsMode == ScsModeFlag.system:  # 切换到系统截图
                        fhkUmi.forget()
                        fhkSys.pack(side='top', fill='x', padx=4)
                        self.updateFrameHeight()  # 刷新框架
                        if isHotkey:  # 当前已在注册
                            if umihk:  # 注销软件截图
                                Widget.delHotkey(umihk)  # 注销按键
                            Hotkey.add(syssscom,  # 添加快捷键监听
                                       lambda *e: self.win.event_generate('<<ScreenshotEvent>>'))
                    elif scsMode == ScsModeFlag.multi:  # 切换到软件截图
                        fhkSys.forget()
                        fhkUmi.pack(side='top', fill='x', padx=4)
                        self.updateFrameHeight()  # 刷新框架
                        if isHotkey:
                            Widget.delHotkey(syssscom)  # 注销按键
                            if umihk:
                                Hotkey.add(umihk,  # 添加快捷键监听
                                           lambda *e: self.win.event_generate('<<ScreenshotEvent>>'))
                    Log.info(f'Screenshot mode change：{scsMode}')
                Config.addTrace('scsModeName', onModeChange)
                onModeChange()
            quickOCR()

            # 批量任务设置
            frameBatch = tk.LabelFrame(self.optFrame, text="batch file")
            frameBatch.pack(side='top', fill='x',
                            ipady=2, pady=LabelFramePadY, padx=4)

            def initScheduler():  # 计划任务设置
                frameScheduler = tk.LabelFrame(
                    frameBatch, labelanchor='n', text="Planned tasks")
                frameScheduler.pack(side='top', fill='x',
                                    ipady=2, pady=LabelFramePadY, padx=4)

                fr1 = tk.Frame(frameScheduler)
                fr1.pack(side='top', fill='x', pady=2, padx=5)
                ttk.Checkbutton(fr1, text="Open the file when finished",
                                variable=Config.getTK('isOpenOutputFile')).pack(side='left')
                ttk.Checkbutton(fr1, text="Open the catalogue when finished",
                                variable=Config.getTK('isOpenExplorer'),).pack(side='left', padx=15)

                fr2 = tk.Frame(frameScheduler)
                fr2.pack(side='top', fill='x', pady=2, padx=5)
                ttk.Checkbutton(fr2, text='Implemented after this completion',
                                variable=Config.getTK('isOkMission')).pack(side='left')
                okMissionDict = Config.get("okMission")
                okMissionNameList = [i for i in okMissionDict.keys()]
                wid = ttk.Combobox(fr2, width=14, state="readonly", textvariable=Config.getTK('okMissionName'),
                                   value=okMissionNameList)
                wid.pack(side='left')
                self.balloon.bind(wid, 'You can open the software configuration json file and add your own tasks (cmd commands)')
                if Config.get("okMissionName") not in okMissionNameList:
                    wid.current(0)  # initialisationCombobox和okMissionName
            initScheduler()

            def initInFile():  # 输入设置
                fInput = tk.LabelFrame(
                    frameBatch, labelanchor='n', text='Photograph import')
                fInput.pack(side='top', fill='x',
                                 ipady=2, pady=LabelFramePadY, padx=4)
                self.balloon.bind(
                    fInput, f"Allowed Photograph Formats：\n{Config.get('imageSuffix')}")

                fr1 = tk.Frame(fInput)
                fr1.pack(side='top', fill='x', pady=2, padx=5)
                wid = ttk.Checkbutton(
                    fr1, variable=Config.getTK('isRecursiveSearch'), text='Recursively read all photographs in a subfolder')
                wid.grid(column=0, row=0, columnspan=2, sticky='w')
                self.lockWidget.append(wid)
                if Config.get('isAdvanced'):  # 隐藏高级选项：修改photograph许可后缀
                    tk.Label(fr1, text='Image Suffix:　').grid(
                        column=0, row=2, sticky='w')
                    enInSuffix = tk.Entry(
                        fr1, textvariable=Config.getTK('imageSuffix'))
                    enInSuffix.grid(column=1, row=2, sticky='nsew')
                    self.lockWidget.append(enInSuffix)

                fr1.grid_columnconfigure(1, weight=1)
            initInFile()

            def initOutFile():  # 输出设置
                fOutput = tk.LabelFrame(
                    frameBatch, labelanchor='n', text="Result Output")
                fOutput.pack(side='top', fill='x',
                                  ipady=2, pady=LabelFramePadY, padx=4)
                # 输出文件类型勾选
                fr1 = tk.Frame(fOutput)
                fr1.pack(side='top', fill='x', pady=2, padx=5)

                wid = ttk.Checkbutton(
                    fr1, variable=Config.getTK('isOutputTxt'), text='merge .txt file')
                self.balloon.bind(wid, f'All recognised text output to the same txt file')
                wid.grid(column=0, row=0,  sticky='w')
                self.lockWidget.append(wid)
                wid = ttk.Checkbutton(
                    fr1, variable=Config.getTK('isOutputSeparateTxt'), text='split .txt file')
                self.balloon.bind(wid, f'The text of each photograph is output to a separate txt file with the same name.')
                wid.grid(column=2, row=0,  sticky='w')
                self.lockWidget.append(wid)
                wid = ttk.Checkbutton(
                    fr1, variable=Config.getTK('isOutputMD'), text='Graphic links.md file')
                self.balloon.bind(wid, f'Opened with a Markdown reader to display both photograph and text')
                wid.grid(column=0, row=1,  sticky='w')
                self.lockWidget.append(wid)
                wid = ttk.Checkbutton(
                    fr1, variable=Config.getTK('isOutputJsonl'), text='Raw Info.json file')
                self.balloon.bind(wid, f'Contains all file paths and OCR information, which can be imported into other programs for further operation.')
                wid.grid(column=2, row=1,  sticky='w')
                self.lockWidget.append(wid)
                tk.Label(fr1, text=' ').grid(column=1, row=0)

                def offAllOutput(e):  # 关闭全部输出
                    if OCRe.msnFlag == MsnFlag.none:
                        Config.set('isOutputTxt', False)
                        Config.set('isOutputSeparateTxt', False)
                        Config.set('isOutputMD', False)
                        Config.set('isOutputJsonl', False)
                labelOff = tk.Label(fr1, text='Turn off all outputs',
                                    cursor='hand2', fg='blue')
                labelOff.grid(column=0, row=2, sticky='w')
                labelOff.bind('<Button-1>', offAllOutput)  # 绑定关闭全部输出

                wid = ttk.Checkbutton(fr1, text='No information is output when there is no text in the photograph.',
                                      variable=Config.getTK('isIgnoreNoText'),)
                wid.grid(column=0, row=10, columnspan=9, sticky='w')
                self.lockWidget.append(wid)

                tk.Label(fOutput, fg='gray',
                         text="If the following two items are empty, the default output will be to the folder where the first photograph is located"
                         ).pack(side='top', fill='x', padx=5)
                # output directory
                fr2 = tk.Frame(fOutput)
                fr2.pack(side='top', fill='x', pady=2, padx=5)
                tk.Label(fr2, text="output directory：").grid(column=0, row=3, sticky='w')
                enOutPath = tk.Entry(
                    fr2, textvariable=Config.getTK('outputFilePath'))
                enOutPath.grid(column=1, row=3,  sticky='ew')
                self.lockWidget.append(enOutPath)
                fr2.grid_rowconfigure(4, minsize=2)  # 第二行拉开间距
                tk.Label(fr2, text="Output file name：").grid(column=0, row=5, sticky='w')
                enOutName = tk.Entry(
                    fr2, textvariable=Config.getTK('outputFileName'))
                enOutName.grid(column=1, row=5, sticky='ew')
                self.lockWidget.append(enOutName)
                fr2.grid_columnconfigure(1, weight=1)  # 第二列自动扩充
            initOutFile()

            # 后处理设置
            def initProcess():  # 后处理设置
                fProcess = tk.LabelFrame(self.optFrame,  text='Text Post-Processing')
                fProcess.pack(side='top', fill='x',
                              ipady=2, pady=LabelFramePadY, padx=4)

                fIgnore = tk.Frame(fProcess)
                fIgnore.pack(side='top', fill='x', pady=2, padx=4)

                self.ignoreBtn = ttk.Button(fIgnore, text='Open the Ignore Region Editor (set to exclude watermarks)',
                                            command=self.openSelectArea)
                self.ignoreBtn.pack(side='top', fill='x')
                self.balloon.bind(
                    self.ignoreBtn, 'Ignore the specified area in the photograph\n can be used to exclude photographic watermarks during batch identification')
                self.lockWidget.append(self.ignoreBtn)
                # 忽略区域本体框架
                self.ignoreFrame = tk.Frame(fIgnore)  # 不pack，动态添加
                self.ignoreFrame.grid_columnconfigure(0, minsize=4)
                wid = ttk.Button(self.ignoreFrame, text='添加区域',
                                 command=self.openSelectArea)
                wid.grid(column=1, row=0, sticky='w')
                self.lockWidget.append(wid)
                wid = ttk.Button(self.ignoreFrame, text='clear zone',
                                 command=self.clearArea)
                wid.grid(column=1, row=1, sticky='w')
                self.lockWidget.append(wid)
                self.ignoreLabel = tk.Label(
                    self.ignoreFrame, anchor='w', justify='left')  # 显示生效大小
                self.ignoreLabel.grid(column=1, row=2, sticky='n')
                self.balloon.bind(
                    self.ignoreLabel, 'When batch tasking, only photographs with the same resolution will have the ignore region applied.')
                self.ignoreFrame.grid_rowconfigure(2, minsize=10)
                self.ignoreFrame.grid_columnconfigure(2, minsize=4)
                self.canvasHeight = 120  # 画板高度不变，宽度根据选区回传数据调整
                self.canvas = tk.Canvas(self.ignoreFrame, width=200, height=self.canvasHeight,
                                        bg="black", cursor='hand2')
                self.canvas.grid(column=3, row=0, rowspan=10)
                self.canvas.bind(
                    '<Button-1>', lambda *e: self.openSelectArea())
                fpro = tk.Frame(fProcess)
                fpro.pack(side='top', fill='x', pady=2, padx=4)
                fpro.grid_columnconfigure(0, weight=1)
                wid = Widget.comboboxFrame(
                    fpro, 'Merge paragraphs: ', 'tbpu', self.lockWidget)
                wid.grid(column=0, row=0, sticky='ew')
                self.balloon.bind(wid, 'Combine single lines of text divided by OCR into whole paragraphs \n Click the button on the right to view the programme description')
                labelUse = tk.Label(fpro, text='clarification', width=5,
                                    fg='deeppink', cursor='question_arrow')
                labelUse.grid(column=1, row=0)
                labelUse.bind(
                    '<Button-1>', lambda *e: self.showTips(GetTbpuHelp(Umi.website)))  # 绑定鼠标左键点击
            initProcess()

            def initOcrUI():  # OCR引擎设置
                frameOCR = tk.LabelFrame(
                    self.optFrame, text="OCR Recognition Engine Settings")
                frameOCR.pack(side='top', fill='x', ipady=2,
                              pady=LabelFramePadY, padx=4)
                wid = Widget.comboboxFrame(
                    frameOCR, 'recognition language', 'ocrConfig', self.lockWidget)
                wid.pack(side='top', fill='x', pady=2, padx=5)
                self.balloon.bind(
                    wid, 'This software has organised multi-language expansion packs to import model libraries in more languages,\n can also manually import PaddleOCR-compatible model libraries,\n for more details, please browse the project Github homepage\n\n Vertical model libraries (recognised languages) are recommended to be used in conjunction with vertically-arranged merged paragraphs')
                # 压缩
                fLim = tk.Frame(frameOCR)
                fLim.pack(side='top', fill='x', pady=2, padx=5)
                self.balloon.bind(
                    fLim, 'The long side compression mode may significantly speed up recognition, but may reduce the accuracy of recognition for large resolution photographs\nPhotographs larger than 4000 pixels may change the value to half the maximum side length. Must be an integer greater than zero\nDefault value: 960\n\nShort side expansion mode may improve the accuracy of small resolution photographs. Generally not used.')
                Widget.comboboxFrame(
                    fLim, 'Zoom Preprocessing：', 'ocrLimitMode', self.lockWidget, 14).pack(side='left')
                tk.Label(fLim, text='until').pack(side='left')
                wid = tk.Entry(
                    fLim, width=9, textvariable=Config.getTK('ocrLimitSize'))
                wid.pack(side='left')
                self.lockWidget.append(wid)
                tk.Label(fLim, text='pixels').pack(side='left')
                # 方向
                wid = ttk.Checkbutton(frameOCR, text='Enable orientation classifiers (text deflection 90°/180° orientation correction)',
                                      variable=Config.getTK('isOcrAngle'))
                wid.pack(side='top', fill='x', pady=2, padx=5)
                self.balloon.bind(
                    wid, 'Turn on this option when the text in the Photograph is deflected by 90 or 180 degrees \n may slightly slow down the recognition speed \n no need to enable this option for small angle deflection')
                self.lockWidget.append(wid)
                # CPU
                fCpu = tk.Frame(frameOCR, padx=5)
                fCpu.pack(side='top', fill='x')
                tk.Label(fCpu, text='Thread count:').pack(side='left')
                wid = tk.Entry(
                    fCpu, width=6, textvariable=Config.getTK('ocrCpuThreads'))
                wid.pack(side='left')
                self.lockWidget.append(wid)
                self.balloon.bind(
                    wid, 'Preferably equal to the number of threads in the CPU. Must be an integer greater than zero')
                wid = ttk.Checkbutton(fCpu, text='Enable MKLDNN acceleration',
                                      variable=Config.getTK('isOcrMkldnn'))
                wid.pack(side='left', padx=40)
                self.balloon.bind(
                    wid, 'Significantly faster recognition. Memory footprint also increases')
                self.lockWidget.append(wid)

                # grid
                fr1 = tk.Frame(frameOCR)
                fr1.pack(side='top', fill='x', padx=5)
                if Config.get('isAdvanced'):
                    # 隐藏高级选项：额外启动参数
                    tk.Label(fr1, text='Additional startup parameters：').grid(
                        column=0, row=2, sticky='w')
                    wid = tk.Entry(
                        fr1, textvariable=Config.getTK('argsStr'))
                    wid.grid(column=1, row=2, sticky="nsew")
                    self.balloon.bind(
                        wid, 'OCR advanced parameter commands. Please adhere to the format required by PaddleOCR-json. For details, please refer to the project homepage')
                    self.lockWidget.append(wid)
                    # 隐藏高级选项：引擎管理策略
                    Widget.comboboxFrame(fr1, 'Engine Management Strategy：', 'ocrRunMode', self.lockWidget
                                         ).grid(column=0, row=6, columnspan=2, sticky='we')
                    # 隐藏高级选项：引擎启动超时
                    fInit = tk.Frame(fr1)
                    fInit.grid(column=0, row=7, columnspan=2,
                              sticky='we', pady=2)
                    self.balloon.bind(
                        fInit, 'When the engine is started and the initialisation is not completed after the time limit, it is judged to have failed.')
                    tk.Label(fInit, text='Initialisation timeout decision：').pack(side='left')
                    tk.Entry(fInit, width=5, 
                             textvariable=Config.getTK('ocrInitTimeout')).pack(side='left')
                    tk.Label(fInit, text='秒').pack(side='left')
                    
                    # 隐藏高级选项：自动清理内存
                    fRam = tk.Frame(fr1)
                    fRam.grid(column=0, row=8, columnspan=2,
                              sticky='we', pady=2)
                    tk.Label(fRam, text='Automatic memory cleaning： Occupancy over').pack(side='left')
                    wid = tk.Entry(
                        fRam, width=5, textvariable=Config.getTK('ocrRamMaxFootprint'))
                    wid.pack(side='left')
                    self.lockWidget.append(wid)
                    tk.Label(fRam, text='MB or free').pack(side='left')
                    wid = tk.Entry(
                        fRam, width=5, textvariable=Config.getTK('ocrRamMaxTime'))
                    wid.pack(side='left')
                    self.lockWidget.append(wid)
                    tk.Label(fRam, text='秒').pack(side='left')
                    self.balloon.bind(
                        fRam, 'When the engine policy is "background resident", it takes effect \n If the occupied memory exceeds the specified value, or if no task is executed within the specified time, the memory will be cleared once \n Frequent memory clearing will lead to lagging, affecting the user experience \n It is recommended that the occupied memory is not less than 1500 MB, and the idle memory is not less than 10 seconds \n The two conditions take effect independently. Ignore this condition when 0 is entered.')

                frState = tk.Frame(fr1)
                frState.grid(column=0, row=10, columnspan=2, sticky='nsew')
                tk.Label(frState, text='The current state of the engine:').pack(
                    side='left')
                tk.Label(frState, textvariable=Config.getTK('ocrProcessStatus')).pack(
                    side='left')
                labStop = tk.Label(frState, text="cessation",
                                   cursor='hand2', fg="red")
                labStop.pack(side='right')
                self.balloon.bind(labStop, 'Forced stopping of engine processes')
                labStart = tk.Label(frState, text="启动",
                                    cursor='hand2', fg='blue')
                labStart.pack(side='right', padx=5)

                def engStart():
                    try:
                        OCRe.start()
                    except Exception as err:
                        tk.messagebox.showerror(
                            'Theres a billion little problems.',
                            f'Engine startup failure：{err}')
                labStart.bind(
                    '<Button-1>', lambda *e: engStart())
                labStop.bind(
                    '<Button-1>', lambda *e: OCRe.stop())

                fr1.grid_rowconfigure(1, minsize=4)
                fr1.grid_rowconfigure(3, minsize=4)
                fr1.grid_columnconfigure(1, weight=1)
            initOcrUI()

            def initAbout():  # 关于面板
                frameAbout = tk.LabelFrame(
                    self.optFrame, text='with respect to')
                frameAbout.pack(side='top', fill='x', ipady=2,
                                pady=LabelFramePadY, padx=4)
                tk.Label(frameAbout, image=Asset.getImgTK(
                    'umiocr64')).pack()  # 图标
                tk.Label(frameAbout, text=Umi.name, fg='gray').pack()
                tk.Label(frameAbout, text=Umi.about, fg='gray').pack()
                labelWeb = tk.Label(frameAbout, text=Umi.website, cursor='hand2',
                                    fg='deeppink')
                labelWeb.pack()  # 文字
                labelWeb.bind(  # 绑定鼠标左键点击，打开网页
                    '<Button-1>', lambda *e: webOpen(Umi.website))
            initAbout()

            def initEX():  # 额外
                fEX = tk.Frame(self.optFrame)
                fEX.pack(side='top', fill='x', padx=4)
                labelOpenFile = tk.Label(
                    fEX, text='Open the settings file', fg='gray', cursor='hand2')
                labelOpenFile.pack(side='left')
                labelOpenFile.bind(
                    '<Button-1>', lambda *e: os.startfile('Umi-OCR_config.json'))
                self.balloon.bind(labelOpenFile, 'Umi-OCR_config.json')
                wid = tk.Checkbutton(fEX, text='debug mode', fg='gray',
                                     variable=Config.getTK('isDebug'))
                self.balloon.bind(
                    wid, 'Debugging features for developers with immediate effect: \nOCR outputs additional debugging information | Built-in screenshot display debugger')
                wid.pack(side='right')
                # 隐藏高级选项
                wid = tk.Checkbutton(fEX, text='Advanced Options', fg='gray',
                                     variable=Config.getTK('isAdvanced'))
                self.balloon.bind(
                    wid, 'Enable hidden advanced options to take effect after reboot')
                wid.pack(side='right', padx=10)
                # 若初始时非置顶，不显示提示，则尾部预留出空间
                if not Config.get('isWindowTop'):
                    tk.Label(self.optFrame).pack(side='top')
            initEX()

            def initOptFrameWH():  # initialisation框架的宽高
                self.updateFrameHeight()
                self.optCanvasWidth = 1  # 宽度则是随窗口大小而改变。

                def onCanvasResize(event):  # 绑定画布大小改变事件
                    cW = event.width-3  # 当前 画布宽度
                    if not cW == self.optCanvasWidth:  # 若与上次不同：
                        self.optFrame['width'] = cW  # 修改设置页 框架宽度
                        self.optCanvasWidth = cW
                self.optCanvas.bind(  # 绑定画布大小改变事件。只有画布组件前台显示时才会触发，减少性能占用
                    '<Configure>', onCanvasResize)

                def onCanvasMouseWheel(event):  # 绑定画布中滚轮滚动事件
                    self.optCanvas.yview_scroll(
                        1 if event.delta < 0 else -1, "units")
                self.optCanvas.bind_all('<MouseWheel>', onCanvasMouseWheel)
                # 为所有复选框解绑默认滚轮事件，防止误触
                self.win.unbind_class('TCombobox', '<MouseWheel>')
            initOptFrameWH()
        initTab3()

        # 解析启动参数
        flags = Parse(argv)
        if 'error' in flags:
            tk.messagebox.showerror(
                'Had a little problem.', flags['error'])
        # 启动托盘
        if Config.get('isTray'):
            SysTray.start()
            self.win.wm_protocol(  # 注册窗口关闭事件
                'WM_DELETE_WINDOW', self.onCloseWin)
            # ↑ 所以，当不启动托盘时，窗口的×未关联任何事件，是默认的退出软件。
            if not flags['hide']:  # 非silent mode
                self.gotoTop()  # 恢复主窗显示
        else:  # 无托盘，强制显示主窗
            self.gotoTop()
        self.win.after(1, Config.initOK)  # 标记initialisation完成
        if flags['img'] or flags['clipboard'] or flags['screenshot']:  # 有初始任务
            self.win.after(10, Mission(flags))
        Notify('Welcome to Umi-OCR', 'Notification popups are enabled!')
        self.win.mainloop()

    # 加载photograph ===============================================

    def draggedImages(self, paths):  # 拖入photograph
        if not self.isMsnReady():
            tk.messagebox.showwarning(
                'Mission in progress', '请discontinue a mission后，Then drag in the photograph')
            return
        self.notebook.select(self.notebookTab[0])  # 切换到表格选项卡
        pathList = []
        for p in paths:  # byte转字符串
            pathList.append(p.decode(Config.sysEncoding,  # 根据系统编码来解码
                            errors='ignore'))
        self.addImagesList(pathList)

    def openFileWin(self):  # 打开option文件窗
        if not self.isMsnReady():
            return
        suf = Config.get('imageSuffix')  # 许可后缀
        paths = tk.filedialog.askopenfilenames(
            title='optionphotograph', filetypes=[('photograph', suf)])
        self.addImagesList(paths)

    def addImagesList(self, paths):  # 添加一批photograph列表
        if not self.isMsnReady():
            tk.messagebox.showwarning(
                'Mission in progress', 'Please discontinue a mission before adding pictures')
            return
        suf = Config.get('imageSuffix').split()  # 许可后缀列表

        def addImage(path):  # 添加一张photograph。传入路径，许可后缀。
            path = path.replace("/", "\\")  # 浏览是左斜杠，拖入是右斜杠；需要统一
            if suf and os.path.splitext(path)[1].lower() not in suf:
                return  # 需要判别许可后缀 且 文件后缀不在许可内，不添加。
            # 检测是否重复
            if self.batList.isDataItem('path', path):
                return
            # 检测是否可用
            try:
                s = Image.open(path).size
            except Exception as e:
                tk.messagebox.showwarning(
                    "Ran into a little problem", f"The image failed to load. Image address:\n{path}\n\nerror message：\n{e}")
                return
            # 计算路径
            p = os.path.abspath(os.path.join(path, os.pardir))  # 父文件夹
            if not Config.get("outputFilePath"):  # initialisation输出路径
                Config.set("outputFilePath", p)
            if not Config.get("outputFileName"):  # initialisation输出文件名
                n = f"[conversion text]_{os.path.basename(p)}"
                Config.set("outputFileName", n)
            # 加入待处理列表
            name = os.path.basename(path)  # 带后缀的文件名
            tableInfo = (name, "", "")
            id = self.table.insert('', 'end', values=tableInfo)  # 添加到表格组件中
            dictInfo = {"name": name, "path": path, "size": s}
            self.batList.append(id, dictInfo)

        isRecursiveSearch = Config.get("isRecursiveSearch")
        for path in paths:  # 遍历拖入的所有路径
            if os.path.isdir(path):  # 若是目录
                if isRecursiveSearch:  # 需要递归子文件夹
                    for subDir, dirs, subFiles in os.walk(path):
                        for s in subFiles:
                            addImage(subDir+"\\"+s)
                else:  # 非递归，只搜索子文件夹一层
                    subFiles = os.listdir(path)  # 遍历子文件
                    for s in subFiles:
                        addImage(path+"\\"+s)  # 添加
            elif os.path.isfile(path):  # 若是文件：
                addImage(path)  # 直接添加

    # 忽略区域 ===============================================

    def openSelectArea(self):  # 打开option区域
        if not self.isMsnReady() or not self.win.attributes('-disabled') == 0:
            return
        defaultPath = ""
        if not self.batList.isEmpty():
            defaultPath = self.batList.get(index=0)["path"]
        self.win.attributes("-disabled", 1)  # 禁用父窗口
        IgnoreAreaWin(self.closeSelectArea, defaultPath)

    def closeSelectArea(self):  # 关闭option区域，获取option区域数据
        self.win.attributes("-disabled", 0)  # 启用父窗口
        area = Config.get("ignoreArea")
        if not area:
            self.ignoreFrame.pack_forget()  # 隐藏忽略区域窗口
            self.ignoreBtn.pack(side='top', fill='x')  # 显示按钮
            self.updateFrameHeight()  # 刷新框架
            return
        self.ignoreLabel["text"] = f"effective resolution：\n宽 {area['size'][0]}\n高 {area['size'][1]}"
        self.canvas.delete(tk.ALL)  # 清除画布
        scale = self.canvasHeight / area['size'][1]  # 显示缩放比例
        width = round(self.canvasHeight * (area['size'][0] / area['size'][1]))
        self.canvas['width'] = width
        areaColor = ["red", "green", "darkorange"]
        tran = 2  # 绘制偏移量
        for i in range(3):  # 绘制新图
            for a in area['area'][i]:
                x0, y0 = a[0][0]*scale+tran, a[0][1]*scale+tran,
                x1, y1 = a[1][0]*scale+tran, a[1][1]*scale+tran,
                self.canvas.create_rectangle(
                    x0, y0, x1, y1,  fill=areaColor[i])
        self.ignoreBtn.pack_forget()  # 隐藏按钮
        self.ignoreFrame.pack(side='top', fill='x')  # 显示忽略区域窗口
        self.updateFrameHeight()  # 刷新框架

    def clearArea(self):  # 清空忽略区域
        self.ignoreFrame.pack_forget()  # 隐藏忽略区域窗口
        self.ignoreBtn.pack(side='top', fill='x')  # 显示按钮
        self.updateFrameHeight()  # 刷新框架
        Config.set("ignoreArea", None)
        self.canvas.delete(tk.ALL)  # 清除画布
        self.canvas['width'] = int(self.canvasHeight * (16/9))

    # 表格操作 ===============================================

    def clearTable(self):  # 清空表格
        if not self.isMsnReady():
            return
        self.progressbar["value"] = 0
        Config.set('tipsTop1', '')
        Config.set('tipsTop2', 'Please import the file')
        Config.set("outputFilePath", "")
        Config.set("outputFileName", "")
        self.batList.clear()
        chi = self.table.get_children()
        for i in chi:
            self.table.delete(i)  # 表格组件移除

    def delImgList(self):  # photograph列表中删除选中
        if not self.isMsnReady():
            return
        chi = self.table.selection()
        for i in chi:
            self.table.delete(i)
            self.batList.delete(key=i)

    def setTableItem(self, time, score, key=None, index=-1):  # 改变表中第index项的数据信息
        if not key:
            key = self.batList.indexToKey(index)
        self.table.set(key, column='time', value=time)
        self.table.set(key, column='score', value=score)

    def clearTableItem(self):  # 清空表格数据信息
        keys = self.batList.getKeys()
        for key in keys:  # 清空表格参数
            self.table.set(key, column='time', value="")
            self.table.set(key, column='score', value="")

    # 写字板操作 =============================================

    def panelOutput(self, text, position=tk.END, highlight=''):
        '''输出面板写入文字'''
        self.textOutput.insert(position, text)
        if highlight:  # 需要高亮
            if position == tk.END:  # 暂时只允许尾部插入
                self.textOutput.tag_add(  # 尾部插入要高亮前一行
                    highlight, f'end -1lines linestart', f'end -1lines lineend')
        if self.isAutoRoll.get():  # 需要自动滚动
            self.textOutput.see(position)

    def errorOutput(self, title, msg='', highlight='red'):
        '''输出错误提示'''
        Notify(title, msg)
        if not self.textOutput.get('end-2c') == '\n':  # 当前面板尾部没有换行，则加换行
            self.panelOutput('\n')
        self.panelOutput(title, highlight=highlight)  # 输出红色提示
        if msg:
            self.panelOutput('\n'+msg)
        self.panelOutput('\n')

    def panelClear(self):
        '''清空输出面板'''
        self.textOutput.delete('1.0', tk.END)

    # 窗口操作 =============================================

    def updateFrameHeight(self):  # 刷新设置页框架高度
        self.optFrame.pack_propagate(True)  # 启用框架自动宽高调整
        self.optFrame.update()  # 强制刷新
        rH = self.optFrame.winfo_height()  # 由组件撑起的 框架高度
        self.optCanvas.config(scrollregion=(0, 0, 0, rH))  # 画布内高度为框架高度
        self.optFrame.pack_propagate(False)  # 禁用框架自动宽高调整
        self.optFrame["height"] = rH  # 手动还原高度

    def gotoTop(self, isForce=False):  # 主窗置顶
        flag = Config.get('WindowTopMode')
        # 模式：silent mode
        if flag == WindowTopModeFlag.never and not isForce and Config.get('isTray'):
            self.win.attributes('-topmost', 0)
            return
        # 模式：pop-up automatically，或不满足silent mode要求
        if self.win.state() == 'iconic':  # 窗口最小化状态下
            self.win.state('normal')  # 恢复前台状态
        self.win.attributes('-topmost', 1)  # 设置层级最前
        geometry = self.win.geometry()  # 缓存主窗当前位置大小
        self.win.deiconify()  # 主窗获取焦点
        self.win.geometry(geometry)  # 若主窗正在贴边，获取焦点会退出贴边模式，所以重新设置位置恢复贴边
        # 未设置窗口置顶，则一段时间后取消层级最前
        if not Config.get('isWindowTop'):
            self.win.after(500, lambda: self.win.attributes('-topmost', 0))

    # 进行任务 ===============================================

    def isMsnReady(self):
        '''可以操作下一次任务时返回T'''
        return OCRe.msnFlag == MsnFlag.none

    def setRunning(self, batFlag):  # 设置运行状态。

        def setNone():
            self.btnRun['text'] = 'Commencement of mission'
            self.btnRun['state'] = 'normal'
            Config.set('tipsTop2', 'Closed')
            return 'normal'

        def initing():
            self.btnRun['text'] = 'discontinue a mission'
            self.btnRun['state'] = 'normal'
            Config.set('tipsTop1', '')
            Config.set('tipsTop2', 'initialisation')
            self.progressbar["maximum"] = 50  # 重置进度条长度，值越小加载动画越快
            self.progressbar['mode'] = 'indeterminate'  # 进度条为来回动模式
            self.progressbar.start()  # 进度条开始加载动画
            return 'disable'

        def running():
            self.progressbar.stop()  # 进度条停止加载动画
            self.progressbar['mode'] = 'determinate'  # 进度条静止模式
            return ''

        def stopping():
            self.btnRun['text'] = 'in the process of stopping'
            self.btnRun['state'] = 'disable'
            if str(self.progressbar["mode"]) == 'indeterminate':
                self.progressbar.stop()  # 进度条停止加载动画
                self.progressbar['mode'] = 'determinate'  # 进度条静止模式
            return ''

        state = {
            MsnFlag.none: setNone,
            MsnFlag.initing: initing,
            MsnFlag.running: running,
            MsnFlag.stopping: stopping,
        }.get(batFlag, '')()
        if state:
            for w in self.lockWidget:  # 改变组件状态（禁用，启用）
                if 'widget' in w.keys() and 'stateOFnormal' in w.keys():
                    if state == 'normal':
                        w['widget']['state'] = w['stateOFnormal']  # 正常状态为特殊值
                    else:
                        w['widget']['state'] = state
                elif 'state' in w.keys():
                    w['state'] = state
        self.win.update()

    def run(self):  # 运行按钮触发
        if self.isMsnReady():  # 未在运行
            if self.batList.isEmpty():
                return
            # initialisation批量识图任务处理器
            try:
                msnBat = MsnBatch()
            except Exception as err:
                tk.messagebox.showwarning('Theres a billion little problems.', f'{err}')
                return  # 未开始运行，终止本次运行
            # 开始运行
            paths = self.batList.getItemValueList('path')
            OCRe.runMission(paths, msnBat)
        # 允许任务进行中或initialisation的中途discontinue a mission
        elif OCRe.msnFlag == MsnFlag.running or OCRe.msnFlag == MsnFlag.initing:
            OCRe.stopByMode()

    def startSingleClipboard(self):  # 开始单张识别的剪贴板任务
        try:  # initialisationfast map recognition任务处理器
            msnQui = MsnQuick()
        except Exception as err:
            tk.messagebox.showwarning('Theres a billion little problems.', f'{err}')
            return  # 未开始运行，终止本次运行
        # 开始运行
        OCRe.runMission(['clipboard'], msnQui)
        self.notebook.select(self.notebookTab[1])  # 转到输出卡
        self.gotoTop()  # 主窗置顶

    def runClipboard(self, e=None):  # 识别剪贴板
        if not self.isMsnReady():  # 正在运行，不执行
            return
        clipData = Tool.getClipboardFormat()  # 读取剪贴板

        failFlag = False

        # 剪贴板中是位图（优先）
        if isinstance(clipData, int):
            self.startSingleClipboard()

        # 剪贴板中是文件列表（文件管理器中对着文件ctrl+c得到句柄）
        elif isinstance(clipData, tuple):
            # 检验文件列表中是否存在合法文件类型
            suf = Config.get('imageSuffix').split()  # 许可后缀列表
            flag = False
            for path in clipData:  # 检验文件列表中是否存在许可后缀
                if suf and os.path.splitext(path)[1].lower() in suf:
                    flag = True
                    break
            # 存在，则将文件载入主表并执行任务
            if flag:
                self.notebook.select(self.notebookTab[0])  # 转到主表卡
                self.gotoTop()  # 主窗置顶
                self.clearTable()  # 清空主表
                self.addImagesList(clipData)  # 添加到主表
                self.run()  # Commencement of mission任务
            else:
                failFlag = True
        else:  # 剪贴板中不是支持的格式
            failFlag = True

        if failFlag:
            self.errorOutput('Picture information not queried in clipboard')
            # 失败也置顶
            self.gotoTop()  # 主窗置顶
            self.notebook.select(self.notebookTab[1])  # 转到输出卡

    def runScreenshot(self):  # 进行截图
        if not self.isMsnReady() or not self.win.attributes('-disabled') == 0:
            return
        self.win.attributes("-disabled", 1)  # 禁用主窗口
        if Config.get('isScreenshotHideWindow'):  # 截图时隐藏主窗口
            self.win.state('iconic')
            self.win.after(Config.get('screenshotHideWindowWaitTime'),
                           ScreenshotCopy)  # 延迟，等待最小化完成再截屏
        else:
            ScreenshotCopy()  # 立即截屏

    def openScreenshot(self, e=None):  # 普通截图
        Config.set('isFinishSend', False)
        self.runScreenshot() 

    def openLinkageScreenshot(self, e=None):  # 联动截图
        Config.set('isFinishSend', True)
        self.runScreenshot() 

    def closeScreenshot(self, flag, errMsg=None):  # 关闭截图窗口，返回T表示已复制到剪贴板
        self.win.attributes("-disabled", 0)  # 启用父窗口
        if errMsg:
            self.errorOutput('Screenshot Failure', errMsg)
        if not flag and self.win.state() == 'normal':  # 截图不成功，但窗口非最小化
            self.gotoTop()  # 主窗置顶
        elif flag:  # 成功
            # self.win.after(50, self.runClipboard)
            self.startSingleClipboard()  # 剪贴板识图

    def onCloseWin(self):  # 关闭窗口事件
        if Config.get('isBackground'):
            self.win.withdraw()  # 隐藏窗口
        else:
            self.onClose()  # 直接关闭

    def onClose(self):  # 关闭软件
        OCRe.stop()  # 强制关闭引擎进程，加快子线程结束
        if OCRe.engFlag == EngFlag.none and OCRe.msnFlag == MsnFlag.none:  # 未在运行
            self.exit()
        else:
            self.win.after(50, self.waitClose)  # 等待关闭，50ms轮询一次是否Closed子线程

    def waitClose(self):  # 等待线程关闭后销毁窗口
        Log.info(f'Closed. Waiting. {OCRe.engFlag} | {OCRe.msnFlag}')
        if OCRe.engFlag == EngFlag.none and OCRe.msnFlag == MsnFlag.none:  # 未在运行
            self.exit()
        else:
            self.win.after(50, self.waitClose)  # 等待关闭，50ms轮询一次是否Closed子进程

    def exit(self):
        SysTray.stop()  # 关闭托盘。这个函数里有判断，不会造成无限递归。
        # 等待一段时间，保证托盘线程关闭，图标从系统注销
        # 然后强制终止主进程，防止引擎子线程苟且偷生
        self.win.after(100, lambda: os._exit(0))

    def showTips(self, tipsText):  # 显示提示
        if not self.isMsnReady():
            tk.messagebox.showwarning(
                'Task in progress', 'Please stop the task before opening the software Description')
            return
        self.notebook.select(self.notebookTab[1])  # 切换到输出选项卡
        outputNow = self.textOutput.get("1.0", tk.END)
        if outputNow and not outputNow == "\n":  # 输出面板内容存在，且不是单换行（初始状态）
            if not tkinter.messagebox.askokcancel('The prompt ', ' will clear the output panel. Want to continue?'):
                return
            self.panelClear()
        self.textOutput.insert(tk.END, tipsText)

# 全角空格：【　】
