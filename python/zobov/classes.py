import numpy as np
import healpy as hp
from astropy.io import fits
from scipy.spatial import ConvexHull, Voronoi, Delaunay

from util import toCoord, flatten

#ctlg  = Catalog(infile,256)
#tess  = Tesselation(ctlg)
#zones = Zones(tess)
#voids = Voids(zones)
#voids_sorted = voids.vSort()

class Catalog:
    def __init__(self,fname,nside):
        hdulist = fits.open(fname)
        z    = hdulist[1].data['z']
        ra   = hdulist[1].data['ra']
        dec  = hdulist[1].data['dec']
        mask = np.zeros(hp.nside2npix(nside),dtype=bool)
        for i in range(len(ra)):
            pid = hp.ang2pix(nside,ra[i],dec[i],lonlat=True)
            mask[pid] = True
        self.mask  = mask
        c1,c2,c3   = toCoord(z,ra,dec)
        self.coord = np.array([c1,c2,c3]).T

class Tesselation:
    def __init__(self,cat):
        coords = cat.coord
        print("Tesselating...")
        Vor = Voronoi(coords)
        ver = Vor.vertices
        reg = np.array(Vor.regions)[Vor.point_region]
        del Vor
        ve2 = ver.T
        vth = np.arctan2(np.sqrt(ve2[0]**2.+ve2[1]**2.),ve2[2])
        vph = np.arctan2(ve2[1],ve2[0])
        vrh = np.array([np.sqrt((v**2.).sum()) for v in ver])
        crh = np.array([np.sqrt((c**2.).sum()) for c in coords])
        rmx = np.amax(crh)
        rmn = np.amin(crh)
        print("Computing volumes...")
        vol = np.zeros(len(reg))
        cu1 = np.array([-1 not in r for r in reg])
        cu2 = np.array([np.product(np.logical_and(vrh[r]>rmn,vrh[r]<rmx),dtype=bool) for r in reg[cu1]])
        msk = cat.mask
        nsd = hp.npix2nside(len(msk))
        pid = hp.ang2pix(nsd,vth,vph)
        imk = msk[pid]
        cu3 = np.array([np.product(imk[r],dtype=bool) for r in reg[cu1][cu2]])
        cut = np.array(range(len(vol)))
        cut = cut[cu1][cu2][cu3]
        hul = []
        for r in reg[cut]:
            try:
                ch = ConvexHull(ver[r])
            except:
                ch = ConvexHull(ver[r],qhull_options='QJ')
            hul.append(ch)
        #hul = [ConvexHull(ver[r]) for r in reg[cut]]
        vol[cut] = np.array([h.volume for h in hul])
        self.volumes = vol
        print("Triangulating...")
        Del = Delaunay(coords)
        sim = Del.simplices
        nei = []
        lut = [[] for _ in range(len(vol))]
        print("Consolidating neighbors...")
        for i in range(len(sim)):
            for j in sim[i]:
                lut[j].append(i)
        for i in range(len(vol)):
            cut = np.array(lut[i])
            nei.append(np.unique(sim[cut]))
        self.neighbors = np.array(nei)

class Zones:
    def __init__(self,tess):
        vol   = tess.volumes
        nei   = tess.neighbors
        print("Sorting cells...")
        srt   = np.argsort(-1.*vol)        
        vol2  = vol[srt]
        nei2  = nei[srt]
        lut   = np.zeros(len(vol),dtype=int)
        zvols = []
        zcell = []
        print("Building zones...")
        for i in range(len(vol)):
            ns = nei2[i]
            vs = vol[ns]
            n  = ns[np.argmax(vs)]
            if n == srt[i]:
                lut[n] = len(zvols)
                zcell.append([n])
                zvols.append(vol[n])
            else:
                lut[srt[i]] = lut[n]
                zcell[lut[n]].append(srt[i])
        self.zcell = np.array(zcell)
        self.zvols = np.array(zvols)
        zlinks = [[[] for _ in range(len(zvols))] for _ in range(2)]       
        print("Linking zones...")
        for i in range(len(vol)):
            ns = nei[i]
            z1 = lut[i]
            for n in ns:
                z2 = lut[n]
                if z1 != z2:
                    if z2 not in zlinks[0][z1]:
                        zlinks[0][z1].append(z2)
                        zlinks[0][z2].append(z1)
                        zlinks[1][z1].append(0.)
                        zlinks[1][z2].append(0.)
                    j  = np.where(zlinks[0][z1] == z2)[0][0]
                    k  = np.where(zlinks[0][z2] == z1)[0][0]
                    nl = np.amin([vol[i],vol[n]])
                    ml = np.amax([zlinks[1][z1][j],nl])
                    zlinks[1][z1][j] = ml
                    zlinks[1][z2][k] = ml
        self.zlinks = zlinks

class Voids:
    def __init__(self,zon):
        zvols  = np.array(zon.zvols)
        zlinks = zon.zlinks
        print("Sorting links...")
        zl1   = np.array(list(flatten(zlinks[1])))
        zlu   = -1.*np.sort(-1.*np.unique(zl1))
        zl0   = np.array(list(flatten(zlinks[0])))
        zlut  = [np.unique(zl0[np.where(zl1==zl)[0]]).tolist() for zl in zlu]
        voids = []
        mvols = []
        ovols = []
        vlut  = np.array(range(len(zvols)))
        mvlut = np.array(zvols)
        ovlut = np.array(zvols)
        print("Expanding voids...")
        for i in range(len(zlu)):
            lvol  = zlu[i]
            mxvls = mvlut[zlut[i]]
            mvarg = np.argmax(mxvls)
            mxvol = mxvls[mvarg]
            for j in zlut[i]:
                if mvlut[j] < mxvol:                
                    voids.append([])
                    ovols.append([])
                    vcomp = np.where(vlut==vlut[j])[0]
                    for ov in -1.*np.sort(-1.*np.unique(ovlut[vcomp])):
                        ocomp = np.where(ovlut[vcomp]==ov)[0]
                        voids[-1].append(vcomp[ocomp].tolist())
                        ovols[-1].append(ov)
                    ovols[-1].append(lvol)
                    mvols.append(mvlut[j])
                    vlut[vcomp]  = vlut[zlut[i]][mvarg]
                    mvlut[vcomp] = mxvol
                    ovlut[vcomp] = lvol
        self.voids = voids
        self.mvols = mvols
        self.ovols = ovols
