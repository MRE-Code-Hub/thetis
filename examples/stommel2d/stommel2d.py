# Wave equation in 2D
# ===================
#
# Rectangular channel geometry.
#
# Tuomas Karna 2015-03-11

from cofs import *
import cofs.timeIntegration as timeIntegration
import time as timeMod

# set physical constants
physical_constants['z0_friction'].assign(0.0)

mesh2d = Mesh('stommel_square.msh')
nonlin = False
depth = 1000.0
outputDir = createDirectory('outputs')
T = 100*24*3600
TExport = 3600*2

# bathymetry
P1_2d = FunctionSpace(mesh2d, 'CG', 1)
P1v_2d = VectorFunctionSpace(mesh2d, 'CG', 1)
bathymetry2d = Function(P1_2d, name='Bathymetry')
bathymetry2d.assign(depth)

# Coriolis forcing
coriolis2d = Function(P1_2d)
betaPlaneCoriolisFunction(45.0, coriolis2d)

# Wind stress
windStress2d = Function(P1v_2d, name='wind stress')
tau_max = 0.1
L_y = 1.0e6
windStress2d.interpolate(Expression(('tau_max*sin(pi*x[1]/L)', '0'), tau_max=tau_max, L=L_y))

# linear dissipation: tau_bot/(h*rho) = -bf_gamma*u
lin_drag = Constant(1e-6)

# --- create solver ---
solverObj = solver.flowSolver2d(mesh2d, bathymetry2d)
solverObj.cfl_2d = 1.0
solverObj.nonlin = False
solverObj.coriolis = coriolis2d
solverObj.wind_stress = windStress2d
solverObj.lin_drag = lin_drag
solverObj.TExport = TExport
solverObj.T = T
solverObj.dt = 20.0
solverObj.outputDir = outputDir
solverObj.uAdvection = Constant(0.01)
solverObj.checkVolConservation2d = True
solverObj.fieldsToExport = ['uv2d', 'elev2d']
solverObj.timerLabels = []

solverObj.iterate()