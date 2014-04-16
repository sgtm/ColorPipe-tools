""" Cube (Iridas LUTs) helpers

.. moduleauthor:: `Marie FETIVEAU <github.com/mfe>`_

"""
__version__ = "0.2"
from utils.abstract_lut_helper import AbstractLUTHelper
from utils.color_log_helper import (print_error_message,
                                    print_warning_message,
                                    print_success_message
                                    )
from utils import lut_presets as presets


class CubeHelperException(Exception):
    """Module custom exception

    Args:
        Exception

    """
    pass

CUBE_1D = "LUT_1D_SIZE"
CUBE_3D = "LUT_3D_SIZE"


class CubeLutHelper(AbstractLUTHelper):
    """Cube LUT helper

    """
    def __init__(self):
        self.default_preset = {
                presets.TYPE: "default",
                presets.EXT: ".cube",
                presets.IN_RANGE: [0.0, 1.0],
                presets.OUT_RANGE: [0.0, 1.0],
                presets.OUT_BITDEPTH: 12,
                presets.CUBE_SIZE: 17,
                presets.TITLE: "Cube LUT",
                presets.COMMENT: ("Generated by ColorPipe-tools, cube_helper "
                                 "{0}").format(__version__),
                presets.VERSION: "1"
                }

    def get_default_preset(self):
        return self.default_preset

    def _write_1d_2d_lut(self, processor, file_path, preset, line_function):
        # Test output range
        self._check_output_range(preset)
        # Get data
        data = self._get_1d_data(processor, preset)
        title = preset['title']
        lutfile = open(file_path, 'w+')
        # skip comment because not supported by every soft
        # title
        if title is None:
            title = self.get_generated_title(file_path, preset)
        lutfile.write("TITLE {0}\n\n".format(title))
        # lut size
        lutfile.write("{0} {1}\n\n".format(CUBE_1D, len(data)))
        # data
        for rgb in data:
            lutfile.write(line_function(preset, rgb))
        lutfile.close()
        print_success_message(self.get_export_message(file_path))

    def write_1d_lut(self, processor, file_path, preset):
        print_warning_message("1D LUT is not supported in Cube format"
                              " --> Switch to 2D LUT.")
        self.write_2d_lut(processor, file_path, preset)

    def write_3d_lut(self, processor, file_path, preset):
        data = self._get_3d_data(processor, preset)
        title = preset['title']
        cube_size = preset['cube_size']
        lutfile = open(file_path, 'w+')
        # Test output range
        self._check_output_range(preset)
        # skip comment because not supported by every soft
        # title
        if title is None:
            title = self.get_generated_title(file_path, preset)
        lutfile.write("TITLE {0}\n\n".format(title))
        # lut size
        lutfile.write("{0} {1}\n\n".format(CUBE_3D, cube_size))
        # data
        for rgb in data:
            lutfile.write(self._get_rgb_value_line(preset, rgb))
        lutfile.close()
        print_success_message(self.get_export_message(file_path))

    @staticmethod
    def _get_range_message(output_range):
        """ Get range warning/error message

        Returns:
            .str

        """
        return ("Cube output range is expected to be float."
                " Ex: [0.0, 1.0] or [-0.25, 2.0].\nYour range {0}"
                ).format(output_range)

    def _check_output_range(self, preset):
        """ Check output range. Cube LUT are float.
            Print a warning or raise an error

        """
        output_range = preset['output_range']
        if self.is_output_int(preset):
            message = self._get_range_message(output_range)
            print_error_message(message)
            raise CubeHelperException(message)
        elif output_range[1] > presets.FLOAT_BOUNDARY:
            message = ("{0} seems too big !\n"
                       "Please check this, if the LUT isn't what you expected"
                       ).format(self._get_range_message(output_range))
            print_warning_message(message)

CUBE_HELPER = CubeLutHelper()
