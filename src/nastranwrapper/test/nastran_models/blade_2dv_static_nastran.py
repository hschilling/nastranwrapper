"""
    blade_2dv_static_nastran.py - Blade implementation for a quad
    example structures problem. 
"""
import math

from openmdao.lib.datatypes.api import Float

from nastranwrapper.nastran import NastranComponent
from nastranwrapper.test.nastranwrapper_test_utils import calculate_stress

class BladeStatic(NastranComponent):
    """ Model of a Blade quad elements  - Nastran Implementation."""

    group1_thickness  = Float(0.5, nastran_card="PSHELL",
                       nastran_id="1",
                       nastran_field="T",
                       iotype='in', units='inch',
                       desc='Thickness for group 1')

    group2_thickness  = Float(0.03, nastran_card="PSHELL",
                       nastran_id="2",
                       nastran_field="T",
                       iotype='in', units='inch',
                       desc='Thickness for group 2')

    # these are actually groups of stresses that will be
    # constrained

    group1_stress = Float(0., #nastran_func=stress1,
                        iotype='out',
                        units='lb/(inch*inch)',
                        desc='Stress in group 1')
    group2_stress = Float(0., #nastran_func=stress2,
                        iotype='out',
                        units='lb/(inch*inch)',
                        desc='Stress in group 2')

    def disp(op2,**keywords):
        d = op2.displacements[keywords['isubcase']].translations[keywords['id']][keywords['xyz']]
        return d

    displacement_z_dir = Float(0.1632, iotype='out',
                               units='inch',
                               desc='Displacement in z-direction',
                               nastran_func=disp,
                               nastran_args={'isubcase':1,'id':28,'xyz':2}
                               )
    def mass(op2):
        return op2.grid_point_weight.mass[0]

    weight = Float(0., nastran_func=mass, iotype='out', units='lb',
                        desc='Weight of the structure')

    def execute(self):
        """ Simulates the analysis of a blade with quad elements.
            Force, Stress, Displacement,Frequency and Weight are returned at
            the Blade output.
        """

        super(BladeStatic, self).execute()

        # stresses = []
        # header = "S T R E S S E S   I N   Q U A D R I L A T E R A L   E L E M E N T S   ( Q U A D 4 )        OPTION = BILIN"

        # columns = ["VON MISES"]
        # data = self.parser.get(header, None, \
        #                        {}, columns, row_width=15)
        # von_mises =[]
        # for element in data:
        #     # element looks like  [['9.859733E+04'], ['2.391967E+05'], [''], ['9.494320E+04'], ['2.176725E+05'], [''], ['8.193106E+04'], ['2.595611E+05'], [''], ['1.056561E+05'], ['2.623137E+05'], [''], ['1.184271E+05'], ['2.195168E+05'], ['']]
        #     values = map(lambda x: x[0],element)
        #     # values looks like  ['9.859733E+04', '2.391967E+05', '', '9.494320E+04', '2.176725E+05', '', '8.193106E+04', '2.595611E+05', '', '1.056561E+05', '2.623137E+05', '', '1.184271E+05', '2.195168E+05', '']
        #     biggest = -1.0E+10
        #     for value in values: 
        #         if value != '':
        #            biggest = max(float(value),biggest)  
        #     von_mises.append(biggest)

        # self.f06.plateStress[1].ovmShear[1]
        # looks like this
        #{1: [94943.2, 217672.5], u'C': [98597.33, 239196.7], 83: [105656.1, 262313.7], 82: [118427.1, 219516.8], 2: [81931.06, 259561.1]}
        # where the second 1 is a key in ovmShear indicating the element id. The keys in the dictionary
        #   inside of that are grid-id values

        isubcase = 1
        von_mises =[]
        for eid, ovmShear in self.op2.plateStress[isubcase].ovmShear.iteritems() :
            biggest = max( max( s[0], s[1] ) for s in ovmShear.values() )
            von_mises.append(biggest)
            # cmd = "self.tria%d_stress = biggest" %i
            # exec(cmd)
                
        # for i in range(157,253):
        #     import pdb; pdb.set_trace()
        #     biggest = self.f06.plateStress[isubcase].ovmShear[i]['C'][0]
        #     # values = map(lambda x: x[0],element)
        #     # biggest = -1.0E+10
        #     # for value in values:
        #     #     if value != '':
        #     #        biggest = max(float(value),biggest)
        #     #von_mises.append(biggest)
        #     cmd = "self.tria%d_stress = biggest" %i
        #     exec(cmd)

        groups = [range(25601,25945+1), range(1, 25600+1)]

        [self.group1_stress, self.group2_stress] = group_von_mises(groups, von_mises) 

def group_von_mises(groups, von_mises):
    final = []
    for group in groups:
        final.append([])
        for element in group:
            final[-1].append(abs(von_mises[element-1])) # stresses is zero indexed
        # we actually just wanted the maximum
        final[-1] = max(final[-1])
    return final
