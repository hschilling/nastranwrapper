"""
    comp_plate_static_nastran.py - Composite plate implementation example.
"""
import math

from openmdao.lib.datatypes.api import Float
from openmdao.util.filewrap import FileParser

from nastranwrapper.nastran import NastranComponent

class Comp_Plate(NastranComponent):
    """ Model of a composite plate """

    #initial thickness of each ply(sum of all the layers)

    thick1_init = 2.6562
    thick2_init = 2.6479
    thick3_init = 1.3309

    # design variables
    thick1 = Float(thick1_init, iotype="in", units="inch", desc="Thickness of pcomp 801")
    thick2 = Float(thick2_init, iotype="in", units="inch", desc="Thickness of pcomp 802")
    thick3 = Float(thick3_init, iotype="in", units="inch", desc="Thickness of pcomp 803")

    # outputs
    property1_max_major_strain = Float(0.0, iotype="out", desc="max major strain for pcomp 801")
    property2_max_major_strain = Float(0.0, iotype="out", desc="max major strain for pcomp 802")
    property3_max_major_strain = Float(0.0, iotype="out", desc="max major strain for pcomp 803")
    property1_max_minor_strain = Float(0.0, iotype="out", desc="max minor strain for pcomp 801")
    property2_max_minor_strain = Float(0.0, iotype="out", desc="max minor strain for pcomp 802")
    property3_max_minor_strain = Float(0.0, iotype="out", desc="max minor strain for pcomp 803")

    property1_max_major_minor_strain = Float(0.0, iotype="out", desc="max major minor strain for pcomp 801")
    property2_max_major_minor_strain = Float(0.0, iotype="out", desc="max major minor strain for pcomp 802")
    property3_max_major_minor_strain = Float(0.0, iotype="out", desc="max major minor strain for pcomp 803")

    def disp(op2,**args):
        d = op2.displacements[args['isubcase']].translations[args['id']][args['xyz']]
        return d

    displacement_18_z_dir = Float(1.25, iotype='out',
                                units='inch',
                                desc='Displacement in z-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':18,'xyz':2}
                                )
    def mass(op2):
        return op2.grid_point_weight.mass[0]

    weight = Float(0., nastran_func=mass, iotype='out', units='lb',
                        desc='Weight of the structure')

    def execute(self):

        print "before Nastran" #qqq

        super(Comp_Plate, self).execute()

        print "after Nastran" #qqq

        self.comp_elm_dict = {}
        # parser = FileParser()
        # parser.set_file(self.nastran_filename)
        # parser.reset_anchor()
        # for cquad4 in range(1,26):
        #     parser.mark_anchor("CQUAD4")
        #     elmtype = parser.transfer_var(0, 1)
        #     elmid = parser.transfer_var(0, 2)
        #     pid = parser.transfer_var(0, 3)

        #     if pid not in self.comp_elm_dict:
        #         self.comp_elm_dict[ pid ] = []

        #     self.comp_elm_dict[pid].append( elmid )

        for cquad4 in range(1,26):
            elmid = self.bdf.elements[cquad4].eid
            pid = self.bdf.elements[cquad4].pid.pid
            if pid not in self.comp_elm_dict:
                self.comp_elm_dict[ pid ] = []

            self.comp_elm_dict[pid].append( elmid )

        print "before calculate_max_strains" # qqq

        max_minor_strain_by_pid, max_major_strain_by_pid = self.calculate_max_strains()

        print "after calculate_max_strains" # qqq

        self.property1_max_major_strain = max_major_strain_by_pid[ 801 ]
        self.property2_max_major_strain = max_major_strain_by_pid[ 802 ]
        self.property3_max_major_strain = max_major_strain_by_pid[ 803 ]

        self.property1_max_minor_strain = max_minor_strain_by_pid[ 801 ]
        self.property2_max_minor_strain = max_minor_strain_by_pid[ 802 ]
        self.property3_max_minor_strain = max_minor_strain_by_pid[ 803 ]

        # Calculate the maximum strain (max(major,minor)) for each property 
        self.property1_max_major_minor_strain = max( self.property1_max_major_strain,
                                                     self.property1_max_minor_strain )
        self.property2_max_major_minor_strain = max( self.property2_max_major_strain,
                                                     self.property2_max_minor_strain )
        self.property3_max_major_minor_strain = max( self.property3_max_major_strain,
                                                     self.property3_max_minor_strain )

    def calculate_max_strains( self ):
        '''Using the data from the input.out file,
            calculate the max major and minor strains
            for each of the three properties'''

        #import pdb; pdb.set_trace()

        # Get the element ID, minor strain and major strain all at once
        # elm_id_minor_majors = self.parser.get("strains in layered composite elements (quad4)",
        #                                       1,
        #                                       {},
        #                                       ["ELEMENT ID",
        #                                        "PRINCIPAL  STRAINS (ZERO SHEAR) MINOR",
        #                                       "PRINCIPAL  STRAINS (ZERO SHEAR) MAJOR"])

        # returns a list like this

        #       [['1', '-6.20489E-03', '7.34675E-05'], ['1', '-2.06830E-03', '2.44892E-05'], ['1', '-2.44892E-05', '2.06830E-03'], ['1', '-7.34675E-05', '6.20489E-03'], ['2', '-3.15067E-03', '1.06995E-03'], ['2', '-1.05022E-03', '3.56652E-04'], ['2', '-3.56652E-04', '1.05022E-03'], ['2', '-1.06995E-03', '3.15067E-03'], ['3', '-2.45402E-03', '9.85521E-04'

        # find the max major and minor strains for each element ID
        max_major_strain_by_elmid = {}
        max_minor_strain_by_elmid = {}

        # for elm_id_minor_major in elm_id_minor_majors:
        #     elmid, minor, major = ( int(elm_id_minor_major[0]),
        #                             abs(float(elm_id_minor_major[1])),
        #                             abs(float(elm_id_minor_major[2]))
        #                             )

        isubcase = 1
        for elmid in self.op2.compositePlateStrain[isubcase].majorP :

            max_major_strain_by_elmid[ elmid ] = max( self.op2.compositePlateStrain[isubcase].majorP[elmid] )
            # returns a list like this
            # self.op2.compositePlateStrain[1].majorP[1]
            #  [7.347079372266307e-05, 2.4492490410921164e-05, 0.002068278146907687, 0.006204872392117977]
            max_minor_strain_by_elmid[ elmid ] = max( self.op2.compositePlateStrain[isubcase].minorP[elmid] )

            #if elmid in max_major_strain_by_elmid:
                #max_major_strain_by_elmid[ elmid ] = max( max_major_strain_by_elmid[ elmid ], major )
            #else:
                #max_major_strain_by_elmid[ elmid ] = major
                
            #if elmid in max_minor_strain_by_elmid:
                #max_minor_strain_by_elmid[ elmid ] = max( max_minor_strain_by_elmid[ elmid ], minor )
            #else:
                #max_minor_strain_by_elmid[ elmid ] = minor
                

        # Find the max minor and major strains for each property
        max_major_strain_by_pid = {}
        max_minor_strain_by_pid = {}
        # Go through the dictionary of self.comp_elm_dict
        for pid in self.comp_elm_dict:
            element_ids_in_pid = self.comp_elm_dict[ pid ]

            max_major_strain_by_pid[ pid ] = max( [ max_major_strain_by_elmid[ elmid ] for elmid in element_ids_in_pid ] ) 
            max_minor_strain_by_pid[ pid ] = max( [ max_minor_strain_by_elmid[ elmid ] for elmid in element_ids_in_pid ] ) 
 
            
            # # For each element in the pid, update the maximums
            # for elmid in element_ids_in_pid:
            #     if pid in max_major_strain_by_pid:
            #         max_major_strain_by_pid[ pid ] = max(
            #             max_major_strain_by_pid[ pid ],
            #             max_major_strain_by_elmid[ elmid ]
            #             )
            #     else:
            #         max_major_strain_by_pid[ pid ] = max_major_strain_by_elmid[ elmid ]
                    
            #     if pid in max_minor_strain_by_pid:
            #         max_minor_strain_by_pid[ pid ] = max(
            #             max_minor_strain_by_pid[ pid ],
            #             max_minor_strain_by_elmid[ elmid ]
            #             )
            #     else:
            #         max_minor_strain_by_pid[ pid ] = max_minor_strain_by_elmid[ elmid ]
                
        
        #for pid in max_minor_strain_by_pid:
        #    print "pid, max minor, max major", pid, max_minor_strain_by_pid[ pid ], max_major_strain_by_pid[ pid ]

        return max_minor_strain_by_pid, max_major_strain_by_pid
        

    def nastran_maker_hook(self, maker):

        # We want to keep the ratios of ply thickness
        # of each ply, but we want to change them in relation
        # to the overall thickness (t1, t2, and t3)

        # We'll use NastranMaker to set the individual ply's
        # thicknesses.

        super(Comp_Plate, self).nastran_maker_hook(maker)

        value_distribution = {"801" : [.25,.25,.25,.25],
                              "802" : [.25,.25,.25,.25],
                              "803" : [.25,.25,.25,.25]}

        
        # for each pcomp, we have to set all four plys
        for pcomp in range(1,4): # there are three pcomps
            id = str(800 + pcomp)
            values = []
            for x in value_distribution[id]:
                values.append(x * self.__getattribute__("thick%d" % pcomp) )

            for ply in range(4): # there are four plys
                plynum = 12 + 4 * ply + 2 * (ply/2)
                maker.set("PCOMP", id,
                          plynum, values[ply])

    def update_hook(self):

        # We want to keep the ratios of ply thickness
        # of each ply, but we want to change them in relation
        # to the overall thickness (t1, t2, and t3)

        # We'll use NastranMaker to set the individual ply's
        # thicknesses.

        #import pdb; pdb.set_trace()

        value_distribution = {"801" : [.25,.25,.25,.25],
                              "802" : [.25,.25,.25,.25],
                              "803" : [.25,.25,.25,.25]}

        
        # for each pcomp, we have to set all four plys
        for pcomp in range(1,4): # there are three pcomps
            id = str(800 + pcomp)
            values = []
            for x in value_distribution[id]:
                values.append(x * self.__getattribute__("thick%d" % pcomp) )

            for ply in range(4): # there are four plys
                #plynum = 12 + 4 * ply + 2 * (ply/2)
                #maker.set("PCOMP", id,
                #          plynum, values[ply])
                # PCOMP    801                    8100.    STRN                           +      A
                # +      A 801    .66405   0.      YES     801    .66405  45.      YES    +      B
                # +      B 801    .66405  -45.     YES     801    .66405   0.      YES
                pcomp = self.bdf.Property( int(id) , "qqq") 
                pcomp.plies[ply][1] = values[ply]
