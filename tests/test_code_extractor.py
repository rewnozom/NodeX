import pytest
from ai_agent.utils.code_extractor import CodeBlockExtractor

def test_extract_code_blocks():
    extractor = CodeBlockExtractor()
    text = """
    ```python
    def test():
        return True
    ```
    ```javascript
    function test() {
        return true;
    }
    ```
    """
    blocks = extractor.extract_code_blocks(text)
    assert len(blocks) == 2
    assert blocks[0]['language'] == 'python'
    assert 'def test()' in blocks[0]['code']
    assert blocks[1]['language'] == 'javascript'

def test_extract_inline_code():
    extractor = CodeBlockExtractor()
    text = "This is `inline code` and `more code`"
    blocks = extractor.extract_inline_code(text)
    assert len(blocks) == 2
    assert blocks[0]['language'] == 'inline'
    assert "inline code" in blocks[0]['code']

def test_code_analysis():
    extractor = CodeBlockExtractor()
    block = {
        'language': 'python',
        'code': 'def test():\n    return True'
    }
    result = extractor.process_code_block(block)
    assert isinstance(result.syntax_highlighted, str)
    assert isinstance(result.complexity, float)
    assert isinstance(result.todos, list)
