'''VoidFinder - Hoyle & Vogeley (2002)'''

################################################################################
#
#   IMPORT MODULES
#
################################################################################

from voidfinder import filter_galaxies, find_voids

import numpy as np
from astropy.io import fits
from astropy.table import Table

from absmag_comovingdist_functions import Distance

import pickle

################################################################################
#
#   USER INPUTS
#
################################################################################


survey_name = 'DESI_void_flatmock_7_'

# File header
in_directory = '/scratch/sbenzvi_lab/desi/void_catalog/'
out_directory = '/scratch/sbenzvi_lab/desi/dylanbranch/VoidFinder2/DESI/mocks/'

# Input file names
galaxies_filename = 'void_flatmock_7.fits'  # File format: RA, dec, redshift, comoving distance, absolute magnitude
mask_filename = 'voidmock7mask.npy'           # File format: RA, dec

in_filename = in_directory + galaxies_filename
mask_filename = out_directory + mask_filename


# Survey parameters
determine_parameters = False
min_dist = 1015  # z = 0.37 --> 1013 Mpc/h
max_dist = 2600  # z = 1.2 --> 2634 Mpc/h

# Cosmology
Omega_M = 0.3
h = 1

# Remove faint galaxies?
mag_cut = False

# Remove isolated galaxies?
rm_isolated = False


# Output file names
if mag_cut and rm_isolated:
    out1_suffix = '_maximal.txt'
    out2_suffix = '_holes.txt'
elif rm_isolated:
    out1_suffix = '_maximal_noMagCut.txt'
    out2_suffix = '_holes_noMagCut.txt'
elif mag_cut:
    out1_suffix = '_maximal_keepIsolated.txt'
    out2_suffix = '_holes_keepIsolated.txt'
else:
    out1_suffix = '_maximal_noFiltering.txt'
    out2_suffix = 'holes_noFiltering.txt'

out1_filename = out_directory + galaxies_filename[:-5] + out1_suffix  # List of maximal spheres of each void region: x, y, z, radius, distance, ra, dec
out2_filename = out_directory + galaxies_filename[:-5] + out2_suffix  # List of holes for all void regions: x, y, z, radius, flag (to which void it belongs)
#out3_filename = out_directory + 'out3_vollim_dr7.txt'                # List of void region sizes: radius, effective radius, evolume, x, y, z, deltap, nfield, vol_maxhole
#voidgals_filename = out_directory + 'vollim_voidgals_dr7.txt'        # List of the void galaxies: x, y, z, void region



################################################################################
#
#   OPEN FILES
#
################################################################################


gal_file = fits.open(in_filename)
infile = Table(gal_file[1].data)

maskfile = np.load(mask_filename)


# Print min and max distances
if determine_parameters:

    # Minimum distance
    min_z = min(infile['z'])

    # Maximum distance
    max_z = max(infile['z'])

    # Convert redshift to comoving distance
    dist_limits = Distance([min_z, max_z], Omega_M, h)

    print('Minimum distance =', dist_limits[0], 'Mpc/h')
    print('Maximum distance =', dist_limits[1], 'Mpc/h')

    exit()



# Rename columns
if 'rabsmag' not in infile.columns:
    '''
    print(infile.columns)
    print('Please rename columns')
    '''
    infile['magnitude'].name = 'rabsmag'

# Calculate comoving distance
if 'Rgal' not in infile.columns:
    infile['Rgal'] = Distance(infile['z'], Omega_M, h)


################################################################################
#
#   FILTER GALAXIES
#
################################################################################


coord_min_table, mask, ngrid = filter_galaxies(infile, maskfile, min_dist, max_dist, survey_name, mag_cut, rm_isolated)

temp_outfile = open("filter_galaxies_output.pickle", 'wb')
pickle.dump((coord_min_table, mask, ngrid), temp_outfile)
temp_outfile.close()


################################################################################
#
#   FIND VOIDS
#
################################################################################


temp_infile = open("filter_galaxies_output.pickle", 'rb')
coord_min_table, mask, ngrid = pickle.load(temp_infile)
temp_infile.close()

find_voids(ngrid, min_dist, max_dist, coord_min_table, mask, out1_filename, out2_filename, survey_name)
