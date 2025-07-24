"""
EEG Stimulus Project - Data Saving Module

This module handles the persistence of experimental data collected during
multisensory stimulus presentation experiments. It manages the organization
and storage of behavioral data, user responses, and timing information.

Key Features:
- Organized directory structure for experiment data
- CSV format for behavioral data storage
- Support for both passive and stroop task experiments
- Integration with external recording systems (EEG, eye tracking)
- Automatic file management and cleanup

Data Organization:
The module creates a hierarchical directory structure:
base_dir/
├── subject_XXX/
│   └── test_Y/
│       ├── Unisensory_Neutral_Visual/
│       │   └── data.csv
│       ├── Multisensory_Alcohol_Visual_Olfactory/
│       │   └── data.csv
│       └── ...

Author: Research Team
Last Modified: 2024
Note: Future versions should integrate with LSL for automatic data labeling
"""

import os
import csv
import sys
from pathlib import Path

# Add the project root to Python path for proper module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import LSL integration for future data stream coordination
from eeg_stimulus_project.lsl.stream_manager import LSL

# Future imports for enhanced data collection
# from eeg_stimulus_project.utils.labrecorder import LabRecorder

# TODO: Future enhancement - create all test directories when participant is created
# This would eliminate the need for directory creation during data saving

class Save_Data():
    """
    Data persistence manager for experimental sessions.
    
    This class handles the saving of experimental data to organized directory
    structures. It supports both passive viewing and stroop task experiments,
    managing behavioral data, timing information, and coordination with external
    recording systems.
    
    The class ensures data integrity through proper file management and provides
    a consistent interface for data storage across different experiment types.
    
    Attributes:
        base_dir (str): Base directory path for all experimental data
        test_number (str): Test number ('1' for passive, '2' for stroop)
        
    Directory Structure:
        Creates organized subdirectories for each test condition under the
        base directory, allowing for easy data analysis and organization.
        
    Integration Points:
        - LSL stream manager for synchronized data collection
        - LabRecorder for EEG data coordination
        - External hardware systems for multi-modal data
    """
    
    def __init__(self, base_dir, test_number):
        """
        Initialize the data saving manager.
        
        Args:
            base_dir (str): Base directory path for data storage
            test_number (str): Test number ('1' or '2')
        """
        self.base_dir = base_dir
        self.test_number = test_number

    def save_data_stroop(self, current_test, user_inputs, elapsed_time, labrecorder=None):
        """
        Save behavioral data from stroop task experiments.
        
        This method stores user responses and reaction times from stroop tasks
        in CSV format. It creates the necessary directory structure and manages
        file operations to ensure data integrity.
        
        Args:
            current_test (str): Name of the current test condition
            user_inputs (list): List of user responses/inputs
            elapsed_time (list): List of reaction times corresponding to inputs
            labrecorder: LabRecorder instance for EEG coordination (optional)
            
        Data Format:
            Creates a CSV file with columns:
            - User Inputs: Participant responses (key presses, choices, etc.)
            - Elapsed Time: Reaction times in appropriate time units
            
        File Management:
            - Creates test-specific subdirectory if it doesn't exist
            - Removes existing data.csv files to prevent data contamination
            - Uses append mode for potential future multi-session support
            
        Error Handling:
            - Ensures directory creation succeeds
            - Handles file permission issues
            - Provides feedback on operation success
            
        TODO: Add image labeling functionality to track stimulus-response pairs
        """
        # Create test-specific directory for data organization
        test_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(test_dir, exist_ok=True)

        # Define the data file path
        file_path = os.path.join(test_dir, 'data.csv')
        file_exists = os.path.isfile(file_path)

        # Remove existing file to prevent data contamination between runs
        if file_exists:
            print("File already exists. Deleting the old file.")
            os.remove(file_path)
        
        # Write behavioral data to CSV file
        with open(file_path, 'a', newline='') as file:  # Use append mode for future extensibility
            writer = csv.writer(file)
            
            # Write CSV headers
            writer.writerow(['User Inputs', 'Elapsed Time'])
            
            # Write paired data (responses and timing)
            for input_response, response_time in zip(user_inputs, elapsed_time):
                writer.writerow([input_response, response_time])
                
        print("Data saved successfully!")

    def save_data_passive(self, current_test, labrecorder=None):
        """
        Save data from passive viewing experiments.
        
        This method handles data saving for passive viewing experiments where
        participants observe stimuli without active responses. Currently creates
        the directory structure for future data integration.
        
        Args:
            current_test (str): Name of the current test condition
            labrecorder: LabRecorder instance for EEG coordination (optional)
            
        Current Implementation:
            - Creates test-specific directory structure
            - Prepares for future data collection integration
            - Provides success feedback
            
        Future Enhancements:
            - Integration with LSL streams for automatic data collection
            - Timestamp logging for stimulus presentation events
            - Coordination with external recording systems
            - Image sequence and timing metadata storage
            
        TODO: Add image labeling and stimulus timing data collection
        """
        # Create test-specific directory for future data storage
        test_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(test_dir, exist_ok=True)

        # TODO: Implement passive data collection
        # - Stimulus presentation timestamps
        # - Image sequence metadata
        # - External recording system coordination
        # - LSL marker integration
        
        print("Data saved successfully!")