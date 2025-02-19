from PIL import Image, ImageTk
import os 

#Global Variables
Beer = Image.open(os.path.join(os.path.dirname(__file__), 'Images', 'Beer.jpg'))
class Display():
    test_assets = {
        'Unisensory Neutral Visual': [Beer],
        'Unisensory Alcohol Visual': [Beer],
        'MultiSensory Alcohol Visual & Olfactory': [Beer],
        'MultiSensory Neutral Visual & Olfactory': [Beer],
        'MultiSensory Alcohol Visual, Tactile & Olfactory' : [Beer],
        'MultiSensory Neutral Visual, Tactile & Olfactory' : [Beer] 
    }

    
    