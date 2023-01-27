__author__ = 'Angus Jack 13-Nov-2022'
__version__ = 'V 0.0.1'
__copyright__ = 'Copyright \xa9 2022 Angus Jack'

import os

import saga_api
import PySimpleGUI as Sg
import saga_tools
import ast
from pathlib import Path
import configparser
import time


class Ini:
    line_name = 'a line name'


def do_gui():
    Sg.theme('DarkGrey')
    try:
        file_list_as_string = Sg.popup_get_file('select input files:',
                                                'make *.gpkg from *.csv :: ' + __version__ + ' : ' + __copyright__,
                                                multiple_files=True, size=(100, 10), font=('courier', 12),
                                                file_types=(('All Files', '*.*'),), files_delimiter='", "')
        file_list_as_string = '["' + file_list_as_string + '"]'
        # Sg.popup('Results', 'The value returned from popup_get_folder', files)

        return file_list_as_string
    except:
        print('returned nothing\U0001f928\ngoing for bailout.....')
        exit()


def do_get_line_name():
    Sg.theme('DarkGrey')
    Ini.line_name = Sg.popup_get_text('name for the mag run line', 'line name', default_text=Ini.line_name)
    return Ini.line_name


def read_ini():
    """
    Reads the ini file.

    :return Ini: Class of ini file parameters.
    """
    config = configparser.ConfigParser()
    if os.path.isfile(os.path.splitext(__file__)[0] + '.ini'):
        config.read(os.path.splitext(__file__)[0] + '.ini')
        Ini.line_name = config['gui']['line_name']
    return Ini


def write_ini():
    """
    writes parameters to the ini file, creates the file if absent

    :return: nothing
    """
    an_ini_file = os.path.splitext(__file__)[0] + '.ini'
    if not os.path.isfile(an_ini_file):
        open(an_ini_file, 'w').close()
    config = configparser.ConfigParser()
    config['gui'] = {}
    gui = config['gui']
    gui['line_name'] = Ini.line_name
    with open(an_ini_file, 'w') as a_file:
        config.write(a_file)


def saga_api_initialise():
    print('\n==========================================================')
    print('SAGA Version: ' + saga_api.SAGA_VERSION)
    print(saga_api.SAGA_API_Get_Version())
    # saga_api.SG_Initialize_Environment(True, True, os.environ['SAGA_PATH'])
    # print('initialised saga environment')
    print('==========================================================\n')
    return


def qc_output_dir(path, dir_name):
    """
    makes a new directory at parent level for qc outputs if it does not already exist
    :param path: path to the pwd
    :param dir_name: name of a new parent directory
    :return:
    """
    plot_dir = Path(path).parents[1]
    plot_dir = str(plot_dir) + os.sep + dir_name
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    return plot_dir


def get_upper_dir_name(path):
    name = str(Path(path).parents[1])
    name = name.rsplit(os.sep)[-1:]
    name = name[0]
    return name


def make_saga_files_string(a_file_list):
    saga_f_list = ''
    for item in a_file_list:
        saga_f_list = saga_f_list + '"{}" '.format(item)
    print(saga_f_list)
    return saga_f_list


if __name__ == '__main__':
    saga_api_initialise()  # this just provides information as the initialisation is in saga_tools.py
    read_ini()
    files = do_gui()
    Ini.line_name = do_get_line_name()
    write_ini()
    Ini.line_name = '[' + Ini.line_name + ']'
    file_list = ast.literal_eval(files)
    saga_file_list = make_saga_files_string(file_list)
    shapes_dir = qc_output_dir(file_list[0], 'shapes')
    grids_dir = qc_output_dir(file_list[0], 'grids')
    # a_file_name = get_upper_dir_name(file_list[0])
    print(Ini.line_name + '\n')
    print('list of files selected:')
    print(*file_list, sep='\n')
    print('\n')

    params_shapes = saga_api.CSG_Parameters()
    a_shape = []
    for an_item in file_list:
        a_shape = saga_api.SG_Get_Data_Manager().Add_Shapes(an_item)

    # saga_shp_list = saga_tools.shapes_from_list(a_shape)

    shape_list = saga_tools.import_shapes(saga_file_list)

    print(saga_api.SG_Get_Data_Manager().Get_Summary().c_str())
    merged_layer = saga_tools.merge_shapes(shape_list, gis_name=Ini.line_name)
    # merged_layers = shapes_dir + os.sep + Ini.line_name + '.gpkg'
    grid_mask = saga_tools.inverse_dist_weighted(merged_layer, 'r_nT', cell_size=0.05)
    grid_out = saga_tools.multilevel_b_spline(merged_layer, 'r_nT', grid_mask)
    masked_grid = saga_tools.grid_masking(grid_out, grid_mask, gis_name=Ini.line_name)

    print(saga_api.SG_Get_Data_Manager().Get_Summary().c_str())
    merged_layer.Save(shapes_dir + os.sep + Ini.line_name + merged_layer.Get_Name() + '.geojson')
    print('wrote: ' + shapes_dir + os.sep + Ini.line_name + merged_layer.Get_Name() + '.geojson')
    masked_grid.Save(grids_dir + os.sep + Ini.line_name + masked_grid.Get_Name() + '.sg-grd-z')
    print('wrote: ' + grids_dir + os.sep + Ini.line_name + masked_grid.Get_Name() + '.sg-grd-z')
    saga_api.SG_Get_Data_Manager().Delete_All()

    print('\U0001f60e done!')
