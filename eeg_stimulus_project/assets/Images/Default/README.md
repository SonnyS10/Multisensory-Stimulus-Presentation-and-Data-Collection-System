# Default Stimulus Images

This folder contains the default images used for alcohol and neutral stimuli in the experiment.

## Folder Structure

- **Alcohol/**: Contains alcohol-related stimulus images (e.g., beer, wine, liquor bottles, alcoholic drinks)
- **Neutral/**: Contains neutral stimulus images (e.g., water, juice, soft drinks, everyday objects)

## Image Guidelines

### Alcohol Stimuli
Place images that clearly represent alcoholic beverages:
- Beer bottles/cans/glasses
- Wine bottles/glasses
- Liquor bottles
- Cocktails
- Bar scenes with alcohol

**Naming Convention Examples:**
- `beer_bottle_1.jpg`
- `red_wine_glass.jpg`
- `whiskey_bottle.jpg`
- `beer_mug.jpg`

### Neutral Stimuli
Place images that represent non-alcoholic items with similar visual characteristics:
- Water bottles/glasses
- Juice bottles/cartons
- Soft drink cans/bottles
- Coffee/tea cups
- Everyday beverage containers

**Naming Convention Examples:**
- `water_bottle_1.jpg`
- `orange_juice_glass.jpg`
- `soda_can.jpg`
- `water_glass.jpg`

## Important Considerations

1. **Visual Similarity**: Neutral images should match alcohol images in terms of:
   - Image complexity
   - Color palette
   - Object size in frame
   - Background context
   - Overall visual appeal

2. **Image Quality**:
   - Use high-resolution images (minimum 800x600 pixels)
   - Ensure good lighting and clear focus
   - Avoid watermarks or text overlays

3. **Supported Formats**:
   - .jpg, .jpeg, .png, .bmp, .gif, .tiff, .webp

4. **Number of Images**:
   - Recommended: At least 10-15 images per category
   - More images allow for better randomization and reduced repetition effects

## How to Add Images

1. Place alcohol-related images in the `Alcohol/` folder
2. Place neutral images in the `Neutral/` folder
3. The system will automatically load all images from these folders
4. No code changes needed - just add the image files!

## Current Defaults

If no images are found in these folders, the system will fall back to:
- **Alcohol**: Beer.jpg and Stella.jpg from the parent Images folder
- **Neutral**: Images from the Personalized folder

## Testing Your Images

After adding images:
1. Launch the experiment GUI
2. Go to "Stimulus Order Management" in the sidebar
3. Select a test to verify your images appear in the available assets
4. The alcohol tests should show images from the Alcohol folder
5. The neutral tests should show images from the Neutral folder
