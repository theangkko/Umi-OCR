# 启动方式相关设置
from utils.logger import GetLog
from utils.config import Config, Umi
from utils.asset import Asset

import os
import tkinter as tk
import winshell

Log = GetLog()


class ShortcutApi:
    '''Operation Shortcuts'''
    @staticmethod  # 询问是否静默启动。返回T为静默启动，F为正常显示窗口
    def askStartupNoWin(action):
        flag = not tk.messagebox.askyesno(
            'enquiry', f'Is the main window displayed when the software is opened via {action}? \n\nYes: Normal display of the main window \n No: Silent startup, stowed in the tray area')
        if flag and not Config.get('isTray'):  # 当前配置不显示托盘，则自动启用托盘
            Config.set('isTray', True)
        return flag

    @staticmethod  # 添加
    def add(path, name, arguments=''):
        '''创建快捷方式'''
        winshell.CreateShortcut(
            Path=f'{path}\\{name}.lnk',
            Target=Umi.path,
            Description=name,
            Icon=(os.path.realpath(Asset.getPath('umiocrico')), 0),
            Arguments=arguments
        )

    @staticmethod  # 删除
    def remove(path, name):
        '''Delete all shortcuts containing name in the target path, return the number of deleted shortcuts.'''
        num = 0  # successes个数
        subFiles = os.listdir(path)  # 遍历目录下所有文件
        for s in subFiles:
            if name in s and s.endswith('.lnk'):
                os.remove(path + '\\'+s)  # 删除文件
                num += 1
        return num

    @ staticmethod  # 切换
    def switch(action, path, configItem):
        '''切换快捷方式。动作名称 | 放置路径 | 设置项名称 | successes添加时额外提示'''
        flag = Config.get(configItem)
        if flag:
            name = Umi.name
            Log.info(f'Ready to add a shortcut. Name [{name}], destination path [{path}].')
            try:
                arguments = ''
                if ShortcutApi.askStartupNoWin(action):
                    arguments = '-hide'
                ShortcutApi.add(path, name, arguments)
                tk.messagebox.showinfo('successes', f'{name} Added to{action}')
            except Exception as e:
                Config.set(configItem, False)
                tk.messagebox.showerror(
                    'A small problem was encountered', f'Failed to create shortcut. Please run the software with administrator privileges and retry. \n\nTarget path: {path}\nError message: {e}')
        else:
            name = Umi.pname  # 纯名称，无视版本号移除所有相关快捷方式
            Log.info(f'Prepare to remove the shortcut. Name [{name}], destination path [{path}].')
            try:
                num = ShortcutApi.remove(path, name)
                if num == 0:
                    tk.messagebox.showinfo('prompts', f'{name} non-existent{action}')
                elif num > 0:
                    tk.messagebox.showinfo(
                        'successes', f'{name} Removed{num}个{action}')
            except Exception as e:
                tk.messagebox.showerror(
                    'Had a little problem.', f'Failed to delete the shortcut. Please run the software with administrator privileges and retry. \n\nTarget path: {path}\nError message: {e}')
        if Config.get('isDebug'):
            os.startfile(path)  # 调试模式，打开对应文件夹


class Startup:
    '''各种启动方式'''

    @ staticmethod
    def switchAutoStartup():
        '''切换开机自启'''
        ShortcutApi.switch('boot item', winshell.startup(), 'isAutoStartup')

    @ staticmethod
    def switchStartMenu():
        '''切换开始菜单快捷方式'''
        ShortcutApi.switch('start menu', winshell.programs(), 'isStartMenu')

    @ staticmethod
    def switchDesktop():
        '''切换桌面快捷方式'''
        ShortcutApi.switch('desktop shortcut', winshell.desktop(), 'isDesktop')
