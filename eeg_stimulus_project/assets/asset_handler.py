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
    ## Print the order after shuffling
    #print("Order of images after shuffling:")
    #for img in mixed_images:
    #    if hasattr(img, 'filename'):
    #        print(os.path.splitext(os.path.basename(img.filename))[0])
    #    else:
    #        print(img)
    return mixed_images

class Display():
    @staticmethod
    def get_assets(alcohol_folder=None, non_alcohol_folder=None):
        # Use user folders if provided, else use defaults
        if alcohol_folder and os.path.isdir(alcohol_folder):
            alcohol_images = load_images_from_folder(alcohol_folder)
        else:
            alcohol_images = [Beer, Stella]

        if non_alcohol_folder and os.path.isdir(non_alcohol_folder):
            non_alcohol_images = load_images_from_folder(non_alcohol_folder)
        else:
            non_alcohol_images = personalized_images

        # Build test_assets dict as before, but use these lists
        test_assets = {
            'Unisensory Neutral Visual': get_mixed_images(non_alcohol_images, []),
            'Unisensory Alcohol Visual': get_mixed_images(alcohol_images, []),
            'Multisensory Neutral Visual & Olfactory': get_mixed_images([], personalized_images),
            'Multisensory Alcohol Visual & Olfactory': get_mixed_images([Beer], personalized_images),
            'Multisensory Neutral Visual, Tactile & Olfactory': get_mixed_images([Beer], personalized_images),
            'Multisensory Alcohol Visual, Tactile & Olfactory': get_mixed_images([Beer], personalized_images),
            'Stroop Multisensory Alcohol (Visual & Tactile)': get_mixed_images([Beer], personalized_images),
            'Stroop Multisensory Alcohol (Visual & Olfactory)': get_mixed_images([Beer], personalized_images),
            'Stroop Multisensory Neutral (Visual & Tactile)': get_mixed_images([Beer], personalized_images),
            'Stroop Multisensory Neutral (Visual & Olfactory)': get_mixed_images([Beer], personalized_images),
        }
        return test_assets