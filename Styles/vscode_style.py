# ./themes/vscode_style.py

from pygments.style import Style
from pygments.token import (
    Comment, Keyword, Name, String, Error, Number, Operator, Generic
)


class VSCodeStyle(Style):
    default_style = ""
    styles = {
        Comment: 'italic #6A9955',
        Keyword: 'bold #569CD6',
        Name: '#DCDCAA',
        Name.Function: '#DCDCAA',
        Name.Class: 'bold #4EC9B0',
        String: '#CE9178',
        Error: 'border:#F44747',
        Number: '#B5CEA8',
        Operator: '#D4D4D4',
        Generic.Heading: 'bold #569CD6',
        Generic.Subheading: 'bold #4EC9B0',
        Generic.Deleted: '#F44747',
        Generic.Inserted: '#B5CEA8',
        Generic.Error: '#F44747',
        Generic.Emph: 'italic',
        Generic.Strong: 'bold',
    }
