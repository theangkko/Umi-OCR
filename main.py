# Python 3.8.10
# (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)] on win32

from utils.config import Umi
from ui.win_main import MainWin

Umi.ver = '1.3.5'
Umi.pname = 'Umi-OCR'
Umi.name = f'{Umi.pname} v{Umi.ver}'
Umi.website = 'https://github.com/hiroi-sora/Umi-OCR'
Umi.about = 'Free, open-source offline OCR software'


def main():
    MainWin()


if __name__ == "__main__":
    main()

# Packaging to_exe.py
