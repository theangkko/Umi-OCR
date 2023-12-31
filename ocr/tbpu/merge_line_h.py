# text block processing：Horizontal - single line
from ocr.tbpu.tbpu import Tbpu

from time import time


class TbpuLineH(Tbpu):
    def __init__(self):
        super().__init__()
        self.tbpuName = 'Horizontal - single line'
        self.isLimitX = True  # 为T时，考虑文块水平距离

    def getInitInfo(self):
        return f'Text block reprocessing：[{self.tbpuName}]'

    def merge2text(self, text1, text2):
        '''Rules for merging two paragraphs'''
        return text1 + text2

    def run(self, textBlocks, imgInfo):
        '''Pass in the block group and image information. Returns the text block group, debug message string.'''
        timeIn = time()
        # All text blocks, sorted by the x-coordinate of the point in the upper left corner
        textBlocks.sort(key=lambda tb: tb['box'][0][0])
        # Iterate through each text block to find the item in the subsequent block that borders it and has the same row height, merge the two blocks
        resList = []
        listlen = len(textBlocks)
        for index in range(listlen):
            tb = textBlocks[index]
            if not tb:
                continue
            box = tb['box']
            bx, by = box[1][0], box[1][1]  # Upper right corner xy
            bh = box[3][1] - box[0][1]  # your height
            limitX, limitY = bh, round(bh/2)  # x, y merge threshold, row height, half row height
            num = 1  # Number of mergers
            # Iterate over subsequent blocks of text
            for i in range(index+1, listlen):
                tb2 = textBlocks[i]
                if not tb2:
                    continue
                box2 = tb2['box']
                b2x, b2y = box2[0][0], box2[0][1]  # 左上角xy
                b2h = box2[3][1] - box2[0][1]  # 行高
                if not self.isLimitX:  # 不考虑水平差距
                    limitX = 999999
                # 文块1的右上角与文块2的左上角接壤，且二者行高一致，则合并
                if abs(b2x-bx) < limitX and abs(b2y-by) < limitY and abs(b2h-bh) < limitY:
                    num += 1
                    # 合并两个文块box
                    yTop = min(box[0][1], box[1][1], box2[0][1], box2[1][1])
                    yBottom = max(box[2][1], box[3][1], box2[2][1], box2[3][1])
                    box[0][1] = box[1][1] = yTop  # y上
                    box[2][1] = box[3][1] = yBottom  # y下
                    box[0][0] = box[3][0] = min(box[0][0], box[3][0])  # x左
                    box[1][0] = box[2][0] = max(box2[1][0], box2[2][0])  # x右
                    # 刷新临时变量
                    bx, by = box[1][0], box[1][1]  # 右上角xy
                    bh = box[3][1] - box[0][1]  # 行高
                    limitX, limitY = bh, round(bh/2)  # x、y 合并阈值，行高、行高一半
                    # 合并内容
                    tb['score'] += tb2['score']  # 合并置信度
                    # tb['text'] += tb2['text']  # 合并文本
                    tb['text'] = self.merge2text(  # 合并文本
                        tb['text'], tb2['text'])
                    textBlocks[i] = None  # 置为空，标记删除
            if num > 1:
                tb['score'] /= num  # 平均置信度
            resList.append(tb)  # 装填入结果
        # 所有新文块，按左上角点的y坐标从高到低排序
        resList.sort(key=lambda tb: tb['box'][0][1])
        # Returns the new text block group and debug string.
        return resList, f'[{self.tbpuName}]Original {listlen} block, merged {len(resList)} block, time consuming{time()-timeIn}s'
