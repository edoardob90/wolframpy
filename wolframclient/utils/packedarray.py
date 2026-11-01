import numpy as np


class PackedArray(np.ndarray):
    """Wrapper class on top of NymPy ndarray used to preserve packed arrays when round-tripping them."""
