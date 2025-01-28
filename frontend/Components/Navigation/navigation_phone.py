# ./components/navigation_phone.py



from PySide6.QtCore import Qt, Signal, QSize  # Added QSize import
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import ( QFrame, QListWidget, QListWidgetItem, QMenu,
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QSpacerItem, QSizePolicy, QScrollArea, QGroupBox,
    QToolButton, QHBoxLayout
)
from Config.AppConfig.icon_config import ICONS
from log.logger import logger

class Navigation_Phone_Menu(QFrame):
    """
    Mobile-friendly navigation menu with collapsible sections and touch-friendly controls.
    """
    
    menuToggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.is_expanded = False
        self.pages = []
        
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header bar (always visible)
        self._init_header_bar()
        
        # Collapsible content
        self._init_collapsible_content()
        
        # Set initial collapsed state
        self.collapsible_widget.setVisible(False)
        
    def _init_header_bar(self):
        """Initialize the header bar with menu toggle."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Menu toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setIcon(QIcon(ICONS.get('menu', '')))
        self.toggle_button.setIconSize(QSize(24, 24))  # Changed from Qt.QSize to QSize
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        header_layout.addWidget(self.toggle_button)
        
        # Current page label
        self.current_page_label = QLabel("Menu")
        self.current_page_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        header_layout.addWidget(self.current_page_label)
        
        self.main_layout.addWidget(header_widget)
        
    def _init_collapsible_content(self):
        """Initialize the collapsible menu content."""
        self.collapsible_widget = QWidget()
        collapsible_layout = QVBoxLayout(self.collapsible_widget)
        collapsible_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scrollable area for menu items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Menu content
        menu_widget = QWidget()
        self.menu_layout = QVBoxLayout(menu_widget)
        self.menu_layout.setSpacing(2)
        
        scroll_area.setWidget(menu_widget)
        collapsible_layout.addWidget(scroll_area)
        
        self.main_layout.addWidget(self.collapsible_widget)
        
    def _connect_signals(self):
        """Connect signals to slots."""
        self.toggle_button.clicked.connect(self.toggle_menu)
        
    def toggle_menu(self):
        """Toggle the menu expansion state."""
        self.is_expanded = not self.is_expanded
        self.collapsible_widget.setVisible(self.is_expanded)
        
        # Update toggle button icon
        icon_name = 'close' if self.is_expanded else 'menu'
        self.toggle_button.setIcon(QIcon(ICONS.get(icon_name, '')))
        
        self.menuToggled.emit(self.is_expanded)
        
    def update_page_list(self, pages):
        """Update the list of available pages."""
        self.pages = pages
        self._create_page_buttons()
        
    def _create_page_buttons(self):
        """Create touch-friendly page buttons."""
        # Clear existing buttons
        for i in reversed(range(self.menu_layout.count())):
            widget = self.menu_layout.itemAt(i).widget()
            if widget:
                self.menu_layout.removeWidget(widget)
                widget.deleteLater()
        
        # Create new buttons
        for page_name in self.pages:
            btn = QPushButton(page_name.replace("_", " ").capitalize())
            btn.setMinimumHeight(48)  # Touch-friendly height
            
            # Add icon
            icon_key = page_name.lower()
            icon_path = ICONS.get(icon_key, '')
            if icon_path:
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(24, 24))  # Changed from Qt.QSize to QSize
            
            # Connect click handler
            btn.clicked.connect(
                lambda checked=False, name=page_name: self._handle_page_click(name)
            )
            
            self.menu_layout.addWidget(btn)
            
        self.menu_layout.addStretch()
        
    def _handle_page_click(self, page_name):
        """Handle page selection and collapse menu."""
        # Update current page label
        self.current_page_label.setText(page_name.replace("_", " ").capitalize())
        
        # Collapse menu
        self.is_expanded = False
        self.collapsible_widget.setVisible(False)
        self.toggle_button.setIcon(QIcon(ICONS.get('menu', '')))
        
        # Load the page
        self.parent.load_page(page_name)