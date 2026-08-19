"""
LinkedIn Profile Photo Cropper — Calvin Omondi Okoth
Crops full-body photo into head/shoulders portrait for LinkedIn (400x400 recommended)
"""
import sys, os, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from PIL import Image, ImageEnhance

# Source image
src = r"C:\Users\Sickdoctor\Downloads\Photo from Calvin..jpg"
out = r"C:\Users\Sickdoctor\OneDrive\Desktop\linkedin_profile_photo.jpg"

# Load
img = Image.open(src)
w, h = img.size
print(f"Original size: {w}x{h}")

# The photo is full-body. LinkedIn profile photos display as circles,
# so we want: head centered, shoulders visible, clean crop.
#
# Strategy: crop a square from the upper portion focusing on face/shoulders.
# From the image: face is roughly in the upper 30% of the image,
# centered slightly right of center.

# Calculate crop box for head + shoulders
# Face center is approximately at x=55% from left, y=18% from top
face_center_x = int(w * 0.55)
face_center_y = int(h * 0.18)

# LinkedIn circle crops from center of square — we want face in upper-third
# of the square so it looks centered in the circle
square_size = min(w, int(h * 0.75))  # Use 75% of height for square

# Top edge: start a bit above the face
top = max(0, face_center_y - int(square_size * 0.28))
bottom = top + square_size

# Left edge: center on face horizontally
left = max(0, face_center_x - square_size // 2)
right = left + square_size

# Adjust if going out of bounds
if right > w:
    right = w
    left = right - square_size
if bottom > h:
    bottom = h
    top = bottom - square_size

print(f"Crop box: left={left}, top={top}, right={right}, bottom={bottom}")
print(f"Crop size: {right-left}x{bottom-top}")

# Crop
cropped = img.crop((left, top, right, bottom))

# Slight enhance for professional look
enhancer = ImageEnhance.Contrast(cropped)
cropped = enhancer.enhance(1.05)

enhancer = ImageEnhance.Sharpness(cropped)
cropped = enhancer.enhance(1.1)

# Resize to LinkedIn recommended size (400x400)
cropped = cropped.resize((400, 400), Image.LANCZOS)

# Save high quality
cropped.save(out, 'JPEG', quality=95)
print(f"Saved: {out}")
print(f"Final size: 400x400px (LinkedIn profile photo)")
