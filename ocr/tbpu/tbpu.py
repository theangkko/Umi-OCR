# tbpu : text block processing unit
# The base class of a text block processor.
# An element of the result returned by OCR that contains text, enclosing boxes, and confidence levels is called a "text block".
# A text block is not necessarily a complete sentence or paragraph. Instead, it is usually fragmented text.
# An OCR result often consists of multiple text blocks.
# A text block processor is a processor that takes multiple incoming text blocks and processes them, such as merging, sorting, and deleting them.

from utils.logger import GetLog
Log = GetLog()


class Tbpu:
    def __init__(self):
        self.tbpuName = 'Block processing unit -- unknown'

    def getInitInfo(self):
        '''返回初始化信息字符串'''
        return f'Text block reprocessing：[{self.tbpuName}]'

    def run(self, textBlocks, img):
        '''输入：textBlocks文块 , img图片信息\n
        输出：textBlocks文块 , 处理日志'''
        Log.info(f'f: {textBlocks}')
        return textBlocks, f'[{self.tbpuName}]'
