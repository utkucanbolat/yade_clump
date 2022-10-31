import numpy as np
import subprocess
from yade import pack, utils, plot
from scipy.io import loadmat
from time import perf_counter


class MultiSphere:
    def __init__(self):
        """initialize the parameters for running the CLUMP file"""

        self.method_name = "clumpGenerator_Euclidean_3D"
        self.stlFile = "Rock.stl"
        self.N = 150
        self.rMin = 0
        self.div = 100
        self.overlap = 0.6
        self.output = "output"

        self.CLUMP_data, self.clump_pos, self.clump_radii = None, None, None

    def run_CLUMP(self, showElapsedTime=True):
        """run the CLUMP matlab file by providing the inputs defined in the initilization"""
        t0 = perf_counter()

        # be sure that matlab is added to your system PATH
        subprocess.run(
            f'matlab -nodesktop -nodisplay -nosplash -batch "{self.method_name} {self.stlFile} {self.N} {self.rMin} '
            f'{self.div} {self.overlap} {self.output}"', shell=True)

        if showElapsedTime:
            print(f"{'#' * 75}\nTime elapsed for clump generation:\t{perf_counter() - t0}\n{'#' * 75}")

    def read_CLUMP(self):
        """Import the output file that is created by MATLAB"""
        self.CLUMP_data = loadmat(self.output + ".mat")
        self.clump_pos = self.CLUMP_data["clump"][0][0][0]
        self.clump_radii = self.CLUMP_data["clump"][0][0][1]

    def form_multisphere(self):
        """Create a clump out of spheres with the positions and radius provided by the CLUMP code"""
        list_of_spheres_in_clump = []
        for coor, radius in zip(self.clump_pos, self.clump_radii):
            list_of_spheres_in_clump.append(
                utils.sphere([float(coor[0]), float(coor[1]), float(coor[2])], float(radius))
                # utils.sphere only accepts float, not np.array.
            )

        return list_of_spheres_in_clump

    def to_simulation(self):
        """Add the formed clump to the simulation"""
        return O.bodies.appendClumped(self.form_multisphere())

    def create_template(self):
        """To make a pack of clumps one can use pack.SpherePack() together with bodies.replaceByClumps.
        To replace spheres with clumps, one must create a clump template because bodies.replaceByClumps only accepts
        clump template. This function creates the template from a given clump."""

        # each element of clump_radii is list but we need float
        # so we change them into list of floats first
 
        clump_r = [float(i) for i in self.clump_radii]
        clump_p = np.ndarray.tolist(self.clump_pos)

        template = [clumpTemplate(relRadii=clump_r, relPositions=clump_p)]
        return template

    def translate(self, x=0.0, y=0.0, z=0.0):
        """translate the clump position by translating the positions of all the constituent particles"""
        self.clump_pos += np.ones((np.shape(self.clump_pos)[0], 1)) * np.array([x, y, z])


cl = MultiSphere()  # instantiate the class
cl.run_CLUMP()  # run the CLUMP code. If the output was already created, one would skip this step by commenting out
cl.read_CLUMP()  # read output file and import clump properties
cl.form_multisphere()  # form multisphere using the imported clump position and radius values
cl.to_simulation()  # add the formed multisphere to the simulation

""" 
# For creating a cloud of clumps, you can uncomment this section 
cl = MultiSphere()
cl.read_CLUMP()
template = cl.create_template()

id_Mat = O.materials.append(FrictMat(young=1e7, poisson=0.3, density=1000, frictionAngle=1))
Mat = O.materials[id_Mat]

sp = pack.SpherePack()
sp.makeCloud(minCorner=(0.0, 0.0, 0.0), maxCorner=(10.0, 10.0, 10.0), rMean=0, rRelFuzz=0, num=100, periodic=False)
O.bodies.append([sphere(c, r, material=Mat) for c, r in sp])
O.bodies.replaceByClumps(template, [1])
"""

# define the simulation parameters
O.engines = [ForceResetter(),
             InsertionSortCollider([Bo1_Sphere_Aabb(), Bo1_Wall_Aabb()]),
             InteractionLoop(
                 [Ig2_Sphere_Sphere_ScGeom(), Ig2_Wall_Sphere_ScGeom()],
                 [Ip2_FrictMat_FrictMat_FrictPhys()],
                 [Law2_ScGeom_FrictPhys_CundallStrack()]
             ),
             GravityEngine(gravity=(0, 0, -9.81)),
             NewtonIntegrator(damping=.2, label='newtonCustomLabel')
             ]

O.dt = 0.5 * utils.PWaveTimeStep()
