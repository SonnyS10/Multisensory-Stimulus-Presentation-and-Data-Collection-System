"""
Stimulus Order Management Frame
This module provides a GUI interface for managing the order of stimulus presentation
for each test. Users can view and rearrange the order of images through drag-and-drop.
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QListWidget, QListWidgetItem, QFrame, QMessageBox, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
from eeg_stimulus_project.assets.asset_handler import Display


class StimulusOrderFrame(QWidget):
    """
    A frame that allows users to view and rearrange the order of stimulus presentation
    for each test using drag-and-drop functionality.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_test_name = None
        self.custom_orders = {}  # Store custom orders for each test
        self.original_assets = {}  # Store original asset order
        
        # Load current assets
        self.load_current_assets()
        
        # Setup UI
        self.setup_ui()
        
        # Set default test
        if self.test_selector.count() > 0:
            self.test_selector.setCurrentIndex(0)
            self.on_test_selected()
    
    def setup_ui(self):
        """Setup the user interface components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Stimulus Order Management")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Test selection
        test_layout = QHBoxLayout()
        test_label = QLabel("Select Test:")
        test_label.setFont(QFont("Segoe UI", 12))
        test_layout.addWidget(test_label)
        
        self.test_selector = QComboBox()
        self.test_selector.setFont(QFont("Segoe UI", 11))
        self.test_selector.setMinimumWidth(400)
        self.test_selector.currentTextChanged.connect(self.on_test_selected)
        
        # Populate test selector with available tests
        test_names = [
            'Unisensory Neutral Visual',
            'Unisensory Alcohol Visual',
            'Multisensory Neutral Visual & Olfactory',
            'Multisensory Alcohol Visual & Olfactory',
            'Multisensory Neutral Visual, Tactile & Olfactory',
            'Multisensory Alcohol Visual, Tactile & Olfactory',
            'Stroop Multisensory Alcohol (Visual & Tactile)',
            'Stroop Multisensory Neutral (Visual & Tactile)',
            'Stroop Multisensory Alcohol (Visual & Olfactory)',
            'Stroop Multisensory Neutral (Visual & Olfactory)'
        ]
        
        for test_name in test_names:
            self.test_selector.addItem(test_name)
        
        test_layout.addWidget(self.test_selector)
        test_layout.addStretch()
        layout.addLayout(test_layout)
        
        # Instructions
        instructions = QLabel(
            "Drag and drop images to rearrange their presentation order. "
            "The first image will be shown first during the test."
        )
        instructions.setFont(QFont("Segoe UI", 10))
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(instructions)
        
        # Image list
        list_frame = QFrame()
        list_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        list_layout = QVBoxLayout(list_frame)
        
        list_label = QLabel("Image Order (drag to rearrange):")
        list_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        list_layout.addWidget(list_label)
        
        self.image_list = QListWidget()
        self.image_list.setDragDropMode(QListWidget.InternalMove)
        self.image_list.setDefaultDropAction(Qt.MoveAction)
        self.image_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
        """)
        self.image_list.setMinimumHeight(300)
        list_layout.addWidget(self.image_list)
        
        layout.addWidget(list_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_button = QPushButton("Reset to Original Order")
        reset_button.setFont(QFont("Segoe UI", 11))
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        reset_button.clicked.connect(self.reset_to_original)
        button_layout.addWidget(reset_button)
        
        button_layout.addStretch()
        
        apply_button = QPushButton("Apply Custom Order")
        apply_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        apply_button.clicked.connect(self.apply_custom_order)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def load_current_assets(self):
        """Load current assets from the asset handler."""
        try:
            # Get assets without randomization to maintain original order
            self.original_assets = Display.get_assets(
                alcohol_folder=None,
                non_alcohol_folder=None,
                randomize_cues=False,
                seed=None
            )
        except Exception as e:
            print(f"Error loading assets: {e}")
            self.original_assets = {}
    
    def on_test_selected(self):
        """Handle test selection change."""
        self.current_test_name = self.test_selector.currentText()
        self.update_image_list()
    
    def update_image_list(self):
        """Update the image list widget with current test's images."""
        if not self.current_test_name or self.current_test_name not in self.original_assets:
            return
        
        self.image_list.clear()
        
        # Use custom order if available, otherwise use original order
        if self.current_test_name in self.custom_orders:
            images = self.custom_orders[self.current_test_name]
        else:
            images = self.original_assets[self.current_test_name]
        
        for i, image in enumerate(images):
            item = QListWidgetItem()
            
            # Get image filename for display
            if hasattr(image, 'filename'):
                filename = os.path.basename(image.filename)
                display_name = os.path.splitext(filename)[0]
                
                # Try to create a thumbnail
                try:
                    pixmap = QPixmap(image.filename)
                    if not pixmap.isNull():
                        # Scale to thumbnail size
                        thumbnail = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(thumbnail))
                except Exception as e:
                    print(f"Error creating thumbnail for {filename}: {e}")
                
                item.setText(f"{i+1}. {display_name}")
            else:
                item.setText(f"{i+1}. Image {i+1}")
            
            # Store the original image object in the item data
            item.setData(Qt.UserRole, image)
            self.image_list.addItem(item)
    
    def reset_to_original(self):
        """Reset the current test to its original image order."""
        if not self.current_test_name:
            return
        
        reply = QMessageBox.question(
            self,
            "Reset Order",
            f"Are you sure you want to reset the order for '{self.current_test_name}' to the original order?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove custom order if it exists
            if self.current_test_name in self.custom_orders:
                del self.custom_orders[self.current_test_name]
            
            # Update the display
            self.update_image_list()
    
    def apply_custom_order(self):
        """Apply the current order as the custom order for the selected test."""
        if not self.current_test_name:
            return
        
        # Get current order from the list widget
        current_order = []
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            image = item.data(Qt.UserRole)
            current_order.append(image)
        
        # Store the custom order
        self.custom_orders[self.current_test_name] = current_order
        
        # Update the parent's asset handler to use custom order
        if hasattr(self.parent, 'update_custom_orders'):
            self.parent.update_custom_orders(self.custom_orders)
        
        QMessageBox.information(
            self,
            "Order Applied",
            f"Custom order applied for '{self.current_test_name}'. "
            f"This order will be used when running the test."
        )
    
    def get_custom_orders(self):
        """Return the current custom orders."""
        return self.custom_orders.copy()