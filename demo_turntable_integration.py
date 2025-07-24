#!/usr/bin/env python3
"""
Turntable Integration Demo

This script demonstrates the key features of the turntable integration
without requiring the full GUI or hardware setup.
"""

import sys
import os
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_bay_mapping():
    """Demonstrate the bay mapping functionality."""
    print("🎯 Bay Mapping Demonstration")
    print("=" * 50)
    
    from eeg_stimulus_project.stimulus.turn_table_code.bay_mapping import bay_mapper
    
    # Sample objects that might be used in experiments
    sample_objects = [
        'beer.jpg', 'wine.png', 'vodka.jpg', 'whiskey.jpg',
        'water.jpg', 'soda.png', 'juice.jpg', 'coffee.jpg',
        'stella.jpg', 'heineken.png', 'unknown_item.jpg'
    ]
    
    print("Default bay assignments:")
    for obj in sample_objects:
        bay = bay_mapper.get_bay_for_object(obj)
        if bay is not None:
            print(f"  📁 {obj:<20} → Bay {bay + 1:>2}")
        else:
            print(f"  📁 {obj:<20} → No mapping (defaults to Bay 1)")
    
    print("\nCustom mapping example:")
    bay_mapper.set_custom_mapping('special_item', 7)
    bay = bay_mapper.get_bay_for_object('special_item')
    print(f"  📁 special_item        → Bay {bay + 1} (custom)")
    
    print()

def demo_stimulus_sequence():
    """Demonstrate how stimulus sequences are converted to bay sequences."""
    print("🔄 Stimulus Sequence Demonstration")
    print("=" * 50)
    
    from eeg_stimulus_project.stimulus.turn_table_code.bay_mapping import bay_mapper
    
    # Mock asset class (represents what comes from Display.get_assets())
    class MockAsset:
        def __init__(self, filename):
            self.filename = filename
    
    class MockCravingAsset:
        def __init__(self):
            self.asset_type = 'craving_rating'
    
    # Sample test sequences
    test_sequences = [
        {
            'name': 'Alcohol Visual Test',
            'assets': [
                MockAsset('beer.jpg'),
                MockAsset('wine.jpg'), 
                MockAsset('vodka.jpg'),
                MockCravingAsset()  # This gets skipped
            ]
        },
        {
            'name': 'Neutral Visual Test',
            'assets': [
                MockAsset('water.jpg'),
                MockAsset('soda.jpg'),
                MockAsset('juice.jpg'),
                MockCravingAsset()
            ]
        },
        {
            'name': 'Mixed Tactile Test',
            'assets': [
                MockAsset('beer.jpg'),
                MockAsset('water.jpg'),
                MockAsset('wine.jpg'),
                MockAsset('coffee.jpg')
            ]
        }
    ]
    
    for sequence in test_sequences:
        print(f"Test: {sequence['name']}")
        
        # Show stimulus order
        stimuli = [getattr(a, 'filename', 'craving_rating') for a in sequence['assets']]
        print(f"  Stimuli: {stimuli}")
        
        # Generate bay sequence
        bay_sequence = bay_mapper.get_bay_sequence_for_assets(sequence['assets'])
        bay_display = [f"Bay {b+1}" for b in bay_sequence]
        print(f"  Bays:    {bay_display}")
        
        # Show turntable sequence
        print("  Sequence:")
        for i, bay in enumerate(bay_sequence):
            stimulus_name = os.path.splitext(os.path.basename(stimuli[i]))[0]
            print(f"    {i+1}. Move to Bay {bay+1} → Open doors → Show {stimulus_name} → Close doors")
        
        print()

def demo_integration_flow():
    """Demonstrate the integration flow with the main GUI."""
    print("🔗 Main GUI Integration Flow")
    print("=" * 50)
    
    print("1. User selects test in main GUI")
    print("   └─ 'Unisensory Alcohol Visual'")
    print()
    
    print("2. User checks 'Viewing Booth' checkbox")
    print("   └─ Triggers turntable mode instead of display mode")
    print()
    
    print("3. User clicks 'Start' button")
    print("   ├─ Frame.start_button_clicked() detects viewing_booth_button.isChecked()")
    print("   ├─ Calls parent.open_turntable_gui(Qt.Checked, ...)")
    print("   └─ Creates AutoTurntableWindow with bay sequence")
    print()
    
    print("4. AutoTurntableWindow initialization")
    print("   ├─ Gets stimulus assets for current test")
    print("   ├─ Generates bay sequence using bay_mapper")
    print("   ├─ Creates TurntableWindow with auto_mode=True")
    print("   └─ Shows 'Press SPACE to begin' instructions")
    print()
    
    print("5. User presses SPACE to start")
    print("   ├─ Countdown: 3... 2... 1... Go!")
    print("   ├─ Calls turntable_window.start_auto_test()")
    print("   └─ Begins automatic sequence")
    print()
    
    print("6. Automatic turntable sequence")
    print("   For each bay in sequence:")
    print("   ├─ Move turntable to bay")
    print("   ├─ Open doors")
    print("   ├─ Wait 2 seconds")
    print("   ├─ Close doors")
    print("   └─ Continue to next bay")
    print()
    
    print("7. Pause/Resume/Stop controls")
    print("   ├─ Main GUI pause button → AutoTurntableWindow.pause_trial()")
    print("   ├─ Main GUI resume button → AutoTurntableWindow.resume_trial()")
    print("   └─ Main GUI stop button → Closes turntable window")
    print()
    
    print("8. Test completion")
    print("   ├─ All bays visited")
    print("   ├─ Emits test_complete signal")
    print("   └─ Returns to ready state")
    print()

def demo_timing_example():
    """Show example timing for a test sequence."""
    print("⏱️  Example Timing Sequence")
    print("=" * 50)
    
    # Sample sequence
    bays = [1, 2, 9]  # beer, wine, water
    objects = ['beer', 'wine', 'water']
    
    print("Test sequence: Alcohol vs Neutral comparison")
    print()
    
    start_time = 0
    for i, (bay, obj) in enumerate(zip(bays, objects)):
        print(f"Object {i+1}: {obj}")
        print(f"  T+{start_time:>3}s: Move to Bay {bay}")
        print(f"  T+{start_time+3:>3}s: Open doors")
        print(f"  T+{start_time+3:>3}s: Participant observes {obj}")
        print(f"  T+{start_time+5:>3}s: Close doors")
        print(f"  T+{start_time+6:>3}s: Ready for next")
        start_time += 7  # 7 seconds per object
        print()
    
    print(f"Total test duration: ~{start_time}s ({start_time//60}:{start_time%60:02d})")
    print()

def main():
    """Run all demonstrations."""
    print("🎪 Turntable GUI Integration Demo")
    print("=" * 70)
    print()
    
    try:
        demo_bay_mapping()
        demo_stimulus_sequence()
        demo_integration_flow()
        demo_timing_example()
        
        print("✅ Demo completed successfully!")
        print()
        print("The turntable integration is ready for use.")
        print("To test with real hardware:")
        print("1. Ensure turntable and door controllers are connected")
        print("2. Run the main GUI application")
        print("3. Select a test and check 'Viewing Booth'")
        print("4. Click 'Start' to begin automatic turntable operation")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())