## @ingroup Analyses-Aerodynamics
# Fidelity_Zero.py
#
# Created:  
# Modified: Feb 2016, Andrew Wendorff

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

import SUAVE
from SUAVE.Core import Data
from .Markup import Markup
from SUAVE.Analyses import Process
import numpy as np
import pylab as plt

# default Aero Results
from .Results import Results

# the aero methods
from SUAVE.Methods.Aerodynamics import Fidelity_Zero as Methods
from SUAVE.Methods.Aerodynamics.Common import Fidelity_Zero as Common
from .Process_Geometry import Process_Geometry
from .Vortex_Lattice import Vortex_Lattice
from smt.surrogate_models import RMTB

# ----------------------------------------------------------------------
#  Analysis
# ----------------------------------------------------------------------
## @ingroup Analyses-Aerodynamics
class Fidelity_Zero_Wing_Surrogate(Markup):
    """This is an analysis based on low-fidelity models.

    Assumptions:
    Subsonic

    Source:
    Primarily based on adg.stanford.edu, see methods for details
    """       
    def __defaults__(self):
        """This sets the default values and methods for the analysis.

        Assumptions:
        None

        Source:
        N/A

        Inputs:
        None

        Outputs:
        None

        Properties Used:
        N/A
        """          
        self.tag            = 'fidelity_zero_markup'
        self.input_file     = None
              
        #self.process = Process()
        #self.process.initialize = Process()
        #self.process.compute = Process()        
    
        # correction factors
        settings = self.settings
        settings.fuselage_lift_correction           = 1.14
        settings.trim_drag_correction_factor        = 1.02
        settings.wing_parasite_drag_form_factor     = 1.1
        settings.fuselage_parasite_drag_form_factor = 2.3
        settings.oswald_efficiency_factor           = None
        settings.viscous_lift_dependent_drag_factor = 0.38
        settings.drag_coefficient_increment         = 0.0000
        settings.spoiler_drag_increment             = 0.00 
        settings.maximum_lift_coefficient           = np.inf 
        settings.maximum_lift_coefficient_factor    = 1.0
        
        # vortex lattice configurations
        settings.number_panels_spanwise  = 5
        settings.number_panels_chordwise = 1
        
        
        # build the evaluation process
        compute = self.process.compute
        
        # these methods have interface as
        # results = function(state,settings,geometry)
        # results are optional
        
        # first stub out empty functions
        # then implement methods
        # then we'll figure out how to connect to a mission
        
        compute.lift = Process()

        compute.lift.inviscid_wings                = Vortex_Lattice()
        compute.lift.vortex                        = SUAVE.Methods.skip
        compute.lift.compressible_wings            = Methods.Lift.wing_compressibility_correction
        compute.lift.fuselage                      = Common.Lift.fuselage_correction
        compute.lift.total                         = Common.Lift.aircraft_total
        
        compute.drag = Process()
        compute.drag.parasite                      = Process()
        compute.drag.parasite.wings                = Process_Geometry('wings')
        compute.drag.parasite.wings.wing           = Common.Drag.parasite_drag_wing 
        compute.drag.parasite.fuselages            = Process_Geometry('fuselages')
        compute.drag.parasite.fuselages.fuselage   = Common.Drag.parasite_drag_fuselage
        compute.drag.parasite.propulsors           = Process_Geometry('propulsors')
        compute.drag.parasite.propulsors.propulsor = Common.Drag.parasite_drag_propulsor
        compute.drag.parasite.pylons               = Common.Drag.parasite_drag_pylon
        compute.drag.compressibility               = Process()
        compute.drag.compressibility.wings         = Process_Geometry('wings')
        compute.drag.compressibility.wings.wing    = Common.Drag.compressibility_drag_wing
        compute.drag.compressibility.total         = Common.Drag.compressibility_drag_wing_total
        compute.drag.induced                       = Common.Drag.induced_drag_aircraft
        compute.drag.parasite.total                = Common.Drag.total_drag_wing_surrogate           # surrogate model for the wing drag
        compute.drag.miscellaneous                 = Common.Drag.miscellaneous_drag_aircraft_ESDU
        compute.drag.untrimmed                     = Common.Drag.untrimmed
        compute.drag.trim                          = Common.Drag.trim
        compute.drag.spoiler                       = Common.Drag.spoiler_drag
        compute.drag.total                         = Common.Drag.total_aircraft
        
        
    def initialize(self):
        """Initializes the surrogate needed for lift calculation.

        Assumptions:
        None

        Source:
        N/A

        Inputs:
        None

        Outputs:
        None

        Properties Used:
        self.geometry
        """                  
        self.process.compute.lift.inviscid_wings.geometry = self.geometry
        self.process.compute.lift.inviscid_wings.initialize()

        # Sample training for the wing drag coefficient
                
        # file name to look for
        file_name = self.input_file
       
        # Load the CSV file
        my_data = np.genfromtxt(file_name, delimiter=';')

        # Remove the header line
        my_data = np.delete(my_data,np.s_[0],axis=0)

        # Generate the SMT input
        CL_data       = my_data[:,0]
        altitude_data = my_data[:,4]/np.max( my_data[:,4]) 
        mach_data     = my_data[:,6]
        CD_data       = my_data[:,7]

        xy = np.hstack([CL_data.reshape(-1, 1),altitude_data.reshape(-1, 1),mach_data.reshape(-1, 1)])

        # set the surrogate data limits
        xlimits = np.array([[np.amin(CL_data),np.amax(CL_data)+0.1],\
                            [np.min(altitude_data),np.amax(altitude_data)+0.1],\
                            [np.min(mach_data), np.amax(mach_data)+0.1]])    
        CD_surrogate = RMTB(print_global=False, num_ctrl_pts=20, xlimits=xlimits, nonlinear_maxiter=100, energy_weight=1e-12)
        CD_surrogate.set_training_values(xy, CD_data)
        CD_surrogate.train()

        self.settings.surrogate_drag_wing  = CD_surrogate
        # check surrogate data
        CD_check = CD_surrogate.predict_values(xy)

        plt.figure()
        plt.plot(CD_data,CD_data,'k')
        plt.scatter(CD_data,CD_check)
        plt.grid(True)
        plt.xlabel('actual data')
        plt.ylabel('predicted data')
        plt.title("Drag surrogate check")
        plt.savefig('surrogate_CD.png') 

        
    finalize = initialize