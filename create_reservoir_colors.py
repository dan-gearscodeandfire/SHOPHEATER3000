#!/usr/bin/env python3
"""
Script to create colored versions of the reservoir image.
Creates orange (warm) and red (hot) versions by replacing blue water colors.
"""

from PIL import Image
import os

def replace_blue_with_color(input_path, output_path, target_color):
    """
    Replace blue-ish pixels in the image with a target color.
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image
        target_color: RGB tuple for replacement color (e.g., (255, 136, 0) for orange)
    """
    # Open the image
    img = Image.open(input_path)
    img = img.convert('RGBA')  # Ensure RGBA mode
    
    # Get pixel data
    pixels = img.load()
    width, height = img.size
    
    print(f"Processing {input_path} -> {output_path}")
    print(f"Image size: {width}x{height}")
    print(f"Target color: RGB{target_color}")
    
    # Count pixels changed
    changed_count = 0
    
    # Iterate through all pixels
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            # Check if pixel is blue-ish (blue component is dominant)
            # We want to replace light blue water, so check for:
            # - Blue component is higher than red and green
            # - Pixel is not too dark (not black/gray)
            # - Alpha is not fully transparent
            if a > 50:  # Not transparent
                # Check if it's a shade of blue or cyan
                # Blue should be higher than red, and reasonably bright
                if b > r and b > g and b > 100:
                    # Calculate the brightness/intensity to preserve
                    # Use the blue component as the reference
                    intensity = b / 255.0
                    
                    # Apply the target color with the same intensity
                    new_r = int(target_color[0] * intensity)
                    new_g = int(target_color[1] * intensity)
                    new_b = int(target_color[2] * intensity)
                    
                    pixels[x, y] = (new_r, new_g, new_b, a)
                    changed_count += 1
    
    print(f"Changed {changed_count} pixels")
    
    # Save the result
    img.save(output_path)
    print(f"Saved to {output_path}\n")

def main():
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, 'images')
    
    input_file = os.path.join(images_dir, '256_reservoir.png')
    warm_file = os.path.join(images_dir, '256_reservoir_warm.png')
    hot_file = os.path.join(images_dir, '256_reservoir_hot.png')
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return 1
    
    # Define colors (matching arrow colors from web UI)
    ORANGE = (255, 136, 0)  # #FF8800
    RED = (255, 51, 51)     # #FF3333
    
    # Create warm version (orange water)
    replace_blue_with_color(input_file, warm_file, ORANGE)
    
    # Create hot version (red water)
    replace_blue_with_color(input_file, hot_file, RED)
    
    print("✅ Successfully created colored reservoir images!")
    print(f"   - {warm_file}")
    print(f"   - {hot_file}")
    
    return 0

if __name__ == '__main__':
    exit(main())
