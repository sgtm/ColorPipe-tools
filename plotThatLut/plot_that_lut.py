#!/usr/bin/python

""" A Look Up Table plotting tool based on OpenColorIO and matplotlib.

.. moduleauthor:: `Marie FETIVEAU <github.com/mfe>`_

"""

## imports
import os
import sys
# OpenColorIO
from PyOpenColorIO import Config, ColorSpace, FileTransform
from PyOpenColorIO.Constants import INTERP_LINEAR, COLORSPACE_DIR_TO_REFERENCE
# matplotlib
import matplotlib


cherry_py_mode = True


def set_matplotlib_backend():
    """ Select display backend

    .. todo:: Externalize this and remove cherry_py_mode global var

    """

    if cherry_py_mode:
        matplotlib.use('Agg')
    else:
        matplotlib.use('Qt4Agg')

OCIO_LUTS_FORMATS = ['.3dl', '.csp', '.cub', '.cube', '.hdl', '.look',
                     '.mga/m3d', '.spi1d', '.spi3d', '.spimtx', '.vf']

DEFAULT_SAMPLE = 256
DEFAULT_CUBE_SIZE = 17


def show_plot(fig, filename):
    """Plot the figure depending on the backend

    Args:
        fig (matplotlib.pyplot.figure): figure to plot

        filename (str): associated lut filename

    Returns:
        str.
            if in cherrypy mode, an html string,
            else a void string.

    """
    if cherry_py_mode:
        split_filename = os.path.splitext(filename)
        filename = '{0}{1}'.format(split_filename[0],
                                   split_filename[1].replace(".", "_"))
        export_path = 'img/export_{0}.png'.format(filename)
        fig.savefig(export_path)
        return """
               <img src="/{0}"" width="640" height="480"
               border="0"/>
               """.format(export_path)
    else:
        matplotlib.pyplot.show()
        return ""


def create_ocio_processor(lutfile, interpolation):
    """Create an OpenColorIO processor for lutfile

    Args:
        lutfile (str): path to a LUT

        interpolation (int): can be INTERP_NEAREST, INTERP_LINEAR or
        INTERP_TETRAHEDRAL (only for 3D LUT)

    Returns:
        PyOpenColorIO.config.Processor.

    """
    config = Config()
    # In colorspace (LUT)
    colorspace = ColorSpace(name='RawInput')
    t = FileTransform(lutfile, interpolation=interpolation)
    colorspace.setTransform(t, COLORSPACE_DIR_TO_REFERENCE)
    config.addColorSpace(colorspace)
    # Out colorspace
    colorspace = ColorSpace(name='ProcessedOutput')
    config.addColorSpace(colorspace)
    # Create a processor corresponding to the LUT transformation
    return config.getProcessor('RawInput', 'ProcessedOutput')


def plot_curve(lutfile, samples_count, processor):
    """Plot a lutfile as a curve

    Args:
        lutfile (str): path to a color transformation file (lut, matrix...)

        samples_count (int): number of points for the displayed curve

        processor (PyOpenColorIO.config.Processor): an OpenColorIO processor
        for lutfile

    Returns:
            str.

    """
    # matplotlib : general plot
    from matplotlib.pyplot import (title, plot, xlabel, ylabel, grid,
                                   figure)
    # init vars
    max_value = samples_count - 1.0
    red_values = []
    green_values = []
    blue_values = []
    input_range = []
    # process color values
    for n in range(0, samples_count):
        x = n/max_value
        res = processor.applyRGB([x, x, x])
        red_values.append(res[0])
        green_values.append(res[1])
        blue_values.append(res[2])
        input_range.append(x)
    # init plot
    fig = figure()
    fig.canvas.set_window_title('Plot That 1D LUT')
    filename = os.path.basename(lutfile)
    title(filename)
    xlabel("Input")
    ylabel("Output")
    grid(True)
    # plot curves
    plot(input_range, red_values, 'r-', label='Red values', linewidth=1)
    plot(input_range, green_values, 'g-', label='Green values', linewidth=1)
    plot(input_range, blue_values, 'b-', label='Blue values', linewidth=1)
    return show_plot(fig, filename)


def plot_cube(lutfile, cube_size, processor):
    """Plot a lutfile as a cube

    Args:
        lutfile (str): path to a color transformation file (lut, matrix...)

        cube_size (int): number of segments. Ex : If set to 17, 17*17*17
        points will be displayed

        processor (PyOpenColorIO.config.Processor): an OpenColorIO processor
        for lutfile

    Returns:
        str.

    """
    # matplotlib : general plot
    from matplotlib.pyplot import title, figure
    # matplotlib : for 3D plot
    # mplot3d has to be imported for 3d projection
    import mpl_toolkits.mplot3d
    from matplotlib.colors import rgb2hex
    # init vars
    input_range = range(0, cube_size)
    max_value = cube_size - 1.0
    red_values = []
    green_values = []
    blue_values = []
    colors = []
    # process color values
    for r in input_range:
        for g in input_range:
            for b in input_range:
                # get a value between [0..1]
                norm_r = r/max_value
                norm_g = g/max_value
                norm_b = b/max_value
                # apply correction via OCIO
                res = processor.applyRGB([norm_r, norm_g, norm_b])
                # append values
                red_values.append(res[0])
                green_values.append(res[1])
                blue_values.append(res[2])
                # append corresponding color
                colors.append(rgb2hex([norm_r, norm_g, norm_b]))
    # init plot
    fig = figure()
    fig.canvas.set_window_title('Plot That 3D LUT')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('Red')
    ax.set_ylabel('Green')
    ax.set_zlabel('Blue')
    ax.set_xlim(min(red_values), max(red_values))
    ax.set_ylim(min(green_values), max(green_values))
    ax.set_zlim(min(blue_values), max(blue_values))
    filename = os.path.basename(lutfile)
    title(filename)
    # plot 3D values
    ax.scatter(red_values, green_values, blue_values, c=colors, marker="o")
    return show_plot(fig, filename)


def test_lut_1d():
    lutfile = "test_files/identity.csp"
    plot_curve(lutfile, samples_count=DEFAULT_SAMPLE)


def test_lut_3d():
    lutfile = "test_files/identity.3dl"
    plot_cube(lutfile, cube_size=DEFAULT_CUBE_SIZE)


def supported_formats():
    """Return supported formats

    Returns:
        str.

    """
    return "Supported LUT formats : {0}".format(', '.join(OCIO_LUTS_FORMATS))


def help():
    """Return help

    Returns:
        str.

    """
    return """
----
plot_that_lut.py <path to a LUT>
            dispay a cube ({0} segments) for 3D LUTs and matrixes
            or a curve ({1} points) for 1D/2D LUTs.

plot_that_lut.py <path to a LUT> curve [points count]
            display a curve with x points (default value : {2}).

plot_that_lut.py <path to a LUT> cube [cube size]
            display a cube with x segments (default value : {3}).

{4}
           """.format(DEFAULT_CUBE_SIZE, DEFAULT_SAMPLE, DEFAULT_SAMPLE,
                      DEFAULT_CUBE_SIZE, supported_formats())


def plot_that_lut(lutfile, plot_type=None, count=None):
    """Plot a lut depending on its type and/or args

    Args:
        lutfile (str): path to a color transformation file (lut, matrix...)

    kwargs:
        plot_type (str): possible values are 'curve' or 'cube'

        count: possible values are curve size or curve samples count or 'auto'

    Raises:
        Exception

    """
    set_matplotlib_backend()
    # check if LUT format is supported
    fileext = os.path.splitext(lutfile)[1]
    if not fileext:
        raise Exception("""
Error: Couldn't extract extension in this
path : {0}
                        """.format(lutfile))
    if fileext not in OCIO_LUTS_FORMATS:
        raise Exception("Error: {0} file format aren't supported.\n{1}"
                        .format(fileext, supported_formats()))
    # create OCIO processor
    processor = create_ocio_processor(lutfile, INTERP_LINEAR)
    # init args
    if not plot_type or plot_type == 'auto':
        if processor.hasChannelCrosstalk() or fileext == '.spimtx':
            plot_type = 'cube'
        else:
            plot_type = 'curve'
    if not count or count == 'auto':
        # set plot_type from the command line and init default count
        if plot_type == 'curve':
            count = DEFAULT_SAMPLE
        else:
            count = DEFAULT_CUBE_SIZE
    # plot
    print "Plotting a {0} with {1} samples...".format(plot_type, count)
    if plot_type == 'curve':
        return plot_curve(lutfile, count, processor)
    elif plot_type == 'cube':
        return plot_cube(lutfile, count, processor)
    else:
        raise Exception("""Unknown plot type : {0}
Plot type should be curve or cube.\n{1}
                        """.format(plot_type, help()))

if __name__ == '__main__':
    """ Command line interface for plot_that_lut

    .. todo:: use optparse (or argparse)

    """
    cherry_py_mode = False
    params_count = len(sys.argv)
    lutfile = ""
    plot_type = None
    count = None
    if params_count < 2:
        print "Syntax error !"
        print help()
        sys.exit(1)
    elif params_count == 2:
        lutfile = sys.argv[1]
    elif params_count == 3:
        lutfile = sys.argv[1]
        plot_type = sys.argv[2]
    elif params_count == 4:
        lutfile = sys.argv[1]
        plot_type = sys.argv[2]
        count = int(sys.argv[3])
    else:
        print "Syntax error !"
        print help()
        sys.exit(1)
    try:
        plot_that_lut(lutfile, plot_type, count)
    except Exception, e:
        print "Watch out !\n%s" % e
