import os
from datetime import datetime
dest = 'C:/Development/python/gimages/archive'
image = "C:/Development/python/gimages/Splash.jpg"
print(os.path.splitext(image)[1])
file = os.path.basename(image)
suffix = os.path.splitext(image)[1]
file = os.path.basename(image)
ind = file.find(suffix)
nufile = file[:ind] + datetime.now().strftime("%Y%m%dT%H%M%S") + file[ind:]
os.rename(image, dest + "/" + nufile)