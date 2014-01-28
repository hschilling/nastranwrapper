"""
    ring_25dv_static_nastran.py - Ring implementation for the a sixty bar truss
    example structures problem. This openMDAO component contains a sixty bar
    truss example referenced in CometBoards
"""
import math

from openmdao.lib.datatypes.api import Float

from nastranwrapper.nastran import NastranComponent

class RingTruss(NastranComponent):

    for i in range(1,26):
        cmd = "bar%d_init_area = 1.0" %i
        exec (cmd)
        cmd = 'bar%d_area  = Float(bar%d_init_area, nastran_card="PROD",\
                       nastran_id="%d", \
                       nastran_field="A",\
                       iotype="in", units="inch*inch",\
                       desc="Cross-sectional area for bar %d")' %(i,i,i,i)
        exec(cmd)

    # these are stresses that will be  constrained

    for i in range(1,61):
        cmd = "bar%d_stress = Float(0., iotype='out', units='lb/(inch*inch)', desc='Axial stress in element %d')" %(i,i)
        exec(cmd)

    # these are displacements that will be  constrained

    def disp(op2,**args):
        d = op2.displacements[args['isubcase']].translations[args['id']][args['xyz']]
        return d

    displacement1_x_dir = Float(1.25, iotype='out',
                                units='inch',
                                desc='Displacement in x-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':10,'xyz':0}
                                )

    displacement1_y_dir = Float(1.25, iotype='out',
                                units='inch',
                                desc='Displacement in y-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':10,'xyz':1}
                                )

    displacement2_x_dir = Float(1.75, iotype='out',
                                units='inch',
                                desc='Displacement in x-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':4,'xyz':0},
                                )

    displacement2_y_dir = Float(1.75, iotype='out',
                                units='inch',
                                desc='Displacement in y-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':4,'xyz':1},
                                )

    displacement3_x_dir = Float(2.75, iotype='out',
                                units='inch',
                                desc='Displacement in x-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':19,'xyz':0},
                                )

    displacement3_y_dir = Float(2.75, iotype='out',
                                units='inch',
                                desc='Displacement in y-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':19,'xyz':1},
                                )

    displacement4_x_dir = Float(2.25, iotype='out',
                                units='inch',
                                desc='Displacement in x-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':13,'xyz':0},
                                )

    displacement4_y_dir = Float(2.25, iotype='out',
                                units='inch',
                                desc='Displacement in y-direction',
                                nastran_func=disp,
                                nastran_args={'isubcase':1,'id':13,'xyz':1},
                                )

    def mass(op2):
        return op2.grid_point_weight.mass[0]

    weight = Float(0., nastran_func=mass, iotype='out', units='lb',
                        desc='Weight of the structure')


    def execute(self):
        """ Simulates the analysis of a sixty bar truss structure.
            Force, Stress, Displacement,Frequency and Weight are returned at
            the Ring output.
        """
        super(RingTruss, self).execute()

        # stresses = []
        # header = "S T R E S S E S   I N   R O D   E L E M E N T S      ( C R O D )"


        # columns = ["AXIAL STRESS", "TORSIONAL STRESS"]
        # data = self.parser.get(header, None, \
        #                        {}, columns)

        # for i, stresses in enumerate(data):
        #     stress = calculate_stress((float(stresses[0]), float(stresses[1])))
        #     cmd = "self.bar%d_stress = stress" % (i+1)
        #     exec(cmd)

        isubcase = 1
        for i in range( len( self.op2.rodStress[isubcase].axial ) ) :
            stress = calculate_stress( ( self.op2.rodStress[isubcase].axial[ i + 1 ],
                                       self.op2.rodStress[isubcase].torsion[ i + 1 ] ) )
            cmd = "self.bar%d_stress = stress" % (i+1)
            exec(cmd)

def calculate_stress((ax, tors)):
    sigma = 2 * ax * ax
    tau = 3 * tors * tors
    val = math.sqrt(.5 * (sigma + tau))
    return val


