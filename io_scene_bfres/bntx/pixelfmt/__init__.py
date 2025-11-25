import logging

from . import bcn, formatinfo, rgb
from .base import TextureFormat, fmts, types

log = logging.getLogger(__name__)

for cls in TextureFormat.__subclasses__():
    fmts[cls.id] = cls
