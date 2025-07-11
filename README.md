# Multisensory Stimulus Presentation and Data Collection System

Overview:
Software system for presenting and synchronizing multisensory stimuli (visual, tactile, olfactory) while collecting EEG, eye tracking, and behavioral data.

System Requirements:
PsychoPy,
Perception Toolbox for Virtual Reality (PTVR),
EMOTIV Pro software,
SR Research eye tracking software,
Lab Streaming Layer (LSL),
Arduino IDE (for turntable control).

Hardware Components:
HTC VIVE Pro Eye VR headset,
EMOTIV EPOC Flex (32-channel EEG),
Eyelink 1000 Plus eye tracker,
Custom odor delivery system,
Custom tactile presentation box,
Arduino-controlled viewing booth.

# Software Architecture

Stimulus Presentation System:
PsychoPy: Core stimulus presentation,
PTVR: VR integration and control,
Arduino Controller: Turntable and viewing booth control,
Custom Scripts: Odor delivery system control.

Data Collection System:
EMOTIV Pro: EEG data acquisition,
SR Research Software: Eye tracking data collection,
LSL Framework: Data synchronization.

Key Features:
Synchronized multisensory stimulus presentation,
Real-time data collection and synchronization,
Variable interstimulus interval control,
Automated trial sequencing,
Response time measurement,
Craving rating collection.
