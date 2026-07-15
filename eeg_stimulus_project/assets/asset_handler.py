from PIL import Image
import os
import random

# Global Variables - Load fallback images only if they exist
def load_fallback_images():
    """Load hardcoded fallback images if they exist."""
    fallback_images = []
    beer_path = os.path.join(os.path.dirname(__file__), 'Images', 'Beer.jpg')
    stella_path = os.path.join(os.path.dirname(__file__), 'Images', 'Stella.jpg')
    
    if os.path.exists(beer_path):
        try:
            beer = Image.open(beer_path)
            beer.filename = beer_path
            fallback_images.append(beer)
        except Exception as e:
            print(f"Warning: Could not load Beer.jpg: {e}")
    
    if os.path.exists(stella_path):
        try:
            stella = Image.open(stella_path)
            stella.filename = stella_path
            fallback_images.append(stella)
        except Exception as e:
            print(f"Warning: Could not load Stella.jpg: {e}")
    
    return fallback_images

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
try:
    personalized_folder = os.path.join(os.path.dirname(__file__), 'Images', 'Personalized')
except Exception as e:
    print(f"Error determining personalized images folder: {e}")
    personalized_folder = None
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
    STROOP_PRACTICE_TESTS = {
        'Stroop Practice Neutral (Visual & Tactile)',
        'Stroop Practice Neutral (Visual & Olfactory)',
    }
    
    @staticmethod
    def randomize_images(images, randomize_cues=False, seed=None, repetitions=None):
        #print(f"Randomize called: {randomize_cues}, seed={seed}, images={len(images)}")
        images = images.copy()
        # Apply repetitions if specified
        if repetitions:
            expanded_images = []
            for img in images:
                fname = getattr(img, 'filename', None)
                base_name = os.path.splitext(os.path.basename(fname))[0] if fname else None
                count = repetitions.get(base_name, 1)
                expanded_images.extend([img] * count)
            images = expanded_images
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
    def get_assets(alcohol_folder=None, non_alcohol_folder=None, randomize_cues=False, seed=None, repetitions=None):
        #print(
        #   f"get_assets called with:\n"
        #    f"  alcohol_folder={alcohol_folder}\n"
        #    f"  non_alcohol_folder={non_alcohol_folder}\n"
        #    f"  randomize_cues={randomize_cues}\n"
        #    f"  seed={seed}\n"
        #    f"  repetitions={repetitions}\n"
        #)
        # Define default folders with separate alcohol and neutral directories
        default_alcohol_folder = os.path.join(os.path.dirname(__file__), 'Images', 'Default', 'Alcohol')
        default_neutral_folder = os.path.join(os.path.dirname(__file__), 'Images', 'Default', 'Neutral')
        
        # Get fallback images
        fallback_images = load_fallback_images()
        
        # Load alcohol images - ALWAYS include default, then add custom
        alcohol_images = []
        
        # First, load from default folder if it exists
        if os.path.isdir(default_alcohol_folder):
            default_alcohol = load_images_from_folder(default_alcohol_folder)
            alcohol_images.extend(default_alcohol)
        
        # Then, add from custom folder if provided
        if alcohol_folder and os.path.isdir(alcohol_folder):
            custom_alcohol = load_images_from_folder(alcohol_folder)
            alcohol_images.extend(custom_alcohol)
        
        # If still no images, use fallback
        if not alcohol_images:
            alcohol_images = fallback_images if fallback_images else []
        
        # Load non-alcohol (neutral) images - ALWAYS include default, then add custom
        non_alcohol_images = []
        
        # First, load from default folder if it exists
        if os.path.isdir(default_neutral_folder):
            default_neutral = load_images_from_folder(default_neutral_folder)
            non_alcohol_images.extend(default_neutral)
        
        # Then, add from custom folder if provided
        if non_alcohol_folder and os.path.isdir(non_alcohol_folder):
            custom_neutral = load_images_from_folder(non_alcohol_folder)
            non_alcohol_images.extend(custom_neutral)
        
        # If still no images, use fallback
        if not non_alcohol_images:
            non_alcohol_images = personalized_images if personalized_images else []

        # Warning if no images found
        if not alcohol_images:
            print("WARNING: No alcohol stimulus images found! Please add images to:")
            print(f"  - {default_alcohol_folder}")
            print("  - Or specify a custom folder in the main GUI")
        
        if not non_alcohol_images:
            print("WARNING: No neutral stimulus images found! Please add images to:")
            print(f"  - {default_neutral_folder}")
            print("  - Or specify a custom folder in the main GUI")

        # Build test_assets dict as before, but randomize if needed
        test_assets = {}
        for test_name, (general, personalized) in {
            'Unisensory Neutral Visual': (non_alcohol_images, []),
            'Unisensory Alcohol Visual': (alcohol_images, []),
            'Multisensory Neutral Visual & Olfactory': (non_alcohol_images, personalized_images),
            'Multisensory Alcohol Visual & Olfactory': (alcohol_images, personalized_images),
            'Multisensory Neutral Visual, Tactile & Olfactory': (non_alcohol_images, personalized_images),
            'Multisensory Alcohol Visual, Tactile & Olfactory': (alcohol_images, personalized_images),
            'Stroop Practice Neutral (Visual & Tactile)': (non_alcohol_images, []),
            'Stroop Practice Neutral (Visual & Olfactory)': (non_alcohol_images, []),
            'Stroop Multisensory Alcohol (Visual & Tactile)': (alcohol_images, personalized_images),
            'Stroop Multisensory Alcohol (Visual & Olfactory)': (alcohol_images, personalized_images),
            'Stroop Multisensory Neutral (Visual & Tactile)': (non_alcohol_images, personalized_images),
            'Stroop Multisensory Neutral (Visual & Olfactory)': (non_alcohol_images, personalized_images),
        }.items():
            #print(f"Custom order for {test_name}: {test_name in Display.custom_orders}")
            mixed = get_mixed_images(general, personalized)
            if test_name in Display.custom_orders:
                test_assets[test_name] = Display.custom_orders[test_name]
            else:
                randomized, used_seed = Display.randomize_images(mixed, randomize_cues, seed, repetitions)
                if test_name in Display.STROOP_PRACTICE_TESTS:
                    randomized = randomized[:5]
                test_assets[test_name] = randomized
        return test_assets
