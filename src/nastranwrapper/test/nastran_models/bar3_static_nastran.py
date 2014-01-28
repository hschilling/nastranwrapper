import math

from openmdao.lib.datatypes.api import Float

from nastranwrapper.nastran import NastranComponent

class Bar3Static(NastranComponent):
    """ Model of a three bar truss - Fortran Implementation."""

    bar1_area  = Float(1., nastran_card="PROD",
                       nastran_id="11", #nastran_fieldnum=3,
                       nastran_field='A',
                       low=0.0009, high=10000.,
                       iotype='in', units='inch*inch',
                       desc='Cross-sectional area for bar 1')

    bar2_area  = Float(1., nastran_card="PROD",
                       nastran_id="12", #nastran_fieldnum=3,
                       nastran_field='A',
                       low=0.0009, high=10000.,
                       iotype='in', units='inch*inch',
                       desc='Cross-sectional area for bar 2')

    bar3_area  = Float(1., nastran_card='PROD',
                       nastran_id="13", #nastran_fieldnum=3,
                       nastran_field='A',
                       low=0.0009, high=10000.,
                        iotype='in', units='inch*inch',
                        desc='Cross-sectional area for bar 3')

    bar1_stress = Float(0., #nastran_func=stress1,
                        iotype='out',
                        units='lb/(inch*inch)',
                        desc='Stress in bar 1')
    bar2_stress = Float(0., #nastran_func=stress2,
                        iotype='out',
                        units='lb/(inch*inch)',
                        desc='Stress in bar 2')
    bar3_stress = Float(0., #nastran_func=stress3,
                        iotype='out',
                        units='lb/(inch*inch)',
                        desc='Stress in bar 3')

    def disp(op2,**keywords):
        d = op2.displacements[keywords['isubcase']].translations[keywords['id']][keywords['xyz']]
        return d

    displacement_x_dir = Float(0.20, iotype='out',
                               units='inch',
                               desc='Displacement in y-direction',
                               nastran_func=disp,
                               nastran_args={'isubcase':1,'id':1,'xyz':0}
                               )

    displacement_y_dir = Float(0.05, iotype='out',
                               units='inch',
                               desc='Displacement in y-direction',
                               nastran_func=disp,
                               nastran_args={'isubcase':1,'id':1,'xyz':1}
                               )


    # displacement_x_dir = Float(0.20, iotype='out',
    #                            units='inch',
    #                            desc='Displacement in x-direction',
    #                            #nastran_func=xdisp)
    #                            nastran_header="displacement vector",
    #                            nastran_subcase=1,
    #                            nastran_constraints={"POINT ID." : "1"},
    #                            nastran_columns=["T1"])

    # displacement_y_dir = Float(0.05, iotype='out',
    #                            units='inch',
    #                            desc='Displacement in y-direction',
    #                            #nastran_func=ydisp)
    #                            nastran_header="displacement vector",
    #                            nastran_subcase=1,
    #                            nastran_constraints={"POINT ID." : "1"},
    #                            nastran_columns=["T2"])
    #def mass(f06):
        #filep.reset_anchor()
        #filep.mark_anchor("MASS AXIS SYSTEM (S)")
        #return filep.transfer_var(1, 2)


    def mass(op2):
        return op2.grid_point_weight.mass[0]

    # def mass(filep):
    #      filep.reset_anchor()
    #      filep.mark_anchor("MASS AXIS SYSTEM (S)")
    #      return filep.transfer_var(1, 2)


    weight = Float(0., nastran_func=mass, iotype='out', units='lb',
                        desc='Weight of the structure')

    # weight = Float(0., nastran_func=mass, iotype='out', units='lb',
    #                     desc='Weight of the structure')

    # def ydisp(f06):
    #     subcase = 1
    #     point_id = 1
    #     dy = f06.displacements[subcase].translations[point_id][1]
    #     return dy

    # displacement_y_dir = Float(0.05, iotype='out',
    #                            units='inch',
    #                            desc='Displacement in y-direction',
    #                            nastran_func=ydisp)

    # def xdisp(f06):
    #     subcase = 1
    #     point_id = 1
    #     dx = f06.displacements[subcase].translations[point_id][0]
    #     return dx

    # displacement_x_dir = Float(0.05, iotype='out',
    #                            units='inch',
    #                            desc='Displacement in x-direction',
    #                            nastran_func=xdisp)




    def execute(self):
        """ Simulates the analysis of a three bar truss structure.
            Force, Stress, Displacement,Frequency and Weight are returned at
            the Bar3Truss output.
        """
        super(Bar3Static, self).execute()


        # self.rodStress
        # {1: ---ROD STRESSES---
        #         EID     eType      axial    torsion   MS_axial MS_torsion 
        #  1        CROD      64644          0          0          0 
        #  2        CROD      58578          0          0          0 
        #  3        CROD      -6066          0          2          0 
        #  }

        # dir(self.rodStress[1])0

        # ['MS_axial', 'MS_torsion', '__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__reprTransient__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_write_f06_transient', '_write_matlab_args', 'add_f06_data', 'add_new_eid', 'add_new_eid_sort1', 'add_new_eid_sort2', 'add_new_transient', 'analysis_code', 'append_data_member', 'apply_data_code', 'axial', 'code', 'code_information', 'data_code', 'delete_transient', 'device_code', 'dt', 'eType', 'element_name', 'element_type', 'format_code', 'getLength', 'getOrderedETypes', 'getUnsteadyValue', 'getVar', 'get_data_code', 'get_element_type', 'get_stats', 'get_transients', 'isCurvature', 'isCurvatureOld', 'isFiberDistance', 'isImaginary', 'isMaxShear', 'isRandomResponse', 'isReal', 'isRealImaginaryOrMagnitudePhase', 'isRealOrRandom', 'isSort2', 'isSortedResponse', 'isStrain', 'isStress', 'isThermal', 'isTransient', 'isVonMises', 'is_magnitude_phase', 'is_real_imaginary', 'is_sort1', 'isubcase', 'log', 'name', 'nonlinear_factor', 'num_wide', 'print_data_members', 'print_table_code', 'recastGridType', 's_code', 'set_data_members', 'set_var', 'sort_bits', 'sort_code', 'start_data_member', 'stress_bits', 'table_code', 'table_name', 'torsion', 'update_data_code', 'update_dt', 'write_f06']

        stresses = []
        # header = "S T R E S S E S   I N   R O D   E L E M E N T S      ( C R O D )"
        for i in range(1,4):
            # constraints = {"ELEMENT ID." : str(i)}

            # columns = ["AXIAL STRESS", "TORSIONAL STRESS"]
            # [[axial, torsion]] = self.parser.get(header, None, \
            #                                  constraints, columns)
            # axial_old, torsion_old = map(float, [axial, torsion])

            isubcase = 1
            #axial = self.f06.rodStress[isubcase].axial[ i ]
            #torsion = self.f06.rodStress[isubcase].torsion[ i  ]
            axial = self.op2.rodStress[isubcase].axial[ i ]
            torsion = self.op2.rodStress[isubcase].torsion[ i  ]
            stresses.append((axial, torsion))

        [self.bar1_stress, self.bar2_stress, self.bar3_stress] = \
                          map(calculate_stress, stresses)


def calculate_stress((ax, tors)):
    sigma = 2 * ax * ax
    tau = 3 * tors * tors
    val = math.sqrt(.5 * (sigma + tau))
    return val
