# text block processing：Horizontal - Single Line - Fuzzy Match
from ocr.tbpu.merge_line_h import TbpuLineH


class TbpuLineHFuzzy(TbpuLineH):
    def __init__(self):
        super().__init__()
        self.tbpuName = 'Horizontal - Single Line - Fuzzy Match'
        self.isLimitX = False  # 不考虑文块水平距离

    def merge2text(self, text1, text2):
        '''合并两段文字的规则'''
        return text1 + ' ' + text2
