import logging
from .base import TextureFormat, fmts, types
from . import rgb, bcn
from . import formatinfo

log = logging.getLogger(__name__)

for cls in TextureFormat.__subclasses__():
    fmts[cls.id] = cls
