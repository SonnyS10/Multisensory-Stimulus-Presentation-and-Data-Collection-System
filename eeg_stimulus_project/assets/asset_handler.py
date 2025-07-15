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

def get_mixed_images(general_images, personalized_images):
    mixed_images = general_images.copy()
    mixed_images.extend(personalized_images)
    return mixed_images

class Display():
    custom_orders = {}  # Class variable to store custom image orders
    
    @staticmethod
    def randomize_images(images, randomize_cues=False, seed=None):
        images = images.copy()
        if randomize_cues:
            if not seed:
                # Generate a random seed if none is provided
                seed = random.randint(0, 10000)
            rnd = random.Random(seed)
            rnd.shuffle(images)
        return images, seed
    
    @staticmethod
    def set_custom_orders(custom_orders):
        """Set custom orders for tests."""
        Display.custom_orders = custom_orders.copy()
    
    @staticmethod
    def get_custom_orders():
        """Get current custom orders."""
        return Display.custom_orders.copy()

    @staticmethod
    def get_assets(alcohol_folder=None, non_alcohol_folder=None, randomize_cues=False, seed=None):
        # Use user folders if provided, else use defaults
        if alcohol_folder and os.path.isdir(alcohol_folder):
            alcohol_images = load_images_from_folder(alcohol_folder)
        else:
            alcohol_images = [Beer, Stella]

        if non_alcohol_folder and os.path.isdir(non_alcohol_folder):
            non_alcohol_images = load_images_from_folder(non_alcohol_folder)
        else:
            non_alcohol_images = personalized_images

        # Build test_assets dict as before, but randomize if needed
        test_assets = {}

        # Example for each test type:
        for test_name, (general, personalized) in {
            'Unisensory Neutral Visual': (non_alcohol_images, []),
            'Unisensory Alcohol Visual': (alcohol_images, []),
            'Multisensory Neutral Visual & Olfactory': ([], personalized_images),
            'Multisensory Alcohol Visual & Olfactory': ([Beer], personalized_images),
            'Multisensory Neutral Visual, Tactile & Olfactory': ([Beer], personalized_images),
            'Multisensory Alcohol Visual, Tactile & Olfactory': ([Beer], personalized_images),
            'Stroop Multisensory Alcohol (Visual & Tactile)': ([Beer], personalized_images),
            'Stroop Multisensory Alcohol (Visual & Olfactory)': ([Beer], personalized_images),
            'Stroop Multisensory Neutral (Visual & Tactile)': ([Beer], personalized_images),
            'Stroop Multisensory Neutral (Visual & Olfactory)': ([Beer], personalized_images),
        }.items():
            mixed = get_mixed_images(general, personalized)
            
            # Check if there's a custom order for this test
            if test_name in Display.custom_orders:
                test_assets[test_name] = Display.custom_orders[test_name]
            else:
                # Use randomization if enabled and no custom order
                randomized, used_seed = Display.randomize_images(mixed, randomize_cues, seed)
                test_assets[test_name] = randomized
            # Optionally, you could store used_seed somewhere if you want to log/display it

        return test_assets