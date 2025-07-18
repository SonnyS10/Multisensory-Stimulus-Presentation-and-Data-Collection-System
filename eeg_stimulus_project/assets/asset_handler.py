from PIL import Image
import os
import random

# Global Variables
Beer = Image.open(os.path.join(os.path.dirname(__file__), 'Images', 'Beer.jpg'))
Stella = Image.open(os.path.join(os.path.dirname(__file__), 'Images', 'Stella.jpg'))

# Function to load images from a folder
def load_images_from_folder(folder):
    supported_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
    images = []
    for fname in os.listdir(folder):
        if fname.lower().endswith(supported_exts):
            path = os.path.join(folder, fname)
            try:
                img = Image.open(path)
                img.filename = path  # Attach the filename attribute for later reference
                images.append(img)
            except Exception as e:
                print(f"Error loading image {path}: {e}")
    return images

# Load personalized images
personalized_folder = os.path.join(os.path.dirname(__file__), 'Images', 'Personalized')
personalized_images = load_images_from_folder(personalized_folder)

def get_mixed_images(general_images, personalized_images):
    # Avoid duplicates by using a set of filenames
    seen = set()
    mixed_images = []
    for img in general_images + personalized_images:
        fname = getattr(img, 'filename', None)
        if fname and fname not in seen:
            mixed_images.append(img)
            seen.add(fname)
        elif not fname:
            mixed_images.append(img)  # If no filename, just add
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
        def_images_folder = os.path.join(os.path.dirname(__file__), 'Images', 'Default')
        # Load backup default images
        backup_default_images = []
        if os.path.isdir(def_images_folder):
            backup_default_images = load_images_from_folder(def_images_folder)
        # Load alcohol images
        if alcohol_folder and os.path.isdir(alcohol_folder):
            alcohol_images = load_images_from_folder(alcohol_folder)
            if not alcohol_images:
                alcohol_images = backup_default_images if backup_default_images else [Beer, Stella]
        else:
            alcohol_images = backup_default_images if backup_default_images else [Beer, Stella]
        # Load non-alcohol images
        if non_alcohol_folder and os.path.isdir(non_alcohol_folder):
            non_alcohol_images = load_images_from_folder(non_alcohol_folder)
            if not non_alcohol_images:
                non_alcohol_images = backup_default_images if backup_default_images else personalized_images
        else:
            non_alcohol_images = backup_default_images if backup_default_images else personalized_images

        # Build test_assets dict as before, but randomize if needed
        test_assets = {}

        for test_name, (general, personalized) in {
            'Unisensory Neutral Visual': (non_alcohol_images, []),
            'Unisensory Alcohol Visual': (alcohol_images, []),
            'Multisensory Neutral Visual & Olfactory': (non_alcohol_images, personalized_images),
            'Multisensory Alcohol Visual & Olfactory': (alcohol_images, personalized_images),
            'Multisensory Neutral Visual, Tactile & Olfactory': (non_alcohol_images, personalized_images),
            'Multisensory Alcohol Visual, Tactile & Olfactory': (alcohol_images, personalized_images),
            'Stroop Multisensory Alcohol (Visual & Tactile)': (alcohol_images, personalized_images),
            'Stroop Multisensory Alcohol (Visual & Olfactory)': (alcohol_images, personalized_images),
            'Stroop Multisensory Neutral (Visual & Tactile)': (non_alcohol_images, personalized_images),
            'Stroop Multisensory Neutral (Visual & Olfactory)': (non_alcohol_images, personalized_images),
        }.items():
            mixed = get_mixed_images(general, personalized)
            # Check if there's a custom order for this test
            if test_name in Display.custom_orders:
                test_assets[test_name] = Display.custom_orders[test_name]
            else:
                randomized, used_seed = Display.randomize_images(mixed, randomize_cues, seed)
                test_assets[test_name] = randomized

        return test_assets