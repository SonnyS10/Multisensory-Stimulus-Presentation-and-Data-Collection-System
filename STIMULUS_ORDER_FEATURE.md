# Stimulus Order Management Feature

## Overview

The Stimulus Order Management feature provides users with an advanced way to rearrange and view the order that visual stimuli (images) will be presented during experiments. This feature allows fine-grained control over stimulus presentation order through an intuitive drag-and-drop interface.

## Feature Location

The feature is accessible through a new "Stimulus Order" button in the sidebar of the main GUI, positioned below the "Latency Checker" button.

## Functionality

### Main Features

1. **Test Selection**: Choose from any of the 10 available tests:
   - 6 Passive Viewing Tests
   - 4 Stroop Tests

2. **Visual Image Order Display**: View the current order of images for the selected test with thumbnail previews

3. **Drag-and-Drop Rearrangement**: Rearrange images by dragging and dropping them in the desired order

4. **Reset to Original Order**: Restore the original/default order for any test

5. **Apply Custom Order**: Confirm and apply the custom arrangement for use in experiments

## How It Works

### User Interface Components

- **Test Selector Dropdown**: Choose which test to configure
- **Image List**: Displays images in their current order with:
  - Thumbnail previews (when available)
  - Numbered sequence (1st, 2nd, 3rd, etc.)
  - Descriptive names based on image filenames
- **Control Buttons**:
  - "Reset to Original Order": Restore default ordering
  - "Apply Custom Order": Save and activate the custom arrangement

### Backend Integration

The feature integrates seamlessly with the existing codebase:

- **Asset Handler Integration**: Modified `asset_handler.py` to support custom ordering
- **Priority System**: Custom orders take precedence over randomization
- **Persistence**: Custom orders are maintained throughout the session

## Usage Instructions

### Basic Usage

1. **Access the Feature**:
   - Click the "Stimulus Order" button in the sidebar
   - The stimulus order management frame will open

2. **Select a Test**:
   - Use the dropdown to choose which test to configure
   - The image list will populate with the current order

3. **Rearrange Images**:
   - Click and drag images to reorder them
   - The numbering will update automatically
   - First image in the list will be shown first during the test

4. **Save Changes**:
   - Click "Apply Custom Order" to save your arrangement
   - A confirmation message will appear
   - The custom order will be used when running that test

5. **Reset if Needed**:
   - Click "Reset to Original Order" to restore defaults
   - Confirm when prompted

### Advanced Usage

- **Multiple Test Configuration**: Configure different orders for different tests
- **Session Persistence**: Custom orders remain active until the application is closed
- **Randomization Override**: Custom orders take priority over randomization settings

## Technical Implementation

### Files Modified

1. **`eeg_stimulus_project/gui/stimulus_order_frame.py`** (NEW):
   - Main UI component for stimulus order management
   - Handles drag-and-drop functionality
   - Manages custom order storage and retrieval

2. **`eeg_stimulus_project/gui/sidebar.py`**:
   - Added "Stimulus Order" button
   - Connected to main GUI toggle function

3. **`eeg_stimulus_project/gui/main_gui.py`**:
   - Integrated StimulusOrderFrame into stacked widget
   - Added toggle functionality
   - Added custom order update method

4. **`eeg_stimulus_project/assets/asset_handler.py`**:
   - Added custom order storage class variables
   - Modified `get_assets()` to check for custom orders
   - Added methods for setting/getting custom orders

### Key Classes and Methods

- **`StimulusOrderFrame`**: Main UI component
- **`Display.set_custom_orders()`**: Set custom order preferences
- **`Display.get_custom_orders()`**: Retrieve current custom orders
- **`GUI.toggle_stimulus_order()`**: Show/hide the stimulus order frame
- **`GUI.update_custom_orders()`**: Update custom orders from the frame

## Benefits

1. **Precise Control**: Researchers can control exact stimulus presentation order
2. **Easy to Use**: Intuitive drag-and-drop interface
3. **Flexible**: Different orders for different tests
4. **Non-Destructive**: Original orders can always be restored
5. **Session Persistent**: Custom orders remain active during the session
6. **Backwards Compatible**: Existing functionality remains unchanged

## Future Enhancements

Potential future improvements could include:

- **Persistent Storage**: Save custom orders to configuration files
- **Order Templates**: Create and save reusable order templates
- **Batch Operations**: Apply the same order to multiple tests
- **Import/Export**: Share custom orders between researchers
- **Visual Previews**: Enhanced image previews with metadata

## Testing

The feature includes comprehensive tests:

- **Unit Tests**: Test core functionality and integration
- **GUI Tests**: Verify user interface components
- **Integration Tests**: Ensure proper interaction with existing systems

## Compatibility

The feature is designed to be:

- **Backwards Compatible**: Existing experiments work unchanged
- **Optional**: Can be ignored if not needed
- **Minimal Impact**: Small footprint on existing codebase
- **Robust**: Handles edge cases gracefully