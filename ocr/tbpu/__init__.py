# tbpu : text block processing unit
# Text Block Processing Unit

# An element of the result returned by OCR that contains text, enclosing boxes, and confidence levels is called a "text block".
# A text block is not necessarily a complete sentence or paragraph. Instead, it is usually fragmented text.
# An OCR result often consists of multiple text blocks.
# A text block processor is a processor that takes multiple incoming text blocks and processes them, such as merging, sorting, and deleting them.


# Conceptual parsing:
# Columns: a page may have a single column, double columns, multiple columns, the text blocks between different columns will not border. Blocks of text from different columns can never be merged.
# Paragraphs: a column may have multiple paragraphs, which may be distinguished by line spacing, starting space, etc. How to divide and merge paragraphs? How to divide paragraphs and how to merge them, different tbpu have different schemes.
# Lines: there may be multiple lines within a paragraph. They should be merged as much as possible.
# Blocks: text blocks are the smallest unit in OCR results, a line may be accidentally divided into multiple blocks, which is not normal and must be merged.

from utils.config import Config
from ocr.tbpu.merge_line_h import TbpuLineH
from ocr.tbpu.merge_line_h_fuzzy import TbpuLineHFuzzy
from ocr.tbpu.merge_line_h_m_left import TbpuLineHMultiLeft
from ocr.tbpu.merge_line_h_m_paragraph import TbpuLineHMultiParagraph
from ocr.tbpu.merge_line_h_m_paragraph_english import TbpuLineHMultiParagraphEnglish
from ocr.tbpu.merge_line_h_m_fuzzy import TbpuLineHMultiFuzzy
from ocr.tbpu.merge_line_v_lr import TbpuLineVlr
from ocr.tbpu.merge_line_v_rl import TbpuLineVrl


Tbpus = {
    'Optimize single line': TbpuLineH,
    'Combining multiple lines - natural paragraphs in Chinese': TbpuLineHMultiParagraph,
    'Merging of multiple lines - natural paragraphs in Spanish': TbpuLineHMultiParagraphEnglish,
    'Merge Multiple Lines - Left Alignment': TbpuLineHMultiLeft,
    'Optimize single line - fuzzy matching': TbpuLineHFuzzy,
    'Merge Multiple Lines - Fuzzy Matc': TbpuLineHMultiFuzzy,
    'Vertical - left to right - single line': TbpuLineVlr,
    'Vertical - right to left - single line': TbpuLineVrl,
    'leave sth. unprocessed': None,
}

Config.set('tbpu', Tbpus)
