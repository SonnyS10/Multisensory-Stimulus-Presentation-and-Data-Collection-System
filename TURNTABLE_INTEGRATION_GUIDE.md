# Turntable GUI Integration Guide

## Overview

The turntable GUI integration allows automatic control of the physical turntable during experiments. Instead of displaying 2D images on a screen, the system rotates the turntable to present physical objects to participants, automatically opening and closing bay doors.

## Features

- **Automatic Bay Mapping**: Objects are automatically assigned to specific turntable bays based on their names
- **Seamless Integration**: Works with existing test framework and stimulus order management
- **Synchronized Operation**: Follows the same timing patterns as display-based tests
- **Manual Controls**: Retains manual turntable control for setup and testing
- **Pause/Resume Support**: Full integration with main GUI control buttons

## Quick Start

1. **Setup Phase**:
   - Ensure turntable and door controllers are connected
   - Place physical objects in their assigned bays (see Bay Assignments below)
   - Start the main GUI application

2. **Running a Test**:
   - Select your desired test from the sidebar
   - **Check the "Viewing Booth" checkbox** instead of "Display"
   - Click "Start" button
   - The turntable GUI window will open automatically
   - Press SPACE bar to begin the test
   - The turntable will automatically move through the sequence

3. **During Test**:
   - Use Pause/Resume buttons in main GUI to control the test
   - The turntable will move to each bay, open doors, wait 2 seconds, then close doors
   - Status is displayed in both windows

## Bay Assignments

### Default Alcohol Objects (Bays 1-8)
| Bay | Object | Notes |
|-----|--------|-------|
| 1 | Beer | Generic beer bottle/can |
| 2 | Wine | Wine bottle |
| 3 | Vodka | Vodka bottle |
| 4 | Whiskey | Whiskey bottle |
| 5 | Stella | Stella Artois |
| 6 | Heineken | Heineken bottle |
| 7 | Budweiser | Budweiser bottle |
| 8 | Corona | Corona bottle |

### Default Neutral Objects (Bays 9-16)
| Bay | Object | Notes |
|-----|--------|-------|
| 9 | Water | Water bottle |
| 10 | Soda | Soda bottle/can |
| 11 | Juice | Juice container |
| 12 | Coffee | Coffee cup/container |
| 13 | Tea | Tea cup/container |
| 14 | Milk | Milk container |
| 15 | Cup | Generic cup |
| 16 | Bottle | Generic bottle |

### Custom Bay Assignments

You can customize bay assignments programmatically:

```python
from eeg_stimulus_project.stimulus.turn_table_code.bay_mapping import bay_mapper

# Assign a custom object to a specific bay
bay_mapper.set_custom_mapping('special_object', 7)  # Assigns to bay 8 (0-based indexing)
```

## File Organization

Objects should be named to match the bay assignments. The system uses intelligent matching:

- `beer.jpg`, `Beer.png`, `beer_bottle.jpg` → Bay 1
- `wine.jpg`, `Wine_Bottle.png`, `red_wine.jpg` → Bay 2
- `water.jpg`, `Water_Bottle.png`, `drinking_water.jpg` → Bay 9

## Integration with Stimulus Order

The turntable integration works seamlessly with the existing stimulus order management:

1. **Stimulus Order Frame**: Configure your test's stimulus order as usual
2. **Bay Sequence Generation**: The system automatically converts your stimulus list to a bay sequence
3. **Automatic Operation**: The turntable follows this sequence during the test

Example:
- Stimulus Order: `['beer.jpg', 'water.jpg', 'wine.jpg']`
- Bay Sequence: `[Bay 1, Bay 9, Bay 2]`
- Turntable Operation: Moves to Bay 1 → Bay 9 → Bay 2

## Hardware Requirements

- **Turntable Controller**: Pololu Tic stepper motor controller
- **Door Controller**: Secondary Tic controller for door mechanisms
- **USB Connections**: Both controllers connected via USB
- **Power Supply**: Appropriate power for stepper motors

## Software Components

### Core Files
- `bay_mapping.py`: Object-to-bay mapping system
- `turntable_gui.py`: Enhanced GUI with automatic mode
- `auto_turntable_window.py`: High-level controller
- `main_gui.py`: Integration with main application

### Hardware Interfaces
- `turntable_controller.py`: Turntable movement control
- `doorcode.py`: Door opening/closing control

## Troubleshooting

### Common Issues

1. **"No bay sequence set" error**:
   - Ensure objects in your stimulus order have recognizable names
   - Check bay mapping assignments
   - Verify stimulus order frame is properly configured

2. **Hardware not responding**:
   - Check USB connections to Tic controllers
   - Verify device IDs in controller files
   - Test manual controls first

3. **Timing issues**:
   - Adjust movement speeds in `turntable_controller.py`
   - Modify door timing in `doorcode.py`
   - Check for mechanical obstructions

### Testing Without Hardware

You can test the integration logic without physical hardware:

```bash
python test_turntable_integration.py  # Basic functionality
python test_integration_logic.py      # Integration logic
python demo_turntable_integration.py  # Full demonstration
```

## Advanced Configuration

### Timing Adjustments

Default timing per object:
- Move to bay: ~3 seconds
- Door operations: ~2 seconds  
- Display time: 2 seconds
- **Total per object**: ~7 seconds

Modify in `auto_turntable_window.py` and `turntable_gui.py`.

### Movement Parameters

Turntable movement settings in `turntable_controller.py`:
- `interval_steps`: Steps between bays (default: 200)
- `max_speed`: Maximum movement speed
- `max_accel`: Movement acceleration

### Door Parameters

Door operation settings in `doorcode.py`:
- `move_steps`: Door opening distance (default: -400)
- Motor current and speed settings

## Safety Considerations

- **Emergency Stop**: Always have manual stop capabilities
- **Clear Area**: Ensure turntable area is clear during operation
- **Supervision**: Maintain visual supervision during automatic operation
- **Testing**: Test all movements manually before using automatic mode

## Support

For issues or questions:
1. Check this documentation
2. Run the test scripts to verify functionality
3. Check hardware connections and configurations
4. Review system logs for error messages

The integration is designed to be robust and user-friendly while maintaining full compatibility with the existing experiment framework.