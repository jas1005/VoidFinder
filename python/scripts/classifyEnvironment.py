'''Identify galaxies as being in a void or not.'''


################################################################################
#
#   IMPORT LIBRARIES
#
################################################################################


import numpy as np

from astropy.table import QTable, Table
import astropy.units as u

import pickle

import sys
sys.path.insert(1, '/Users/kellydouglass/Documents/Research/VoidFinder/python')
from voidfinder.vflag import determine_vflag
from voidfinder.voidfinder_functions import build_mask


################################################################################
#
#   USER INPUT
#
################################################################################


#-------------------------------------------------------------------------------
# FILE OF VOID HOLES
void_filename = '../voidfinder/data/vollim_dr7_cbp_102709_holes.txt'
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# SURVEY MASK FILE
mask_filename = '../voidfinder/data/dr7_mask.pickle'
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# FILE OF OBJECTS TO BE CLASSIFIED

#galaxy_file = input('Galaxy data file (with extension): ')
galaxy_filename = '/Users/kellydouglass/Documents/Research/Rotation_curves/RotationCurves/master_file.txt'

galaxy_file_format = 'ecsv'
#-------------------------------------------------------------------------------


################################################################################
#
#   CONSTANTS
#
################################################################################


c = 3e5 # km/s
h = 1
H = 100*h

DtoR = np.pi/180


################################################################################
#
#   IMPORT DATA
#
################################################################################


# Read in list of void holes
voids = Table.read(void_filename, format='ascii.commented_header')
'''
voids['x'] == x-coordinate of center of void (in Mpc/h)
voids['y'] == y-coordinate of center of void (in Mpc/h)
voids['z'] == z-coordinate of center of void (in Mpc/h)
voids['R'] == radius of void (in Mpc/h)
voids['voidID'] == index number identifying to which void the sphere belongs
'''


# Read in list of objects to be classified
if galaxy_file_format == 'ecsv':
    galaxies = QTable.read( galaxy_filename, format='ascii.ecsv')
    DtoR = 1.
else:
    galaxies = Table.read( galaxy_filename, format='ascii.' + galaxy_file_format)


# Read in survey mask
mask_infile = open(mask_filename, 'rb')
mask_resolution, maskfile = pickle.load(mask_infile)
mask_infile.close()

mask = build_mask(maskfile, mask_resolution)


################################################################################
#
#   CONVERT GALAXY ra,dec,z TO x,y,z
#
################################################################################
'''Conversions are from http://www.physics.drexel.edu/~pan/VoidCatalog/README'''


# Convert redshift to distance
galaxies_r = c*galaxies['NSA_redshift']/H


# Calculate x-coordinates
galaxies_x = galaxies_r*np.cos(galaxies['NSA_DEC']*DtoR)*np.cos(galaxies['NSA_RA']*DtoR)

# Calculate y-coordinates
galaxies_y = galaxies_r*np.cos(galaxies['NSA_DEC']*DtoR)*np.sin(galaxies['NSA_RA']*DtoR)

# Calculate z-coordinates
galaxies_z = galaxies_r*np.sin(galaxies['NSA_DEC']*DtoR)


################################################################################
#
#   IDENTIFY LARGE-SCALE ENVIRONMENT
#
################################################################################


galaxies['vflag'] = -9

for i in range(len(galaxies)):

    #print('Galaxy #', galaxies['NSA_index'][i])
    
    galaxies['vflag'][i] = determine_vflag( galaxies_x[i], galaxies_y[i], galaxies_z[i], 
                                            voids, mask, mask_resolution)


################################################################################
#
#   SAVE RESULTS
#
################################################################################


# Output file name
galaxy_file_name, extension = galaxy_filename.split('.')
outfile = galaxy_file_name + '_vflag.txt'


if galaxy_file_format == 'ecsv':
    galaxies.write( outfile, format='ascii.ecsv', overwrite=True)
else:
    galaxies.write( outfile, format='ascii.' + galaxy_file_format, overwrite=True)
