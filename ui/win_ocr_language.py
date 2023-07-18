# 更改OCR语言
from ui.widget import Widget  # control
from utils.config import Config
from utils.asset import Asset  # resource
from utils.data_structure import KeyList
from utils.hotkey import Hotkey
from utils.logger import GetLog

import tkinter as tk
from tkinter import ttk

Log = GetLog()


class OcrLanguageWin:
    def __init__(self):
        self.lanList = KeyList()
        self.win = None

    def _initWin(self):
        # main window
        self.win = tk.Toplevel()
        self.win.iconphoto(False, Asset.getImgTK('umiocr24'))  # Setting the window icon
        self.win.minsize(250, 340)  # minimum size
        self.win.geometry(f'{250}x{340}')
        self.win.unbind('<MouseWheel>')
        self.win.title('Change Language')
        self.win.wm_protocol(  # Register window close event
            'WM_DELETE_WINDOW', self.exit)
        fmain = tk.Frame(self.win, padx=4, pady=4)
        fmain.pack(fill='both', expand=True)

        # 顶部信息
        ftop = tk.Frame(fmain)
        ftop.pack(side='top', fill='x')
        tk.Label(ftop, text='present：').pack(side='left')
        tk.Label(ftop, textvariable=Config.getTK(
            'ocrConfigName')).pack(side='left')
        wid = tk.Label(ftop, text='prompt', fg='deeppink', cursor='question_arrow')
        wid.pack(side='right')
        Config.main.balloon.bind(
            wid, '''Window Operation:
1. When normal, switching language takes effect immediately
2. If you switch language during the task, it will take effect in the next task.
3. After enabling/cancelling the topping of the main window, you need to re-open this window to make this window set to the corresponding topping status.

More languages:
This software has organised multi-language expansion packs, you can import more language model libraries. You can also
manually import PaddleOCR-compatible model libraries, please visit the project's Github page for details.''')

        # 中部控制
        fmiddle = tk.Frame(fmain, pady=4)
        fmiddle.pack(side='top', expand=True, fill='both')
        fmiddle.grid_columnconfigure(0, weight=1)

        # 语言表格
        ftable = tk.Frame(fmiddle, bg='red')
        ftable.pack(side='left', expand=True, fill='both')
        self.table = ttk.Treeview(
            master=ftable,  # parent container
            # height=50,  # The number of rows displayed in the table, the height of the rows and the number of rows in the table.
            columns=['ConfigName'],  # Columns displayed
            show='headings',  # Hide the first column
        )
        self.table.pack(expand=True, side='left', fill='both')
        self.table.heading('ConfigName', text='language')
        self.table.column('ConfigName', minwidth=40)
        vbar = tk.Scrollbar(  # Binding scrollbars
            ftable, orient='vertical', command=self.table.yview)
        vbar.pack(side='left', fill='y')
        self.table["yscrollcommand"] = vbar.set
        self.table.bind('<ButtonRelease-1>',  # Bind mouse release. When pressed, it first allows the form component to update, and it is released to get the latest value
                        lambda *e: self.updateLanguage())

        # fmright = tk.Frame(fmiddle)
        # fmright.pack(side='left', fill='y')
        # tk.Label(fmright, text='右侧').pack(side='left')

        # 底部控制
        fbottom = tk.Frame(fmain)
        fbottom.pack(side='top', fill='x')
        Widget.comboboxFrame(fbottom, 'Merge paragraphs：', 'tbpu').pack(
            side='top', fill='x', pady=3)
        wid = ttk.Checkbutton(fbottom, variable=Config.getTK('isLanguageWinAutoOcr'),
                              text='Know Your Maps Now')
        wid.pack(side='left')
        Config.main.balloon.bind(wid, 'Immediately after modifying the language, a clipboard reading is performed in the current language.')
        wid = ttk.Button(fbottom, text='disable', width=5,
                         command=self.exit)
        wid.pack(side='right')
        wid = ttk.Checkbutton(fbottom, variable=Config.getTK('isLanguageWinAutoExit'),
                              text='auto-off')
        wid.pack(side='right', padx=10)
        Config.main.balloon.bind(wid, 'Close this window immediately after changing the language')

        self.updateTable()

    def open(self):
        if self.win:
            self.win.state('normal')  # Restore foreground state
        else:
            self._initWin()  # Initialising the window
        self.win.attributes('-topmost', 1)  # Setting the top of the hierarchy
        if Config.get('isWindowTop'):
            self.win.title('Change language (top)')
        else:
            self.win.title('Change Language')
            self.win.attributes('-topmost', 0)  # lift
        # Window moves near the mouse
        (x, y) = Hotkey.getMousePos()
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        if w < 2:
            w = 250
        if h < 2:
            h = 340
        w1 = self.win.winfo_screenwidth()
        h1 = self.win.winfo_screenheight()
        x -= round(w/2)
        y -= 140
        # Preventing windows from exceeding the screen
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x > w1-w:
            x = w1-w
        if y > h1-h-70:
            y = h1-h-70
        self.win.geometry(f"+{x}+{y}")

    def updateTable(self):  # Refresh Language Form
        configDist = Config.get('ocrConfig')
        configName = Config.get('ocrConfigName')
        for key, value in configDist.items():
            tableInfo = (key)
            dictInfo = {'key': key}
            id = self.table.insert('', 'end', values=tableInfo)  # 添加到表格组件中
            self.lanList.append(id, dictInfo)
            if key == configName:
                self.table.selection_set(id)

    def updateLanguage(self):  # 刷新选中语言，写入配置
        chi = self.table.selection()
        if len(chi) == 0:
            return
        chi = chi[0]
        lan = self.lanList.get(key=chi)['key']
        Config.set('ocrConfigName', lan)
        if Config.get('isLanguageWinAutoExit'):  # 自动关闭
            self.exit()
        if Config.get('isLanguageWinAutoOcr'):  # 重复任务
            Config.main.runClipboard()

    def exit(self):
        self.win.withdraw()  # 隐藏窗口


lanWin = OcrLanguageWin()


def ChangeOcrLanguage():
    lanWin.open()
