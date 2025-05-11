from PIL import Image, ImageDraw, ImageFont
from utils import settings
from utils.fonts import getheight
from utils.console import print_step, print_substep
import os
import textwrap


def get_text_dimensions(text_string, font):
    """Gets the width and height of a string for a given font."""
    try:
        bbox = font.getbbox(text_string)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height
    except AttributeError: # Fallback for older Pillow
        try:
            width, height = font.getsize(text_string)
            return width, height
        except AttributeError:
            print_step("Warning: Could not determine text dimensions. Using fallback.")
            return len(text_string) * 10, 20 # Crude fallback

def getheight(font, text_line):
    """Helper to get only height, consistent with original usage."""
    _, height = get_text_dimensions(text_line, font)
    return height

def find_image_content_horizontal_bounds(image, alpha_threshold=10, rgb_background_color=(255, 255, 255)):
    """
    Finds the horizontal pixel bounds of the non-background content in an image.
    Returns (min_x_content, max_x_content_exclusive).
    max_x_content_exclusive is suitable for draw.rectangle's x1 or slicing.
    """
    if not image:
        return 0, 0

    img_width, img_height = image.size
    min_x = img_width  # Start with min_x beyond the right edge
    max_x = -1         # Start with max_x before the left edge

    # Ensure image is in a mode we can easily work with for pixel access
    # If not RGBA or RGB, convert. This simplifies pixel checking.
    # For PNGs, 'P' mode with transparency is also common.
    img_to_scan = image
    if image.mode not in ['RGB', 'RGBA']:
        if 'A' in image.mode or (image.mode == 'P' and 'transparency' in image.info):
            img_to_scan = image.convert('RGBA')
            print_step(f"Converted image from {image.mode} to RGBA for content bounds detection.")
        else:
            img_to_scan = image.convert('RGB')
            print_step(f"Converted image from {image.mode} to RGB for content bounds detection.")
    
    pixels = img_to_scan.load()
    scan_mode = img_to_scan.mode

    for y in range(img_height):
        row_min_x = -1
        # Scan from left for current row
        for x in range(img_width):
            px = pixels[x, y]
            is_content = False
            if scan_mode == 'RGBA':
                if px[3] > alpha_threshold: # Check alpha channel
                    is_content = True
            elif scan_mode == 'RGB':
                if px != rgb_background_color: # Check if not background color
                    is_content = True
            # Add other mode checks if necessary, e.g., for 'L' mode
            elif scan_mode == 'L': # Grayscale
                if px < rgb_background_color[0] - alpha_threshold: # Assuming white is background
                    is_content = True


            if is_content:
                row_min_x = x
                if x < min_x:
                    min_x = x
                break # Found first content pixel from left in this row
        
        if row_min_x != -1: # If content was found in this row from the left
            # Scan from right for current row (only up to where content was first found)
            for x in range(img_width - 1, row_min_x - 1, -1):
                px = pixels[x, y]
                is_content = False
                if scan_mode == 'RGBA':
                    if px[3] > alpha_threshold:
                        is_content = True
                elif scan_mode == 'RGB':
                    if px != rgb_background_color:
                        is_content = True
                elif scan_mode == 'L':
                    if px < rgb_background_color[0] - alpha_threshold:
                         is_content = True

                if is_content:
                    if x > max_x:
                        max_x = x
                    break # Found first content pixel from right in this row
                        
    if min_x > max_x : # No content found, or image was empty
        print_step("Content bounds: No discernible content found or image is empty/background.")
        return 0, img_width # Default to full image width for the band
    
    return min_x, max_x + 1 # max_x + 1 to make it exclusive for rectangle drawing
# --- End of assumed dependencies ---

def create_fancy_thumbnail(image, text, text_color, padding, wrap=35, is_user=False):
    print_step(f"Creating fancy thumbnail for: {text}")

    # --- 1. Font, Image Dimensions, and Initial Setup ---
    fixed_font_title_size = 47
    font = ImageFont.truetype(os.path.join("fonts", "Segoe UI.ttf"), fixed_font_title_size)

    original_image_width, original_image_height = image.size
    
    # --- Determine actual content horizontal bounds from the ORIGINAL image ---
    # This is for the *visual width of the expansion band*
    content_band_x_start, content_band_x_end_exclusive = find_image_content_horizontal_bounds(image)
    print_step(f"Detected content bounds for band: X from {content_band_x_start} to {content_band_x_end_exclusive}")

    # --- Text Area Definition (for text wrapping and placement) ---
    # This remains based on full image width and fixed margins for text layout consistency.
    text_x_start_margin = 120
    text_block_pixel_width = original_image_width - (2 * text_x_start_margin)
    if text_block_pixel_width <= 0: 
        text_block_pixel_width = original_image_width - text_x_start_margin
        if text_block_pixel_width <=0:
            text_block_pixel_width = original_image_width / 2
    
    # --- 2. Pixel-Aware Text Wrapping ---
    initial_char_wrap = wrap
    temp_lines_for_count = textwrap.wrap(text, width=initial_char_wrap) # Used to decide if wrap width needs adjustment
    
    current_char_wrap = initial_char_wrap
    if len(temp_lines_for_count) > 2: # Original logic to increase wrap width for more lines
        current_char_wrap = initial_char_wrap + 10
    
    lines = []
    # Iteratively adjust char_wrap to fit text_block_pixel_width
    # (Safety break added to avoid overly long loops if something is off)
    max_char_wrap_attempts = current_char_wrap + 5 # Allow some reduction
    attempt_count = 0
    candidate_lines_final = [] # Store best candidate

    while current_char_wrap > 0 and attempt_count < max_char_wrap_attempts:
        attempt_count += 1
        candidate_lines = textwrap.wrap(text, width=current_char_wrap, break_long_words=True, replace_whitespace=True)
        candidate_lines_final = candidate_lines # Keep track of last valid attempt

        if not candidate_lines: # Empty text
            lines = [""] 
            break

        max_line_pixel_width_found = 0
        for line_text in candidate_lines:
            line_pixel_width, _ = get_text_dimensions(line_text, font)
            if line_pixel_width > max_line_pixel_width_found:
                max_line_pixel_width_found = line_pixel_width
        
        if max_line_pixel_width_found <= text_block_pixel_width:
            lines = candidate_lines
            break # Lines fit
        else:
            current_char_wrap -= 1 # Reduce char wrap and try again
            if current_char_wrap <= 0: # If reduced to nothing
                 print_step(f"Warning: Text wrapping failed to fit. Using last attempt. Max line width {max_line_pixel_width_found}px vs target {text_block_pixel_width}px.")
                 lines = candidate_lines_final # Use the last set of lines before char_wrap hit 0
                 break
    else: # Loop finished without break (either char_wrap became 0 or max_attempts reached)
        if not lines: # If 'lines' was not set in the loop
            print_step(f"Warning: Text wrapping loop exhausted. Using last candidate or aggressive wrap for: {text[:30]}...")
            lines = candidate_lines_final if candidate_lines_final else textwrap.wrap(text, width=1, break_long_words=True)

    if not lines: # Final fallback
        lines = [""] if not text.strip() else textwrap.wrap(text, width=10)
    print_step(f"Text wrapped into {len(lines)} lines using effective char wrap: {current_char_wrap if current_char_wrap > 0 else 1}")


    # --- 3. Image Expansion Logic ---
    current_image_canvas = image
    current_canvas_height = float(original_image_height)
    username_original_y = 825
    username_final_y = username_original_y 
    expansion_band_height = 0
    expanded_this_run = False
    split_y_on_original = original_image_height // 2

    if len(lines) > 2:
        print_step(f"Text has {len(lines)} lines, expanding image.")
        # Using "Ay" as a sample for typical line height.
        avg_line_render_height = getheight(font, "Ay") 
        height_needed_per_additional_line = avg_line_render_height + padding
        num_lines_over_two = len(lines) - 2
        expansion_band_height = int(round(num_lines_over_two * height_needed_per_additional_line))

        if expansion_band_height > 0:
            expanded_this_run = True
            new_total_height = original_image_height + expansion_band_height
            
            # New canvas background: transparent for RGBA, white for RGB.
            # The pasted parts of original image will cover this. Band is drawn later.
            new_canvas_bg_color = (0, 0, 0, 0) if image.mode == "RGBA" else (255, 255, 255)
            
            expanded_canvas = Image.new(image.mode, (original_image_width, new_total_height), new_canvas_bg_color)
            
            top_half = image.crop((0, 0, original_image_width, split_y_on_original))
            bottom_half = image.crop((0, split_y_on_original, original_image_width, original_image_height)) 

            expanded_canvas.paste(top_half, (0, 0))
            expanded_canvas.paste(bottom_half, (0, split_y_on_original + expansion_band_height))
            
            current_image_canvas = expanded_canvas
            current_canvas_height = float(new_total_height)

            if username_original_y >= split_y_on_original: # If username was in or crossed into bottom half
                username_final_y = username_original_y + expansion_band_height
            
            print_step(f"Image expanded. New height: {new_total_height}. Band height: {expansion_band_height}")
    
    # --- 4. Prepare for Drawing & Draw Expansion Band ---
    draw = ImageDraw.Draw(current_image_canvas)

    if expanded_this_run and expansion_band_height > 0:
        if is_user:
            band_color = (14, 18, 23)
        else:
            band_color = (255, 255, 255) 
        if current_image_canvas.mode == "RGBA": # Ensure opaque white if canvas is RGBA
            if is_user:
                band_color = (14, 18, 23, 255)
            else:
                band_color = (255, 255, 255, 255) 
        
        # Draw the band using DETECTED CONTENT BOUNDS from original image
        draw.rectangle(
            [(content_band_x_start, split_y_on_original), 
             (content_band_x_end_exclusive, split_y_on_original + expansion_band_height)],
            fill=band_color
        )
        print_step(f"Drew expansion band from x={content_band_x_start} to x={content_band_x_end_exclusive}")


    # --- 5. Draw Username ---
    username_font_size = 30
    username_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), username_font_size)
    
    if is_user:
      channel_name_text = "User" # Fallback

    else:
      channel_name_text = settings.config["settings"]["channel_name"]

    # Username X is 205, as per original code.
    draw.text(
        (205, username_final_y), 
        channel_name_text,
        font=username_font,
        fill=text_color,
        align="left",
    )

    # --- 6. Calculate Main Text Start Position `y` & Draw Main Text ---
    actual_text_block_height = 0.0
    if lines:
        line_render_heights = [float(getheight(font, l)) if l.strip() else 0 for l in lines]
        actual_text_block_height = sum(line_render_heights)
        if len(lines) > 1: # Add padding between lines
            actual_text_block_height += float((len(lines) - 1) * padding)
    
    # Vertical offset logic from original code
    vertical_center_offset = 30.0
    if len(lines) == 3:
        vertical_center_offset = 35.0
    elif len(lines) == 4:
        vertical_center_offset = 40.0
    elif len(lines) > 4: # For 5 or more lines
        vertical_center_offset = 30.0 

    y_start_text_float = (current_canvas_height / 2.0) - (actual_text_block_height / 2.0) + vertical_center_offset
    
    current_y_for_line = y_start_text_float
    for line_text in lines:
        line_render_height = float(getheight(font, line_text)) if line_text.strip() else 0
        # Main text is drawn starting at text_x_start_margin (120px from left of image)
        draw.text((text_x_start_margin, round(current_y_for_line)), line_text, font=font, fill=text_color, align="left")
        current_y_for_line += line_render_height + float(padding)

    return current_image_canvas