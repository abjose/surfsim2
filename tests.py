

from rule import Constraint as C, ExecStep as E
import random
#from node import Node
from context import Context
import matplotlib.pyplot as plt
import numpy as np

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
TODO: Would be nice to add something that catches exceptions when ExecSteps
      or Constraints don't work and tells you what the string is. 
TODO: Have warnings when variables are made without being prepended by $ or 
      other?
TODO: Why is nothing shown for initialization during copies?
TODO: Could....add a second init step so there's one before connections
      and one after?
"""

# create context
s = Context()

# add stimulus sizes to root node...would be nicer if they went in stimulus node
s.add_rule('init',
           '$kernel_length = 10',
           '$output_length = 50',
           '$bcm_radius = 4.',
           '$stim_size  = 20',
           '$max_delay  = 3')
           # add all grids here? just name differently...
# NOTE: these are one longer than you think - fix?



# add a container for stimulus and 'focus' on it
s.add_node('$name = "stimulus"')
s.set_focus('$name == "stimulus"')

# add a distribution rule for stimulus points
s.add_rule('init',
           # dx and dy were initially 2 for both of these, changing temporarily
           '$stim_grid = Grid(xl=$stim_size, yl=$stim_size, dx=1, dy=1)',
           # should just reset stim_grid instead of copying?
           '$bph_grid  = Grid(xl=$stim_size, yl=$stim_size, dx=1, dy=1)')
           #'print $stim_grid.positions')

# also maintain a matrix of stimulus values for stimulus points to access
s.add_rule('init',
           #'$stim = SinusoidStim($stim_size, $stim_size)', # why two?
           #'$stim = JigglySinusoidStim($stim_size, 10)',
           #'$stim = InvertingSinusoidStim($stim_size, 20)',
           #'$stim = SquareWaveStim($stim_size, 8)',
           #'$stim = BarStim($stim_size, 10)',
           '$stim = FullFieldStim($stim_size, 20)',
           '$stim.step()', 
           '$stim_data = $stim.output')
s.add_rule('update',
           '$stim.step()', 
           '$stim_data = $stim.output')



# add a point of stimulus and change focus
s.add_node('$name = "stim_point"')
s.set_focus('$name == "stim_point"')

# make stim_point read from its associated position in parent's stimulus matrix
s.add_rule('init', 
           '$x, $y = $stim_grid.get_next()',
           'print $x, $y',
           '$init_data($output_length)')
s.add_rule('interact',
           '$temp_data = $stim_data[$x][$y]')
s.add_rule('update',
           #'print "TEMP_DATA: ", $temp_data',
           '$append_data($temp_data)',
           '$clean_data($output_length)')

# make some stim_point copies...should technically make lots more than 10...
#s.set_focus('parent')
# TODO: want to change copy_node so that it takes constraints? 
#s.copy_node(N=99) # for dx,dy = 2,2
s.copy_node(N=399)
#raw_input()



# now add grid of biphasics for every input
s.set_focus('parent')
# note that this is in the "stimulus" layer...
s.add_node('$name = "biphasic"')
s.set_focus('$name == "biphasic"')

# make biphasic read from associated stim_point
s.add_rule('init', 
           '$x, $y = $bph_grid.get_next()',
           '$init_data($output_length)')
# Add a biphasic irf...unity amplitude for now
s.add_rule('init', 
           '$irf = biphasic($kernel_length, 1)')

# use irf to update output vector
s.add_rule('interact',
           '$temp_data = $dot_input()')
s.add_rule('update',
           '$append_data($temp_data)',
           '$clean_data($output_length)') 

# make biphasic read from associated stim_point
s.add_rule('incoming',
           "other.name == 'stim_point'",
           "(other.x, other.y) == ($x, $y)") # if not connecting consider dist
           #"len($get_predecessors()) < 1") # ugly-ish

# and connect to BCM sum if closer than bcm_radius. Should do in sum instead?
s.add_rule('outgoing',
           'other.name == "sum"',
           'other.parent().name == "BCM"',
           'dist((other.x, other.y), ($x, $y)) < $bcm_radius') 

# make some copies
#s.copy_node(N=99) # for 2 spacing
s.copy_node(N=399)



# Add another node to root to act as the Ganglion Cell Module
s.set_focus('parent')
s.set_focus('parent')
s.add_node('$name = "GCM"')
s.set_focus('$name == "GCM"')

# Add a grid-positioning rule for BCMs (grid same size as stimulus)
s.add_rule('init',
           '$x, $y = $stim_size/2., $stim_size/2.',
           '$child_grid = Grid(x0=5, y0=5, dx=5, dy=5, xl=$stim_size, yl=$stim_size)')
           


# Add a node to act as a Bipolar Cell Module
s.add_node('$name = "BCM"')
s.set_focus('$name == "BCM"')

# Grab position from parent
s.add_rule('init',
           '$x, $y = $child_grid.get_next()')



# set up sum
# remember to handle inputs differently...
s.add_node('$name = "sum"')
s.set_focus('$name == "sum"')
s.add_rule('init', '$init_data($output_length)')

# also initialize some stuff for use during update
s.add_rule('init',
           '$bphs   = [p for p in $get_predecessors() if p.name == "biphasic"]',
           '$others = [p for p in $get_predecessors() if p.name != "biphasic"]',
           '$dists  = [dist((p.x, p.y), ($x, $y)) for p in $bphs]',
           '$weights = [DoG_weight(d, $bcm_radius) for d in $dists]')

# get and weight inputs
# TODO: don't need to sum entire vectors every time...
s.add_rule('interact',
           '$bphs_out   = [w*p.get_output() for p,w in zip($bphs, $weights)]',
           '$others_out = [p.get_output() for p in $others]',
           '$temp_data  = sum($bphs_out + $others_out)')

s.add_rule('update',
           '$set_data($temp_data)',
           '$clean_data($output_length)')
           #'print $get_output()')

# want to make connections to thresh
s.add_rule('outgoing',
           'other.name == "thresh"',
           '$parent() == other.parent()') # want to verify shared parents?
# Don't have to worry about getting connections from biphasics - already handled



# set up thresh
s.set_focus('parent')
s.add_node('$name = "thresh"')
s.set_focus('$name == "thresh"')
s.add_rule('init', '$init_data($output_length)')

# threshold input vector
s.add_rule('interact',
           # TODO: This is an ugly way of doing this
           '$temp_data = threshold(verify_single($get_inputs())[0], 0.)')
s.add_rule('update',
           #'print $temp_data',
           '$set_data($temp_data)',
           '$clean_data($output_length)')

# add rule to connect to GCM's sum node
s.add_rule('outgoing',
           'other.name == "sum"',
           'other.parent().name == "GCM"',
           'other.parent() == $parent().parent()')



# go back to BCM to make exponential feedback between thresh and sum units
s.set_focus('parent')
s.add_node('$name = "feedback"')
s.set_focus('$name == "feedback"')
s.add_rule('init', '$init_data($output_length)')

# add exponential IRF
s.add_rule('init',
           '$irf = exponential($kernel_length)')
           
# use irf to update output vector
s.add_rule('interact',
           '$temp_data = $dot_input()')
s.add_rule('update',
           '$append_data($temp_data)',
           '$clean_data($output_length)') 

# get input from thresh
s.add_rule('incoming',
           'other.name == "thresh"',
           '$parent() == other.parent()')

# send output to sum
s.add_rule('outgoing',
           'other.name == "sum"', 
           "$parent() == other.parent()") 



# make some more BCMs
s.set_focus('parent')
s.copy_node(N=8)



# finish out GCM
s.set_focus('parent')

# add sum to GCM
s.add_node('$name = "sum"')
s.set_focus('$name == "sum"')
s.add_rule('init', '$init_data($output_length)')

# also initialize some stuff for use during update
s.add_rule('init',
           '$ths    = [p for p in $get_predecessors() if p.name == "thresh"]',
           '$others = [p for p in $get_predecessors() if p.name != "thresh"]',
           '$dists  = [dist((p.x, p.y), ($x, $y)) for p in $ths]',
           # what max_distance to use?
           '$weights = [DoG_weight(d, 20) for d in $dists]')

# get and weight inputs
# TODO: don't need to sum entire vectors every time...
s.add_rule('interact',
           '$ths_out    = [w*p.get_output() for p,w in zip($ths, $weights)]',
           '$others_out = [p.get_output() for p in $others]',
           '$temp_data  = sum($ths_out + $others_out)')

# On every step, sum inputs, push sum to end of output vector
s.add_rule('update',
           '$set_data($temp_data)',
           '$clean_data($output_length)')

# want to make connections to thresh
s.add_rule('outgoing',
           'other.name == "thresh"',
           '$parent() == other.parent()')



# add thresh to GCM
s.set_focus('parent')
s.add_node('$name = "thresh"')
s.set_focus('$name == "thresh"')
s.add_rule('init', '$init_data($output_length)')

# threshold input vector
s.add_rule('interact',
           # TODO: This is an ugly way of doing this
           '$temp_data = threshold(verify_single($get_inputs())[0], 0.)')
s.add_rule('update',
           #'print $temp_data',
           '$set_data($temp_data)',
           '$clean_data($output_length)')



# add feedback to GCM
s.set_focus('parent')
s.add_node('$name = "feedback"')
s.set_focus('$name == "feedback"')
s.add_rule('init', '$init_data($output_length)')

# add exponential IRF
s.add_rule('init',
           '$irf = exponential($kernel_length)')
           
# use irf to update output vector
s.add_rule('interact',
           '$temp_data = $dot_input()')
s.add_rule('update',
           '$append_data($temp_data)',
           '$clean_data($output_length)') 

# get input from thresh
s.add_rule('incoming',
           'other.name == "thresh"',
           '$parent() == other.parent()')

# send output to sum
s.add_rule('outgoing',
           'other.name == "sum"', 
           "$parent() == other.parent()") 



# Re-initialize entire circuit
# really need to do before and after connection?...
s.init_simulation()

# make connections between necessary populations

# connect stim_points to biphasics
#s.connect(['$name == "stimulus"'], 
#          ['$name == "BCM"']) 
s.connect(['$name == "stim_point"'], 
          ['$name == "biphasic"']) 

# connect biphasics to sums
s.connect(['$name == "biphasic"'], 
          ['$name == "sum"'])

# connect thresh to feedback ..better way of doing both this and next one?
s.connect(['$name == "thresh"'], 
          ['$name == "feedback"'])

# connect feedback to sums
s.connect(['$name == "feedback"'], 
          ['$name == "sum"'])

# connect sums to thresh
s.connect(['$name == "sum"'], 
          ['$name == "thresh"'])

# connect BCM thresh to GCM sum
# TODO: this is maybe where relative names would be nice...
s.connect(['$name == "thresh"'], 
          ['$name == "sum"'])

# Re-initialize entire circuit
s.init_simulation()

#s.focus.show_cg()


# step the network a few times to 'prime' things
prime_steps = 50
for i in range(prime_steps):
    print 'priming:', i+1, '/', prime_steps
    s.step_simulation()




# prepare plotting stuff

s.set_focus('root')
s.set_focus('$name == "stimulus"')
stim = s.focus

s.set_focus('root')


# NOTE: (for convolution) only need extension on one side - because IRF makes 
#       point at only one side
# TODO: biphasic should 'value' recent time more




bcms = s.focus.filter_nodes(C(['$name == "BCM"']))

bcm_sum = list(s.focus.filter_nodes(C(['$name == "sum"',
                                       '$parent().name == "BCM"'])))
bcm_thresh = list(s.focus.filter_nodes(C(['$name == "thresh"',
                                          '$parent().name == "BCM"'])))

gcm_sum = list(s.focus.filter_nodes(C(['$name == "sum"',
                                       '$parent().name == "GCM"'])))[0]
gcm_thresh = list(s.focus.filter_nodes(C(['$name == "thresh"',
                                          '$parent().name == "GCM"'])))[0]


colors = ['green', 'blue', 'yellow', 'red', 'magenta', 'orange', 'beige', 'LimeGreen', 'aqua']

bcm_xs = [b.x for b in bcms]
bcm_ys = [b.y for b in bcms]


plt.ion()
#plt.axis('off')

for i in range(500):
    #plt.ion()
    print 'plotting:', prime_steps+i
    s.step_simulation()
    plt.cla()
    
    plt.subplot2grid((6,5), (0,3), colspan=4, rowspan=4)
    plt.xlim([0,19])
    plt.ylim([0,19])
    plt.axis('off')
    plt.title('Input and node locations')
    plt.imshow(stim.stim_data, cmap='Greys', vmin=-1, vmax=1)
    for i in range(len(bcm_xs)):
        plt.plot(bcm_xs[i], bcm_ys[i], marker='x', markersize=20, 
                 color=colors[i], markeredgewidth=2)    

    # REMEMBER TO COLOR LINES!
    plt.subplot2grid((6,5), (4, 0), colspan=5)
    plt.title('bcm sum')
    for i in range(len(bcm_sum)):      
        plt.plot(bcm_sum[i].get_output(), color=colors[i])
    plt.plot([0]*len(bcm_sum[0].get_output()), color='black')


    plt.subplot2grid((6,5), (5, 0), colspan=5)
    plt.title('gcm sum')
    plt.plot(gcm_sum.get_output())
    plt.plot([0]*len(gcm_sum.get_output()), color='black')


    plt.draw()
    #plt.ioff()
    raw_input()

plt.ioff()


