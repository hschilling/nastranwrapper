"""``nastran.py`` defines NastranComponent.
  
"""
import sys
from os import path
from tempfile import mkdtemp, gettempdir
from shutil import rmtree

from openmdao.lib.components.external_code import ExternalCode

from openmdao.lib.datatypes.api import Float, Int, Array, Str, Bool, List

class NastranComponent(ExternalCode):
    """All Nastran-capable components should be subclasses of NastranComponent.

    By subclassing NastranComponent, any component should have easy access
    to NastranMaker, NastranReplacer, and NastranParser. Your subclass
    must specify how to handle the input and output variables to NastranComponent
    by specifying nastran-specific attributes on the traits. All of these
    attributes are described further in the :ref:`NastranComponent` docs.

    Note: This component does nothing with ``external_files``. If you want to deal with
    that, then do so in your subclass.
    """


    nastran_filename = Str(iotype="in", desc="Input filename with \
                                              placeholder variables.")
    nastran_command = Str(iotype="in", desc="Location of nastran \
                                             executable.")
    nastran_command_args = List(Str, iotype="in",
                                desc="Arguments to the nastran command.")

    output_filename = Str(iotype="out", desc="Output filename.")

    delete_tmp_files = Bool(True, iotype="in", desc="Should I delete \
                            the temporary files?")

    output_tempdir_dir = Str(gettempdir(), iotype="in", desc="Directory in which \
                                            to put the output temp dir.")


    keep_first_iteration = Bool(True, iotype="in", desc="If I am \
    deleting temporary files, should I keep the first one?")

    keep_last_iteration = Bool(True, iotype="in", desc="If I am \
    deleting temporary files, should I keep the last one?")

    def __init__(self):
        super(NastranComponent, self).__init__()

        # We're initializing parser here so that it's not an
        # honest-to-god trait, just an attribute that can
        # be accessed from the the class that subclasses NastranComponent
        self.parser = None

        self.bdf = None #qqq
        self.f06 = None #qqq
        self.op2 = None #qqq
        
        # This variables are just to keep track of what we've
        # deleted if you select keep_first_iteration or keep_last_iteration
        self._seen_first_iteration = False
        self._last_seen_iteration = ""


    def execute(self):
        """Runs the NastranComponent.

        We are overiding ExternalCode's execute function. First, we
        setup the input file (by running NastranReplacer and then
        NastranMaker). Next, we run Nastran by calling our
        parent's execute function. Finally, we parse the data
        and set the output variables given to us.

        RuntimeError
            The component relies on ExternalCode which can throw all
            sorts of RuntimeError-like exceptions (RunStopped,
            RunInterrupted also included).
            
        Filesystem-type Errors
            NastranComponent makes a temporary directory with mkdtemp
            in the temp module. If that fails, the error just
            propagates up.


        While there are no explicit parameters or return values for this
        function, it gets all the input it needs from the design
        variables that are connected to the subclass of NastranComponent.
        This should be described pretty well in the :ref:`documentation<NastranComponent>`.

        """
        # We are going to keep track of all the ways we
        # can manage input/output:
        #  - the crude way (NastranReplacer, NastranOutput)
        #    correspond to input_variables, output_variables
        #  - the better way (NastranMaker, NastranParser)
        #    correspond to smart_replacements and grid_outputs

        # all of these are {"traitname" : trait}
        input_variables = {}
        smart_replacements = {}
        output_variables = {}
        grid_outputs = {}

        for name, trait in self.traits().iteritems():
            if trait.iotype == "in":
                # nastran_var is a variable that should be replaced
                if trait.nastran_var:
                    # if the variable is longer than seven characters
                    # it won't fit in the nastran file, since the limit
                    # there is 8 characters (%xxxxxxx)
                    if len(trait.nastran_var) > 7:
                        raise ValueError("The variable " + trait.nastran + \
                                         " is too long to be a variable")
                    input_variables[name] = trait

                # it could also be a smart replacement, but we'll have
                # to specify the card, id, and fieldnum
                if trait.nastran_card and trait.nastran_id and trait.nastran_field:
                    smart_replacements[name] = trait
                # if trait.nastran_card and trait.nastran_id and trait.nastran_fieldnum:
                #     smart_replacements[name] = trait

                elif trait.nastran_card or trait.nastran_id or trait.nastran_fieldnum:
                    raise RuntimeError("You specified at least one of " + \
                                    "nastran_card, nastran_id, and " + \
                                    "nastran_fieldnum, but you did " + \
                                    "not specify all of them. You " + \
                                    "most probably mistyped.")

            elif trait.iotype == "out":

                # if we want to supply a function that will parse
                # out the wanted information from the output object
                # and the fileparser, then this
                if trait.nastran_func:
                    output_variables[name] = trait


                #qqq begin
                # if trait.pynastran_func:
                #     output_pynastran_variables[name] = trait
                #qqq end

                # this is the grid method of accessing. We have to
                # specify a header, row, and attribute and
                # the output variable will be set to that value
                elif trait.nastran_table and trait.nastran_id and trait.nastran_column:
                    grid_outputs[name] = trait
                elif trait.nastran_table or trait.nastran_id or trait.nastran_column:
                    raise RuntimeError("You specified at least one of " + \
                                    "nastran_table, nastran_id"+\
                                    ", and nastran_columns, but you " + \
                                    "did not specify all them. You " + \
                                    "most probably mistyped")

        # let's do our work in a tmp dir
        tmpdir = mkdtemp(dir = self.output_tempdir_dir)
        tmppath = path.join(tmpdir, "input.bdf")

        #### qqq pyNastran way to take inputs and write them to the BDF file
        from pyNastran.bdf.bdf import BDF

        pyNastran_get_card_methods = {
            'PSHELL': 'Property',
            'PROD': 'Property',
            'FORCE': 'Load',
            'MAT1': 'Material',
            }


        import logging
        self.bdf = BDF(debug=False,log=logging.getLogger() )
        #mesh.cardsToRead = set(['GRID','CQUAD4','PSHELL','MAT1','CORD2R'])
        # not required, but lets you limit the cards
        # if there's a problem with one


        #from os.path import split
        self.bdf.readBDF(self.nastran_filename,xref=True) # reads the bdf
        # bdf_dirname, bdf_filename = split( self.nastran_filename ) 
        # bdf.readBDF(bdf_filename,includeDir=bdf_dirname,xref=True) # reads the bdf
        for name, trait in smart_replacements.iteritems():
            # for now need to handle PROD, FORCE, MAT1


            #bdf.Property( 2 ,'qq')
            # 'mid', 'mid1', 'mid2', 'mid3', 'mid4', 'nsm', 'pid', 'printRawFields', 'print_card', 'rawFields', 'reprFields', 'repr_card', 't', 'tst', 'twelveIt3', 'type', 'writeCalculix', 'writeCodeAster', 'writeCodeAsterLoad', 'z1', 'z2'
            # from the QRG 
            # PID
            # MID1
            # T
            # MID2
            # 12I/T**3
            # MID3
            # TS/T
            # NSM
            # Z1
            # Z2
            # MID4
            
            value = getattr(self, name)
            id = int( trait.nastran_id )
            get_method = getattr( self.bdf, pyNastran_get_card_methods[ trait.nastran_card ] )
            import inspect
            args = inspect.getargspec(get_method).args

            if 'msg' in args:
                nastran_item = get_method( id, 'dummy msg' )
            else:
                nastran_item = get_method( id )

            if trait.nastran_card == 'FORCE' :
                nastran_item = nastran_item[0]

            if trait.nastran_field_index :
                getattr(nastran_item, trait.nastran_field)[ trait.nastran_field_index ] = value
                #setattr(nastran_item[ trait.nastran_field_index ] , trait.nastran_field, value)
            else:
                setattr(nastran_item, trait.nastran_field, value)

            
            # if trait.nastran_card == "PROD" :
            #     prop = bdf.Property( id, 'qqq' )
            #     if trait.nastran_fieldnum == 3:
            #         prop.A = value
            # elif trait.nastran_card == "FORCE" :
            #     load = bdf.Load( id, "qqq" )[0]
            #     if trait.nastran_fieldnum in [5,6,7]:
            #         load.xyz[ trait.nastran_fieldnum - 5 ] = value
            #     elif trait.nastran_fieldnum == 4:
            #         load.mag = value
            # elif trait.nastran_card == "MAT1" :
            #     # E which is Youngs modulus is rawFields()[2]
            #     # that does correspond to the nastran_fieldnum value
            #     # we use so indices are not off by one
            #     mat = bdf.Material( id )
            #     if trait.nastran_fieldnum == 2:
            #         mat.e = value
            #     elif trait.nastran_fieldnum == 5:
            #         mat.rho = value
            #     # maker.set(trait.nastran_card,
            #     #           trait.nastran_id,
            #     #           trait.nastran_fieldnum, value)

        self.update_hook()

        #self.bdf.write_bdf(tmppath)
        self.bdf.write_bdf(tmppath,precision='double',size=16)

        # what is the new file called?
        self.output_filename = path.join(tmpdir, "input.out")

        # perhaps this should be logged, or something
        print self.output_filename

        # Then we run the nastran file
        if self.nastran_command == 'python':  # True when using fake_nastran.py
            self.command = [self.nastran_command,
                            self.nastran_command_args[0], tmppath]
            self.command.extend(self.nastran_command_args[1:])
        else:
            self.command = [self.nastran_command, tmppath]
            self.command.extend(self.nastran_command_args)
        self.command.extend(["batch=no", "out=" + tmpdir, "dbs=" + tmpdir])

        # This calls ExternalCode's execute which will run
        # the nastran command via subprocess
        super(NastranComponent, self).execute()

        ###################
        # OP2
        from pyNastran.op2.op2 import OP2
        op2_filename = self.output_filename[:-4] + '.op2'
        f06_filename = self.output_filename
        self.op2 = OP2(op2_filename, debug=False,log=None)
        #self.op2.make_op2_debug = True   # can create a HUGE file that slows things down a lot
        #self.op2.readOP2()

        from pyNastran.f06.f06 import F06, FatalError
        self.f06 = F06(f06_filename,debug=False)  # debug True makes it slow
        import os
        if os.path.exists(op2_filename):
            try:
                self.op2.read_op2()  # doesn't tell you what the error message is
            except FatalError:
                try:
                    self.f06.read_f06()
                except FatalError as err:
                    raise RuntimeError('Nastran fatal error:' + str( err ) )
        elif os.path.exists(f06_filename):
            try:
                self.f06.read_f06()  # this will stop with a FatalError with the proper FATAL message
            except FatalError as err:
                raise RuntimeError('Nastran fatal error:' + str( err ) )
        else:
            raise RuntimeError('nastran fatal error' )


        
        #import pdb; pdb.set_trace()
        ###################


        # qqq start
        # get the outputs using pyNastran
        if 0:
            from pyNastran.f06.f06 import F06, FatalError
            self.f06 = F06(self.output_filename,debug=False)  # debug True makes it slow
            try:
                self.f06.readF06()
            except FatalError:
                raise RuntimeError("There was a problem with " + \
                                   "Nastran. It failed to run " + \
                                   "correctly. If you want to see " +\
                                   "the output, check out " + \
                                   self.output_filename)
        
        # try handling
        # nastran_header="displacement vector",
        # nastran_subcase=1,
        # nastran_constraints={"POINT ID." : "1"},
        # nastran_columns=["T2"])
        displacement_columns = ['T1','T2','T3']
        for name, trait in grid_outputs.iteritems():
            table = trait.nastran_table
            subcase = trait.nastran_subcase
            nastran_id = trait.nastran_id
            column = trait.nastran_column
            if table == "displacement vector" :
                ixyz = displacement_columns.index( column )
                setattr(self, name, self.op2.displacements[subcase].translations[nastran_id][ixyz])
        
        for output_name, output_trait in output_variables.iteritems():
            # We run trait.nastran_func on filep and get the
            # final value we want
            if output_trait.nastran_args:
                setattr(self, output_name,
                        #output_trait.nastran_func(self.op2,*output_trait.nastran_args))
                        output_trait.nastran_func(self.op2,**output_trait.nastran_args))
                        #output_trait.nastran_func(self.f06,*output_trait.nastran_args))
            else:
                setattr(self, output_name,
                        #output_trait.nastran_func(self.f06))
                        output_trait.nastran_func(self.op2))

        # get rid of our tmp dir
        tmpdir_to_delete = ""
        if self.delete_tmp_files:
            if self.keep_first_iteration:
                if not self._seen_first_iteration:
                    self._seen_first_iteration = True
                else:
                    if self.keep_last_iteration: # keep both
                        tmpdir_to_delete = self._last_seen_iteration
                        self._last_seen_iteration = tmpdir
                    else: # just keep first
                        tmpdir_to_delete = tmpdir
            else:
                if self.keep_last_iteration: # only keep last
                    tmpdir_to_delete = self._last_seen_iteration
                    self._last_seen_iteration = tmpdir
                else: # don't keep anything
                    tmpdir_to_delete = tmpdir

            if tmpdir_to_delete:
                rmtree(tmpdir_to_delete)

    def nastran_maker_hook(self, maker):
        """A subclass can override this function to dynamically
        add variables to NastranMaker.

        maker: NastranMaker object
            This NastranMaker object already has all the variables that
            were specified in the traits.

        The return will be ignored. Right after this function exits,
        the Nastran input file will be written out to a file.
        """
        pass

    def update_hook(self):
        """
        """
        pass
