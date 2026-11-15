import io,warnings
from PIL import Image,ImageOps
MAX_BYTES=10*1024*1024
MAX_PIXELS=16_000_000
class Invalid(ValueError):pass

def image_bytes(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise Invalid('Choose a PNG or JPEG no larger than 10 MiB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in ('PNG','JPEG') or source.width*source.height>MAX_PIXELS or getattr(source,'n_frames',1)!=1:raise Invalid('Use a single PNG or JPEG up to 16 megapixels.')
                source.load();img=ImageOps.exif_transpose(source).convert('RGBA');clean=Image.new('RGBA',img.size);clean.paste(img);out=io.BytesIO();clean.save(out,format='PNG');data=out.getvalue()
                if len(data)>MAX_BYTES:raise Invalid('Decoded PNG exceeds 10 MiB. Resize the image.')
                return data,clean.width,clean.height
    except Invalid:raise
    except (OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning):raise Invalid('This image cannot be decoded.')
