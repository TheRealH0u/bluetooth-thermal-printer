from PIL import Image
import os
from Dither import dither
import cv2
import numpy as np

CRC8_TABLE = [
    0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15, 0x38, 0x3f, 0x36, 0x31,
    0x24, 0x23, 0x2a, 0x2d, 0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
    0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d, 0xe0, 0xe7, 0xee, 0xe9,
    0xfc, 0xfb, 0xf2, 0xf5, 0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
    0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85, 0xa8, 0xaf, 0xa6, 0xa1,
    0xb4, 0xb3, 0xba, 0xbd, 0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
    0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea, 0xb7, 0xb0, 0xb9, 0xbe,
    0xab, 0xac, 0xa5, 0xa2, 0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
    0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32, 0x1f, 0x18, 0x11, 0x16,
    0x03, 0x04, 0x0d, 0x0a, 0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
    0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a, 0x89, 0x8e, 0x87, 0x80,
    0x95, 0x92, 0x9b, 0x9c, 0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
    0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec, 0xc1, 0xc6, 0xcf, 0xc8,
    0xdd, 0xda, 0xd3, 0xd4, 0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
    0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44, 0x19, 0x1e, 0x17, 0x10,
    0x05, 0x02, 0x0b, 0x0c, 0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
    0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b, 0x76, 0x71, 0x78, 0x7f,
    0x6a, 0x6d, 0x64, 0x63, 0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
    0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13, 0xae, 0xa9, 0xa0, 0xa7,
    0xb2, 0xb5, 0xbc, 0xbb, 0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8d, 0x84, 0x83,
    0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb, 0xe6, 0xe1, 0xe8, 0xef,
    0xfa, 0xfd, 0xf4, 0xf3
]

CMD_HEADER = [
    81, 120, -92, 0, 1, 0, 53, -117, -1, # print Quiality 5
    81,120,-81,0,2,0,-120,19,103,-1,
    81,120,-66,0,1,0,0,0,-1 # print Image
]

CMD_FOOTER = [
    81,120,-67,0,1,0,25,79,-1,
    81,120,-95,0,2,0,48,0,-7,-1,
    81,120,-95,0,2,0,48,0,-7,-1,
    81,120,-67,0,1,0,25,79,-1,
    81,120,-93,0,1,0,0,0,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
]

class ImageUtils:
    def __init__(self, choice="dither", dither_method="jarvis-judice-ninke", width=384, max_height=1536):
        self.width = width
        self.max_height = max_height
        self.dither_method = dither_method
        self.choice = choice
    
    @property
    def choice(self):
        return self._choice
    @choice.setter
    def choice(self, value):
        allowed_choices = ["dither", "PIL"]
        if value not in allowed_choices:
            raise ValueError(f"Invalid choice: {value}. Allowed values are: {', '.join(allowed_choices)}")
        self._choice = value

    @property
    def dither_method(self):
        return self._dither_method
    @dither_method.setter
    def dither_method(self, value):
        allowed_methods = ["jarvis-judice-ninke", "floyd-steinberg", "simple2D"]
        if value not in allowed_methods:
            raise ValueError(f"Invalid dither method: {value}. "
                             f"Allowed values are: {', '.join(allowed_methods)}")
        self._dither_method = value
    
    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("width must be a positive integer")
        self._width = value

    @property
    def max_height(self):
        return self._max_height
    @max_height.setter
    def max_height(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("max_height must be a positive integer")
        self._max_height = value

    def process_image_PIL(self, image):
        image_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), image)
        image = Image.open(image_path)
        aspect_ratio = image.height / image.width
        new_height = int(self.width * aspect_ratio)
        if new_height > self.max_height:
            new_height = self.max_height

        # Resize the image
        resized_img = image.resize((self.width, new_height), Image.ANTIALIAS)
        image = resized_img.convert("L")
        return image, image.width, image.height

    def process_image_dither(self, image):
        image_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), image)
        img = cv2.imread(image_path, 0)
        if img is None:
            raise ValueError(f"Error reading image: {image_path}")

        # Resize the image
        aspect_ratio = img.shape[0] / img.shape[1]  # height / width
        new_height = int(self.width * aspect_ratio)
        if new_height > self.max_height:
                new_height = self.max_height
        img = cv2.resize(img, (self.width, new_height))

        dithered_img = dither(img, method='jarvis-judice-ninke', resize=False)

        dithered_img = np.array(dithered_img)

        dithered_img = (dithered_img * 255).astype(np.uint8)

        height = dithered_img.shape[0]
        width = dithered_img.shape[1]

        return dithered_img, width, height

    def crc8(self, data):
        """ Compute the CRC using the provided CRC table. """
        byte_values = [(x + 256) % 256 for x in data]
        data_bytes = bytes(byte_values)
        crc = 0
        for byte in data_bytes:
            crc = CRC8_TABLE[crc ^ byte]
        return crc if crc < 0x80 else crc - 0x100

    def generate_image(self, image):

        cmd_send = []
        cmd_send.extend(CMD_HEADER)
        
        # Process the image using dither
        #print(f"Process image option {self.choice}")
        if self.choice == "dither":
            #print("Using Dither")
            image, width, height = self.process_image_dither(image)
        elif self.choice == "PIL":
            #print("Using PIL")
            image, width, height = self.process_image_PIL(image)

        for y in range(0, height):
            cmd_send.extend([81,120,-67,0,1,0,10,54,-1])
            bmp = []
            bit = 0

            # Turn RGBA8 line into 1bpp
            for x in range(0, width):
                if bit % 8 == 0:
                    bmp += [0x00]
                if self.choice == "dither":
                    a = image[y,x]
                elif self.choice == "PIL":
                    a = image.getpixel((x, y))
                bmp[int(bit / 8)] >>= 1
                if (a > 0x80 ):
                    bmp[int(bit / 8)] |= 0
                else:
                    bmp[int(bit / 8)] |= 0x80

                bit += 1
            cmd_command = [81, 120, -65, 0, len(bmp), 0]
            cmd_command.extend(bmp)
            crc = self.crc8(bmp)
            cmd_command.extend([crc, -1])
            cmd_send.extend(cmd_command)
        cmd_send.extend(CMD_FOOTER)
        return cmd_send
