import cv2
import numpy as np
import math as maths

class UniqueSectionsError(Exception):
    pass

class MatrixError(Exception):
    pass

class DimensionsError(Exception):
    pass

image = cv2.imread("test_matrix.bmp")

class ImageProcessor:
    def __init__(self, image):
        self.image = image
        self.unique_sections = {}

    def populate_unique_sections(self, section_width: int, section_height: int) -> dict[int,np.zeros]:

        """
            Requires:
                knowledge of the size of the tiles
                access to either a tiles item image or a bg image.

            Purpose:
                converts tile item image into a dictionary/hash_map of indices mapped to the 
                tile itself
            
            Usage of return:
                This is then used by create_matrix to create a matrix for use in the butano engine
                to create dynamic bg maps

        """
        if section_width == 0 or section_height == 0:
            raise DimensionsError(f"\n\nError: Section dimension of 0 not allowed./nSection width {section_width}, Section height {section_height}")
    
        elif self.image.shape[0]%section_width != 0:
            raise DimensionsError(f"\n\nError: image width ({self.image.shape[0]}) is not divisible by section width ({section_width}).\nMake sure image width is divisible by section width")

        elif self.image.shape[1]%section_height != 0:
            raise DimensionsError(f"\n\nError: image height ({self.image.shape[1]}) is not divisible by section height ({section_height}).\nMake sure image height is divisible by section height")

        y = 0
        x = 0
        index = 0
        while y <=self.image.shape[1] -section_height:
            section =self.image[y:y+section_height, x:x+section_width]
            if x <self.image.shape[0] -section_width:
                x += section_width
            else:
                x = 0
                y += section_height
            
            unique = True
            for item in self.unique_sections.values():
                if np.mean((section - item) ** 2) == 0:
                    unique = False
                    break
            if unique:
                self.unique_sections[index] = section
                index += 1
            
            if len(self.unique_sections) == 0:
                self.unique_sections[index] = section
                index += 1
    
    def generate_tile_item(self, section_width: int, section_height: int) -> None:

        """
            Requires:
                section width
                section height
                unique_tiles
            
            Purpose:
                Creates a tile map bmp for use with butano.

            Usage of return:
                See above.
        """

        if section_width == 0 or section_height == 0:
            raise DimensionsError(f"\n\nError: Section dimension of 0 not allowed./nSection width {section_width}, Section height {section_height}")
    
        elif self.image.shape[0]%section_width != 0:
            raise DimensionsError(f"\n\nError: image width ({self.image.shape[0]}) is not divisible by section width ({section_width}).\nMake sure image width is divisible by section width")

        tile_map_image = maths.ceil((section_height*len(self.unique_sections))/64)*section_height

        new_image = np.zeros((tile_map_image, 64, 3), dtype=np.uint8)
        x_offset = 0 
        y_offset = 0
        for tile in self.unique_sections.values():
            new_image[y_offset:y_offset + section_height, x_offset:x_offset + section_width] = tile

            if x_offset <64 -section_width:
                x_offset += section_width
            else:
                x_offset = 0
                y_offset += section_height
        
        cv2.imwrite("unique_tiles_image.bmp", new_image)

    def create_matrix(self, section_width: int, section_height: int) -> np.zeros:

        """
            Requires:
                section dimensions
                actual image file
            
            Purpose:
                creates an np matrix if the indices associated with each 
                tile in the image such that the image can be drawn using 
                only the tile map and this matrix

            Return purpose:
                Matrix is processed by convert_matrix_to_cpp_string
                So that I don't have to manually re-write the matrix I can just copy the string
                into the game files
        """

        if len(self.unique_sections) == 0:
            raise UniqueSectionsError("\n\nError: unique_sections of length 0.\nClass unique_sections attribute has length of 0.\nYou have either not run the populate_unique_sections method or the image has no tiles to populate the unique_sections attribute with.\nEnsure that these issues have been dealt with and try again!")
        
        x = 0
        y = 0

        matrix_x = self.image.shape[0]/section_width
        matrix_y = self.image.shape[1]/section_height 
        self.matrix = np.zeros((int(matrix_x), int(matrix_y)))
        while y <= self.image.shape[1] -section_height:
            section = self.image[y:y+section_height, x:x+section_width]

            for key,value in self.unique_sections.items():
                if np.mean((section - value) ** 2) == 0:
                    self.matrix[int(y/section_height),int(x/section_width)] = int(key)

            if x < self.image.shape[0] -section_width:
                x += section_width
            else:
                x = 0
                y += section_height

    def convert_matrix_to_cpp_string(self):

        """
            Requires:
                The matrix from create_matrix

            Purpose:
                Generates a cpp string for creating bgs from tile maps 
                and this matrix.
                Reason for this is it SHOULD allow for significantly larger maps, while also reducing the size of the roms.
                Can also potentially easily swap between tiles to completely change the map
                EG 
                Seasons become a simple change of tiles rather than a change in the entire BG. 

            Return usage:
                Paste the string into cpp file rather than manually typing it
        """

        if not hasattr(self, 'matrix'):
            raise MatrixError("\n\nError: Matrix attribute has not been set.\nMake sure to run create_matrix before running the convert_matrix_to_cpp_string code")

        matrix_x, matrix_y = self.matrix.shape
        self.cpp_matrix = f"int map_array[{matrix_x}][{matrix_y}] = " + "{"
        for idx, row in enumerate(self.matrix):
            self.cpp_matrix = self.cpp_matrix + "{"
            for inner_idx, element in enumerate(row):
                if inner_idx != len(row) - 1:
                    self.cpp_matrix = self.cpp_matrix + f"{int(element)}, "
                else:
                    self.cpp_matrix = self.cpp_matrix + f"{int(element)}"
            if idx != self.matrix.shape[1] - 1:
                self.cpp_matrix = self.cpp_matrix + "},"
            else:
                self.cpp_matrix = self.cpp_matrix + "}"
        self.cpp_matrix = self.cpp_matrix + "};"

if __name__ == "__main__":
    section_width = 8
    section_height = 8

    processor = ImageProcessor(image)
    processor.populate_unique_sections(section_width,section_height)
    processor.generate_tile_item(section_width, section_height)
    processor.create_matrix(section_width,section_height)
    processor.convert_matrix_to_cpp_string()

    pretty_string = processor.cpp_matrix.replace("},", "},\n")
    pretty_string = pretty_string.replace("{{", "{\n{")
    pretty_string = pretty_string.replace("}}", "}\n}")
    pretty_string = pretty_string.replace("{", "\t{")