from PIL import Image
import os
import random

# Global Variables
Beer = Image.open(os.path.join(os.path.dirname(__file__), 'Images', 'Beer.jpg'))
Stella = Image.open(os.path.join(os.path.dirname(__file__), 'Images', 'Stella.jpg'))

# Function to load images from a folder
def load_images_from_folder(folder):
    images = []
    for filename in os.listdir(folder):
        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            img = Image.open(os.path.join(folder, filename))
            images.append(img)
    return images

# Load personalized images
personalized_folder = os.path.join(os.path.dirname(__file__), 'Images', 'Personalized')
personalized_images = load_images_from_folder(personalized_folder)

# Mix personalized images with general images
def get_mixed_images(general_images, personalized_images):
    mixed_images = general_images.copy()
    mixed_images.extend(personalized_images)
    random.shuffle(mixed_images)
    return mixed_images

class Display():
    test_assets = {
        'Unisensory Neutral Visual': get_mixed_images([Beer, Stella], personalized_images),
        'Unisensory Alcohol Visual': get_mixed_images([Beer, Stella], personalized_images),
        'Multisensory Neutral Visual & Olfactory': get_mixed_images([], personalized_images),
        'Multisensory Alcohol Visual & Olfactory': get_mixed_images([Beer], personalized_images),
        'Multisensory Neutral Visual, Tactile & Olfactory': get_mixed_images([Beer], personalized_images),
        'Multisensory Alcohol Visual, Tactile & Olfactory': get_mixed_images([Beer], personalized_images),
        'Multisensory Alcohol (Visual & Tactile)': get_mixed_images([Beer], personalized_images),
        'Multisensory Alcohol (Visual & Olfactory)': get_mixed_images([Beer], personalized_images),
        'Multisensory Neutral (Visual & Tactile)': get_mixed_images([Beer], personalized_images),
        'Multisensory Neutral (Visual & Olfactory)': get_mixed_images([Beer], personalized_images),
    }