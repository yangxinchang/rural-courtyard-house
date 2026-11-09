"""Create local repeatable finish textures; no downloaded assets are used."""
from pathlib import Path
import numpy as np
from PIL import Image

output=Path(__file__).resolve().parents[1]/'assets/finishes'
output.mkdir(parents=True,exist_ok=True)
size=1024
y,x=np.mgrid[0:size,0:size]/size
rng=np.random.default_rng(42)
grain=np.sin(x*1100+np.sin(y*18)*1.9+np.sin(y*5)*3.8)
grain+=.5*np.sin(x*2480+np.sin(y*55)*2.7)
grain+=.35*rng.normal(size=(size,size))
grain+=.7*np.sin(x*40+np.sin(y*4)*2.1)
oak=np.array([151,111,74])+grain[:,:,None]*np.array([4.5,4.0,3.3])
stone_noise=2.7*rng.normal(size=(size,size))
stone_noise+=3.8*np.sin(x*17+np.sin(y*8))*np.cos(y*13)
vein=np.exp(-((np.sin(x*12+y*4+np.sin(y*9)*.24))/.045)**2)*9
stone=np.array([210,205,191])+(stone_noise-vein)[:,:,None]
weave=2.5*np.cos(x*size*np.pi/2)+2.5*np.cos(y*size*np.pi/2)
weave+=rng.normal(size=(size,size))*2
linen=np.array([191,177,153])+weave[:,:,None]
for name,pixels in [('warm-oak.png',oak),('warm-stone.png',stone),('linen.png',linen)]:
    pixels=np.clip(pixels,0,255).astype(np.uint8)
    assert pixels.shape==(1024,1024,3) and np.std(pixels[:,:,0])>2
    Image.fromarray(pixels).save(output/name)
print('Created three 1024px local finish textures:',output)
reference=Path(__file__).resolve().parents[1]/'装修图片及风格/Code_Generated_Image (3).jpeg'
# shortcut: this crop matches the supplied reference; recrop when replacing that image.
with Image.open(reference) as image:
    image.crop((644,290,740,386)).resize((512,512),Image.Resampling.LANCZOS).save(output/'reference-ink-art.png')
