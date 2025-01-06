from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import re
from datetime import datetime
import random

def put_custom_text(frame, text, position, font_path, font_size, color):
    # Create a PIL image from the frame
    pil_img = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil_img)

    # Load the custom font
    font = ImageFont.truetype(font_path, font_size)

    # Draw the text
    draw.text(position, text, font=font, fill=color)

    # Convert back to OpenCV image
    return np.array(pil_img)

def parse_time(time_str):
    # Convert SRT time format to seconds
    time_obj = datetime.strptime(time_str, '%H:%M:%S,%f')
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond/1000000

def parse_srt(file_path):
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into subtitle blocks
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # Get time stamps
            time_line = lines[1]
            start_time, end_time = time_line.split(' --> ')
            
            # Get text
            text = ' '.join(lines[2:])
            
            subtitles.append({
                'start': parse_time(start_time),
                'end': parse_time(end_time),
                'text': text
            })
    
    return subtitles

class WordDisplay:
    def __init__(self, word, position, width, height, color=(255, 255, 255)):
        self.word = word
        self.position = position
        self.width = width
        self.height = height
        self.color = color

def get_relative_position(last_position, text_width, text_height, width, height, existing_words):
    max_attempts = 100
    margin = 50  # Minimum distance from edges
    for _ in range(max_attempts):
        # Random offset for positioning the next word
        offset_x = random.randint(-40, 40)
        offset_y = random.randint(-40, 40)
        
        # Calculate new position
        new_x = last_position[0] + text_width + offset_x
        new_y = last_position[1] + offset_y
        
        # Ensure the new position is within bounds
        new_x = max(margin, min(new_x, width - text_width - margin))
        new_y = max(margin, min(new_y, height - text_height - margin))
        
        # Check for overlap with existing words
        overlap = False
        for word in existing_words:
            if (new_x < word.position[0] + word.width and new_x + text_width > word.position[0] and
                new_y < word.position[1] + word.height and new_y + text_height > word.position[1]):
                overlap = True
                break
        
        if not overlap:
            return (new_x, new_y)

    # If no safe position found, return the original position
    return (last_position[0] + text_width + 10, last_position[1])

def create_video():
    # Read subtitles
    subtitles = parse_srt('SUBS.srt')
    
    # Video settings
    width, height = 1280, 720
    fps = 30
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('output.mp4', fourcc, fps, (width, height))
    
    # Get max duration from subtitles
    max_duration = max(sub['end'] for sub in subtitles)
    total_frames = int(max_duration * fps)
    
    # Keep track of displayed words
    current_words = []
    word_count = 0
    
    # Path to your custom font
    font_path = "C:/Users/nitis/Videos/songs_and_fonts/fonts/AppleGaramond-LightItalic.ttf"  # Update with your font file path
    font_size = 40  # Adjust size as needed
    color = (255, 255, 255)  # White color
    
    # Create frames
    for frame_num in range(total_frames):
        current_time = frame_num / fps
        
        # Create black frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Find current subtitle
        for sub in subtitles:
            if sub['start'] <= current_time <= sub['end']:
                words = sub['text'].split()
                # Calculate which word to show
                word_duration = (sub['end'] - sub['start']) / len(words)
                word_index = int((current_time - sub['start']) / word_duration)

                if word_index < len(words):
                    current_word = words[word_index]
                    
                    # Check if this is a new word
                    if len(current_words) == 0 or current_words[-1].word != current_word:
                        word_count += 1
                        
                        # Get text size using PIL
                        font = ImageFont.truetype(font_path, font_size)
                        bbox = font.getbbox(current_word)
                        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                        
                        # Determine position
                        if current_words:
                            last_position = current_words[-1].position

                            position = get_relative_position(last_position, text_width, text_height, width, height, current_words)
                        else:
                            # Start from a random position if no words yet
                            randomizer_num = 90
                            position = (random.randint(randomizer_num, width - text_width - randomizer_num), random.randint(randomizer_num, height - text_height - randomizer_num))
                        
                        # Add new word to current words
                        current_words.append(WordDisplay(current_word, position, text_width, text_height))
                        
                        # Reset after 7 words
                        if len(current_words) >= 7:
                            if len(current_words) >= 7:
                                current_words = [WordDisplay(current_words[-1].word, (640, 360), current_words[-1].width, current_words[-1].height)]
                                word_count = 1  # Reset word count to 1 to account for the kept word


                
                break
        
        # Draw all current words using custom font
        for word_display in current_words:
            frame = put_custom_text(frame, word_display.word, word_display.position, font_path, font_size, color)
        
        # Write frame
        out.write(frame)
        
        # Progress indicator
        if frame_num % fps == 0:
            print(f"Processing: {frame_num/total_frames*100:.1f}%")
    
    # Release video writer
    out.release()
    print("Video creation complete!")

if __name__ == "__main__":
    create_video()
