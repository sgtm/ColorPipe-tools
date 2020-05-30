#!/usr/bin/python3

""" Convert a LUT into another format

.. moduleauthor:: `Marie FETIVEAU <github.com/mfe>`_

"""
__version__ = "0.2"
import argparse
import os
import ntpath
from PyOpenColorIO import Constants
from utils import debug_helper
import sys
import utils.lut_presets as presets
from utils.lut_utils import get_default_out_path, check_extension
from utils.ocio_helper import (create_ocio_processor,
                               is_3d_lut)
from utils.export_tool_helper import (add_export_lut_options,
                                      add_version_option,
                                      add_inverse_option,
                                      add_silent_option,
                                      add_inlutfile_option,
                                      add_trace_option,
                                      get_preset_and_write_function,
                                      add_outlutfile_option,
                                      get_write_function)
from utils.color_log_helper import print_error_message, print_success_message


class LutToLutException(Exception):
    """Module custom exception

    Args:
        Exception

    """
    pass


def lut_to_lut(inlutfiles, out_type=None, out_format=None, outlutfile=None,
               input_range=None, output_range=None, out_bit_depth=None,
               inverse=False, out_cube_size=None, verbose=False,
               smooth_size=None, preset=None, overwrite_preset=False):
    """ Concert a LUT in another LUT
    Arguments testing are delegated to LUT helpers

    Args:
        lutfiles (str or [str]): path to a LUT or list of LUT paths

        out_type (str): 1D, 2D or 3D

        out_format (str): '3dl', 'csp', 'cube', 'lut', 'spi', 'clcc', 'json'...

    Kwargs:
        outlutfile (str): path to output LUT

        input_range ([int/float, int/float]): input range.
        Ex: [0.0, 1.0] or [0, 4095]

        output_range ([int/float, int/float]): output range.
        Ex: [0.0, 1.0] or [0, 4095]

        out_bit_depth (int): output lut bit precision (1D only).
        Ex : 10, 16, 32.

        inverse (bool): inverse input LUT (1D only)

        out_cube_size (int): output cube size (3D only). Ex : 17, 32.

        verbose (bool): print log if true

        smooth_size (int): smooth exported LUT (1D only).
        Specify how many points are computed.
        A first subsampled curve is first processed and then resample with
        a smooth to fit input lutsize.
        So the smaller this value is, the smoother the curve will be.
        Ex: 10, 20,...

        preset (dict): lut generic and sampling informations

    """
    if preset:
        write_function = get_write_function(preset, overwrite_preset,
                                            out_type, out_format,
                                            input_range,
                                            output_range,
                                            out_bit_depth,
                                            out_cube_size,
                                            verbose)
    elif out_type is None or out_format is None:
        raise LutToLutException("Specify out_type/out_format or a preset.")
    else:
        preset, write_function = get_preset_and_write_function(out_type,
                                                               out_format,
                                                               input_range,
                                                               output_range,
                                                               out_bit_depth,
                                                               out_cube_size)
    ext = preset[presets.EXT]
    if not isinstance(inlutfiles, (list, tuple)):
        inlutfiles = [inlutfiles]
    if not outlutfile:
        outlutfile = get_default_out_path(inlutfiles, ext)
    elif os.path.isdir(outlutfile):
        filename = os.path.splitext(ntpath.basename(inlutfiles[0]))[0] + ext
        outlutfile = os.path.join(outlutfile, filename)
    else:
        check_extension(outlutfile, ext)
    # smooth
    if smooth_size:
        preset[presets.SMOOTH] = smooth_size
    if verbose:
        print("{0} will be converted into {1}.".format(inlutfiles,
                                                       outlutfile))
        print("Final setting:\n{0}".format(presets.string_preset(preset)))
    processor = create_ocio_processor(inlutfiles,
                                      interpolation=Constants.INTERP_LINEAR,
                                      inverse=inverse)
    # change interpolation if 3D LUT
    if is_3d_lut(processor, inlutfiles[0]):
        processor = create_ocio_processor(inlutfiles,
                                          interpolation=Constants.INTERP_TETRAHEDRAL,
                                          inverse=inverse)
    # write LUT
    message = write_function(processor.applyRGB, outlutfile, preset)
    if verbose:
        print_success_message(message)


def __get_options():
    """ Return lut_to_lut option parser

    Returns:
        .argparse.ArgumentParser.args

    """
    # Define parser
    description = 'Convert a LUT into another format'
    parser = argparse.ArgumentParser(description=description)
    # input lut
    add_inlutfile_option(parser, is_list=True)
    add_outlutfile_option(parser)
    # type, format, ranges,  out bit depth, out cube size
    add_export_lut_options(parser)
    # inverse (1d arg)
    add_inverse_option(parser)
    # Smooth size
    parser.add_argument("-sms", "--smooth-size", help=(
        "Smooth sub-sampling size (1D only). Ex : 17"
    ), default=None, type=int)
    # version
    full_version = debug_helper.get_imported_modules_versions(sys.modules,
                                                              globals())
    add_version_option(parser, description, __version__, full_version)
    # verbose
    add_silent_option(parser)
    # trace
    add_trace_option(parser)
    return parser.parse_args()


if __name__ == '__main__':
    ARGS = __get_options()
    if ARGS.input_range is not None:
        ARGS.input_range = presets.convert_string_range(ARGS.input_range)
    if ARGS.output_range is not None:
        ARGS.output_range = presets.convert_string_range(ARGS.output_range)
    if ARGS.preset is not None:
        ARGS.preset = presets.get_presets_from_env()[ARGS.preset]
    try:
        lut_to_lut(ARGS.inlutfiles,
                   ARGS.out_type,
                   ARGS.out_format,
                   ARGS.outlutfile,
                   ARGS.input_range,
                   ARGS.output_range,
                   ARGS.out_bit_depth,
                   ARGS.inverse,
                   ARGS.out_cube_size,
                   not ARGS.silent,
                   ARGS.smooth_size,
                   ARGS.preset,
                   ARGS.overwrite_preset
                   )
    except Exception as error:
        if ARGS.trace:
            print_error_message(error)
            raise
        MSG = "{0}.\nUse --trace option to get details".format(error)
        print_error_message(MSG)
