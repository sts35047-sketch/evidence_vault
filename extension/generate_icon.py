import os
from PIL import Image, ImageDraw

def create_icon():
    # Create a 128x128 transparent image
    size = 128
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 1. Draw a deep purple circle background (EvidenceVault theme)
    d.ellipse((10, 10, 118, 118), fill="#7c3aed")

    # 2. Draw the lock shackle (top arc)
    d.arc((44, 34, 84, 74), start=180, end=0, fill="white", width=8)

    # 3. Draw the lock body (rounded rectangle)
    d.rounded_rectangle((34, 60, 94, 104), radius=8, fill="white")

    # 4. Draw a small keyhole inside the lock
    d.ellipse((58, 72, 70, 84), fill="#7c3aed")
    d.polygon([(64, 78), (60, 92), (68, 92)], fill="#7c3aed")

    # Save to the current directory
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    img.save(filepath)
    print(f"✅ Successfully generated icon at: {filepath}")

if __name__ == "__main__":
    create_icon()