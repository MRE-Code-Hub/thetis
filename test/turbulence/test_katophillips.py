"""
Wind-driver entrainment test case.

Based on Kato-Phillips laboratory tests.

Initial water column is stratified with a constant density gradient.
Circulation is driven by constant wind stress at the surface. Wind-induced
mixing begins to destroy stratification, creating a well-mixed surfacelayer.
The depth of the surface layer follows an empirical relation versus time.

Surface friction velocity is u_s = 0.01 m s-1.
Initially buoyancy frequency is constant N = 0.01 s-1.


[1] http://www.gotm.net/
[2] Karna et al. (2012). Coupling of a discontinuous Galerkin finite element
    marine model with a finite difference turbulence closure model.
    Ocean Modelling, 47:55-64.
    http://dx.doi.org/10.1016/j.ocemod.2012.01.001

Tuomas Karna 2016-03-05
"""
from thetis import *
import numpy


def run_katophillips(do_export=False):
    physical_constants['rho0'] = 1027.0  # NOTE must match empirical setup

    outputdir = 'outputs'
    # set mesh resolution
    dx = 2500.0
    layers = 20
    depth = 50.0

    # generate unit mesh and transform its coords
    nx = 3  # nb elements in flow direction
    lx = nx*dx
    ny = 2  # nb elements in cross direction
    ly = ny*dx
    mesh2d = PeriodicRectangleMesh(nx, ny, lx, ly, direction='x', reorder=True)
    # move mesh, center to (0,0)
    mesh2d.coordinates.dat.data[:, 0] -= lx/2
    mesh2d.coordinates.dat.data[:, 1] -= ly/2

    dt = 60.0
    t_end = 4 * 3600.0
    t_export = 5*60.0
    u_mag = 1.0

    # bathymetry
    p1_2d = FunctionSpace(mesh2d, 'CG', 1)
    bathymetry2d = Function(p1_2d, name='Bathymetry')
    bathymetry2d.assign(depth)

    wind_stress_x = 0.1027  # Pa
    wind_stress_2d = Constant((wind_stress_x, 0))

    # create solver
    solver_obj = solver.FlowSolver(mesh2d, bathymetry2d, layers)
    options = solver_obj.options
    options.nonlin = False
    options.solve_salt = True
    options.solve_temp = False
    options.constant_temp = Constant(10.0)
    options.solve_vert_diffusion = True
    options.use_bottom_friction = True
    options.use_turbulence = True
    options.use_ale_moving_mesh = False
    options.baroclinic = True
    options.use_limiter_for_tracers = False
    options.v_viscosity = Constant(1.3e-6)  # background value
    options.v_diffusivity = Constant(1.4e-7)  # background value
    options.wind_stress = wind_stress_2d
    options.no_exports = not do_export
    options.t_export = t_export
    options.dt = dt
    options.t_end = t_end
    options.outputdir = outputdir
    options.u_advection = u_mag
    options.check_salt_overshoot = True
    options.timer_labels = []
    options.fields_to_export = ['uv_2d', 'elev_2d', 'elev_3d', 'uv_3d',
                                'w_3d', 'w_mesh_3d', 'salt_3d',
                                'baroc_head_3d', 'baroc_head_2d',
                                'uv_dav_2d', 'uv_bottom_2d',
                                'parab_visc_3d', 'eddy_visc_3d',
                                'shear_freq_3d', 'buoy_freq_3d',
                                'tke_3d', 'psi_3d', 'eps_3d', 'len_3d', ]
    options.fields_to_export_hdf5 = ['uv_3d', 'salt_3d', 'uv_bottom_2d',
                                     'eddy_visc_3d', 'eddy_diff_3d',
                                     'shear_freq_3d', 'buoy_freq_3d',
                                     'tke_3d', 'psi_3d', 'eps_3d', 'len_3d', ]

    solver_obj.create_function_spaces()

    # initial conditions
    buoyfreq0 = 0.01
    rho_grad = -buoyfreq0**2 * physical_constants['rho0'] / physical_constants['g_grav']
    beta = 0.7865  # haline contraction coefficient [kg m-3 psu-1]
    salt_grad = rho_grad/beta
    salt_init3d = Function(solver_obj.function_spaces.H, name='initial salinity')
    salt_init_expr = Expression('dsdz*x[2]', dsdz=salt_grad)
    salt_init3d.interpolate(salt_init_expr)

    solver_obj.assign_initial_conditions(salt=salt_init3d)

    solver_obj.iterate()

    # check mixed layer depth
    npoints = layers*4
    z = numpy.linspace(0, -depth, npoints)
    x = numpy.zeros_like(z)
    y = numpy.zeros_like(z)
    xyz = numpy.vstack((x, y, z)).T
    tke_arr = numpy.array(solver_obj.fields.tke_3d.at(tuple(xyz)))
    # mixed layer depth: lowest point where tke > tol
    tke_tol = 1e-5
    ix = tke_arr > tke_tol
    if ix.any():
        ml_depth = -z[ix].min()
    else:
        ml_depth = 0.0
    # correct depth
    u_s = 0.01
    buoyfreq0 = 0.01
    target = 1.05*u_s*np.sqrt(solver_obj.simulation_time/buoyfreq0)
    rtol = 0.05
    rel_err = (ml_depth - target)/target
    assert rel_err > -rtol, 'mixed layer is too shallow: {:} < {:}'.format(ml_depth, target)
    assert rel_err < rtol, 'mixed layer is too deep: {:} > {:}'.format(ml_depth, target)


def test_katophillips():
    run_katophillips()

if __name__ == '__main__':
    run_katophillips(do_export=True)