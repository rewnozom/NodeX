# Guide: Converting PySide6 GUI Applications to Dynamic Page Format

## Prerequisites
- Your GUI application should be in a single Python file (e.g., `gui.py`)
- The application should use PySide6
- You have access to the DynamicMain base pages module

## Step 1: File Structure
```
your_page_directory/
├── gui.py           # Your original GUI application
└── Page.py         # The new page wrapper
```

## Step 2: Page.py Implementation
```python
from frontend.DynamicMain.base_pages import BasePage
from . import gui  # Relative import from same directory

class Page(BasePage):
    def init_ui(self):
        super().init_ui()
        self.app = gui.App()
        self.app.setStyleSheet("")  # Prevent theme conflicts
        self.layout.addWidget(self.app)
    
    def on_load(self):
        super().on_load()
        if hasattr(self, 'app'):
            gui.QTimer.singleShot(0, self.app.setup_ui)
            gui.QTimer.singleShot(100, self.app.setup_connections)

    def on_unload(self):
        super().on_unload()
        if hasattr(self, 'app'):
            self.app.closeEvent(gui.QEvent(gui.QEvent.Type.Close))
```

## Step 3: GUI Requirements
Your GUI application must:
1. Have a main `App` class inheriting from `QMainWindow`
2. Contain `setup_ui()` and `setup_connections()` methods
3. Handle cleanup in `closeEvent()`

## Common Issues
1. **Theme Conflicts**: Set empty stylesheet on app instance
2. **Import Errors**: Use relative imports (from . import gui)
3. **Missing Cleanup**: Ensure closeEvent handles resource cleanup

## Testing
1. Place both files in your pages directory
2. Restart the dynamic application
3. The page should appear in navigation menu
4. Test all functionality remains intact

## Example GUI Structure
```python
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        
    def setup_ui(self):
        # UI initialization
        pass
        
    def setup_connections(self):
        # Signal/slot connections
        pass
        
    def closeEvent(self, event):
        # Cleanup
        pass
```