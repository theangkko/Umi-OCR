# text block processing：Horizontal - Combine Multiple Lines - English Natural Paragraphs
from ocr.tbpu.merge_line_h_m_paragraph import TbpuLineHMultiParagraph


class TbpuLineHMultiParagraphEnglish(TbpuLineHMultiParagraph):
    def __init__(self):
        super().__init__()
        self.tbpuName = 'Horizontal - Combine Multiple Lines - English Natural Paragraphs'

    def merge2text(self, text1, text2):
        '''合并两段文字的规则'''
        return text1 + ' ' + text2
