## @ingroup Analyses-Aerodynamics
# AVL.py
#
# Created: Jul 2019, S. Karpuk 

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

import SUAVE
from SUAVE.Core import Data
from .Markup import Markup
from SUAVE.Analyses import Process
import numpy as np

# Default aero Results
from .Results import Results

# The aero methods
from SUAVE.Methods.Aerodynamics.Common            import Fidelity_Zero as Common
from SUAVE.Methods.Aerodynamics.Quasi_3D.Q3D      import Q3D as Quasi3D
from .Process_Geometry                            import Process_Geometry
from SUAVE.Analyses.Aerodynamics.AVL_Inviscid_Q3D import AVL_Inviscid_Q3D

# ----------------------------------------------------------------------
#  Analysis
# ----------------------------------------------------------------------
## @ingroup Analyses-Aerodynamics
class AVLQ3D(Markup):
    """This uses AVL to compute lift.

    Assumptions:
    None

    Source:
    None
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
        self.tag    = 'AVLQ3D_markup'       
    
        # Correction factors
        settings = self.settings
        settings.trim_drag_correction_factor        = 1.02
        settings.wing_parasite_drag_form_factor     = 1.1
        settings.fuselage_parasite_drag_form_factor = 2.3
        settings.oswald_efficiency_factor           = None
        settings.viscous_lift_dependent_drag_factor = 0.38
        settings.drag_coefficient_increment         = 0.0000
        settings.spoiler_drag_increment             = 0.00 
        
        # ------
        settings.spanwise_vortices                  = None
        settings.chordwise_vortices                 = None        
        
        settings.maximum_lift_coefficient           = np.inf 
        
                
        # Build the evaluation process
        compute = self.process.compute
        compute.lift = Process()

        # Run AVL to determine lift
        compute.lift.inviscid                      = AVL_Inviscid_Q3D()
        compute.lift.total                         = Common.Lift.aircraft_total
        # Do a traditional drag buildup for everything but the wing
        compute.drag = Process()
        compute.drag.parasite                      = Process()
        compute.drag.parasite.wings                = Process_Geometry('wings')
        compute.drag.parasite.wings.wing           = Quasi3D()                        
        compute.drag.parasite.fuselages            = Process_Geometry('fuselages')
        compute.drag.parasite.fuselages.fuselage   = Common.Drag.parasite_drag_fuselage
        compute.drag.parasite.propulsors           = Process_Geometry('propulsors')
        compute.drag.parasite.propulsors.propulsor = Common.Drag.parasite_drag_propulsor
        compute.drag.parasite.pylons               = Common.Drag.parasite_drag_pylon
        compute.drag.parasite.total                = Common.Drag.parasite_total
        compute.drag.compressibility               = Process()
        compute.drag.compressibility.wings         = Process_Geometry('wings')
        #compute.drag.compressibility.wings.wing    = Common.Drag.compressibility_drag_wing
        compute.drag.compressibility.total         = Common.Drag.compressibility_drag_wing_total        
        compute.drag.miscellaneous                 = Common.Drag.miscellaneous_drag_aircraft_ESDU
        compute.drag.untrimmed                     = Common.Drag.untrimmed
        compute.drag.trim                          = Common.Drag.trim
        compute.drag.spoiler                       = Common.Drag.spoiler_drag
        compute.drag.total                         = Common.Drag.total_aircraft
        
        
    def initialize(self):
        """Initializes the surrogate needed for AVL.

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
        # unpack
        sv = self.settings.spanwise_vortices
        cv = self.settings.chordwise_vortices 
        
        self.process.compute.lift.inviscid.geometry            = self.geometry
        self.process.compute.drag.parasite.wings.wing.geometry = self.geometry
        
        # Generate the surrogate
        self.process.compute.lift.inviscid.initialize(sv,cv)
        self.process.compute.drag.parasite.wings.wing.initialize()
        
    finalize = initialize
    
    