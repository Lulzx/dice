from glob import glob
from PIL import Image

files = glob("*.png")
sizes = [(455.33,234.66)]

for image in files:
    for size in sizes:
        im = Image.open(image)
        im.thumbnail(size)
        im.save("thumbnail_%s" % (image))


