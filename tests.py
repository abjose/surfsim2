

#from rule import Constraint as C, ExecStep as E
#from node import Node
from context import Context

"""
i1 = E(["$name = 'test1'",
        "$value = 5",
        "$woop = True",
        "$position = (1,1)"])
i2 = E(["$name = 'test2'",
        "$value = 10",
        "$woop = False"])

c1 = C(["$name  = 'test1'",
        "$value = 6",])
c2 = C(["$value > 5"])
c3 = C(["$name ='test1' or $name='test2'",
        "$value = 5",])
"""

""" NOTES    
TODO: put useful Es and Cs into a file somewhere
      maybe make them into functions so you can modify their insides :O
NOTE: Problem that with *args can only do ALL conjunctions or ALL disjunctions?
NOTE: Note that for most things that need to be accessed from parents, easy
      to just do self.(whatever)!! so $parent.rule = $rule if don't overwrite
TODO: Come up with 'rules' on how to use things. For example, seeming like
      you must re-initialize everything before expecting it to work correctly,
      and you (maybe) can only do reference by name before initializing, and
      (maybe) must force things to only be 'dependent' on things higher in
      their own hierarchy (so don't initialize based on some random other 
      thing's position or something), and should initialize variables before
      referencing them...and don't connect things before initializing...
TODO: If going to have many things that take a (list of) input vectors but need
      to operate on only a single output vector...better way of doing?
TODO: Need to add some kind of "step_network" function
TODO: Would be nice to add something that catches exceptions when ExecSteps
      or Constraints don't work and tells you what the string is. Also could
      have warnings when variables are made without being prepended by $ or 
      other?
"""

# create context
s = Context()

# add stimulus sizes to root node...would be nicer if they went in stimulus node
# TODO: HOW TO HAVE RELATIVE 'parent' accesses? so could put these just in stimulus but check them from things that aren't children of stimulus?
s.add_rule('init',
           "$bcm_radius = 10",
           "$kernel_length = 30",
           "$stim_size = 50")

# add a container for stimulus and 'focus' on it
s.add_node('$name = "stimulus"')
s.set_focus('$name == "stimulus"')

# add a distribution rule for stimulus points
s.add_rule('init',
           '$child_grid = Grid(xl=$stim_size, yl=$stim_size)')

# also maintain a matrix of sinusoid values for stimulus points to access
s.add_rule('init',
           '$sin_input = SinusoidInput($stim_size, $stim_size)',
           '$sin_matrix = None')
s.add_rule('update',
           '$sin_input.step()', 
           '$sin_matrix = $sin_input.output')

# add a point of stimulus and change focus
s.add_node('$name = "stim_point"')
s.set_focus('$name == "stim_point"')

# make stim_point read from its associated position in parent's sinusoid matrix
s.add_rule('init', 
           '$x, $y = $child_grid.get_next()',
           '$init_output()')
s.add_rule('update',
           '$output.append($sin_matrix[$x][$y])', # ????
           '$clean_output()')

# make some stim_point copies...should technically make lots more than 10...
#s.set_focus('parent')
# TODO: want to change copy_node so that it takes constraints? 
s.copy_node(N=10)

# Add another node to root to act as the Ganglion Cell Module
s.set_focus('parent')
s.set_focus('parent')
s.add_node('$name = "GCM"')
s.set_focus('$name == "GCM"')

# Add a grid-positioning rule for BCMs (grid same size as stimulus)
s.add_rule('init',
           '$child_grid = Grid(dx=10, dy=10, xl=$stim_size, yl=$stim_size)')
           
# Add a node to act as a Bipolar Cell Module
s.add_node('$name = "BCM"')
s.set_focus('$name == "BCM"')

# Grab position from parent
s.add_rule('init',
           '$x, $y = $child_grid.get_next()')

# Add a node to act as a biphasic filter
s.add_node('$name = "biphasic"')
s.set_focus('$name == "biphasic"')

# Position randomly in a circle centered on parent
s.add_rule('init',
           "$x=rand_centered($parent().x, $bcm_radius)",
           "$y=rand_centered($parent().y, $bcm_radius)")

# Add a biphasic irf with amplitude proportional to distance from parent
s.add_rule('init', 
           '$irf = biphasic($kernel_length, ' + 
           '1/dist(($parent().x, $parent().y), ($x, $y)))') # ??? TODO

# use irf to update output vector
s.add_rule('update',
           '$output.append($convolve_input())',
           '$clean_output()') # ??? 

# Get connections from nearest input node
# could put something in parent to help?
# for now just connect if close, limit to one connection
s.add_rule('incoming',
           "other.name == 'stim_point'",
           "dist((other.x, other.y), ($x, $y)) < 10",
           "len($get_predecessors()) < 1") # ugly-ish

# want to make connection to BCM's sum node
s.add_rule('outgoing',
           'other.name == "sum"', 
           "$parent() == other.parent()") 

# set up sum
s.set_focus('parent')
s.add_node('$name = "sum"')
s.set_focus('$name == "sum"')
s.add_rule('init', '$init_output()')

# On ever step, sum inputs, push sum to end of output vector
s.add_rule('update',
           '$output.append(sum($get_inputs()))',
           '$clean_output()')

# want to make connections to thresh
s.add_rule('outgoing',
           'other.name == "thresh"',
           '$parent() == other.parent()') # want to verify shared parents?
# Don't have to worry about getting connections from biphasics - already handled

# set up thresh
s.set_focus('parent')
s.add_node('$name = "thresh"')
s.set_focus('$name == "thresh"')
s.add_rule('init', '$init_output()')

# threshold input vector
s.add_rule('update',
           # TODO: This is an ugly way of doing this
           '$output = thresh(verify_single($get_inputs())[0])', 
           '$clean_output()')

# make connections to sum of GCM...but skip for now
# also make copies of BCMs

# TODO: Need to init graph, actually connect things, and step simulation.
# hmm, isn't graph already basically initialized? Should still have some
# kind of "reinitialize" thing...

# Re-initialize entire circuit
s.reinitialize()

# make connections between necessary populations

# connect stim_points to biphasics
s.connect(['$name == "stim_point"'], 
          ['$name == "biphasic"']) 
# alternately could connect stim and bcm? or any combination...
# TODO: see if ^ works the same

# connect biphasics to sums
s.connect(['$name == "biphasic"'], 
          ['$name == "sum"'])

# connect sums to thresh
s.connect(['$name == "sum"'], 
          ['$name == "thresh"'])

