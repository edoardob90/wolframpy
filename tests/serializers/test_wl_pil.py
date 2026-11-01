from unittest import TestCase as BaseTestCase

from tests.configure import path_to_file_in_data_dir
from wolframclient.serializers import export
from wolframclient.utils.api import PIL, numpy


class TestCase(BaseTestCase):
    def test_png_mode_I(self):

        with PIL.open(path_to_file_in_data_dir("5x2.png")) as image:
            self.assertEqual(
                export(image, target_format="wl"),
                b'ImportByteArray[ByteArray["iVBORw0KGgoAAAANSUhEUgAAAAUAAAACEAAAAADlkZXCAAAAH0lEQVR4nGP0+P39rf6+ky9/R7Aoen2+9shDWSRCHwCO7ws73c3PRQAAAABJRU5ErkJggg=="], "PNG"]',
            )

    def test_mode_L(self):
        a = numpy.arange(10).reshape((2, 5)).astype(numpy.uint8)
        img = PIL.fromarray(a)
        self.assertEqual(img.mode, "L")
        out = export(img, target_format="wl")
        self.assertEqual(
            out,
            b'Image[BinaryDeserialize[ByteArray["ODrCEAICBQABAgMEBQYHCAk="]], "Byte", Rule[ColorSpace, "Grayscale"], Rule[Interleaving, True]]',
        )

    def test_bool_img(self):
        a = numpy.array([[1, 0], [0, 1]], dtype="bool")
        img = PIL.fromarray(a)
        out = export(img, target_format="wl")
        self.assertEqual(
            out,
            b'Image[BinaryDeserialize[ByteArray["ODrCEAICAgEAAAE="]], "Bit", Rule[ColorSpace, Automatic], Rule[Interleaving, True]]',
        )
