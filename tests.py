

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
TODO: Appending to numpy arrays is bad, do some other way
"""

# create context
s = Context()

# add stimulus sizes to root node...would be nicer if they went in stimulus node
s.add_rule('init',
           '$kernel_length = 10',
           '$output_length = 50',
           '$bcm_radius = 4',
           '$stim_size  = 20',
           '$time_delay = 5')
# NOTE: these are one longer than you think - fix?



# add a container for stimulus and 'focus' on it
s.add_node('$name = "stimulus"')
s.set_focus('$name == "stimulus"')

# add a distribution rule for stimulus points
s.add_rule('init',
           '$child_grid = Grid(xl=$stim_size, yl=$stim_size, dx=2, dy=2)',
           'print $child_grid.positions')

# also maintain a matrix of stimulus values for stimulus points to access
s.add_rule('init',
           #'$stim = SinusoidStim($stim_size, $stim_size)', # why two?
           '$stim = JigglySinusoidStim($stim_size, 10)',
           #'$stim = InvertingSinusoidStim($stim_size, 5)',
           #'$stim = SquareWaveStim($stim_size, 5)',
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
           '$x, $y = $child_grid.get_next()',
           '$init_data($output_length)')
s.add_rule('interact',
           '$temp_data = $stim_data[$x][$y]')
s.add_rule('update',
           #'print "TEMP_DATA: ", $temp_data',
           '$append_data($temp_data)',
           #'print $data',
           '$clean_data($output_length)')

# make some stim_point copies...should technically make lots more than 10...
#s.set_focus('parent')
# TODO: want to change copy_node so that it takes constraints? 
s.copy_node(N=99)



# Add another node to root to act as the Ganglion Cell Module
s.set_focus('parent')
s.set_focus('parent')
s.add_node('$name = "GCM"')
s.set_focus('$name == "GCM"')

# Add a grid-positioning rule for BCMs (grid same size as stimulus)
s.add_rule('init',
           '$child_grid = Grid(x0=5, y0=5, dx=5, dy=5, xl=$stim_size, yl=$stim_size)')
           


# Add a node to act as a Bipolar Cell Module
s.add_node('$name = "BCM"')
s.set_focus('$name == "BCM"')

# Grab position from parent
s.add_rule('init',
           '$x, $y = $child_grid.get_next()')



# Add a node to act as a biphasic filter
s.add_node('$name = "biphasic"')
s.set_focus('$name == "biphasic"')

# need to change this so positioned on everything...
# Position randomly in a square centered on parent
s.add_rule('init',
           "$x=rand_centered($parent().x, $bcm_radius)",
           "$y=rand_centered($parent().y, $bcm_radius)",
           '$init_data($output_length)')

# Add a biphasic irf with amplitude proportional to distance from parent
s.add_rule('init', 
           '$irf = biphasic($kernel_length, ' + 
           '1./flip_dist(($parent().x, $parent().y), ($x, $y), 3))')
# need to make this negative past a certain threshold...

# use irf to update output vector
s.add_rule('interact',
           '$temp_data = $dot_input()')
s.add_rule('update',
           #'print $temp_data',
           '$append_data($temp_data)',
           '$clean_data($output_length)') 

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

# make some more biphasics
s.copy_node(N=5)



# set up sum
s.set_focus('parent')
s.add_node('$name = "sum"')
s.set_focus('$name == "sum"')
s.add_rule('init', '$init_data($output_length)')

# On every step, sum inputs, push sum to end of output vector
s.add_rule('interact',
           #'print $get_inputs()',
           '$temp_data = sum($get_inputs())')
s.add_rule('update',
           '$set_data($temp_data)',
           '$clean_data($output_length)')

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

# On every step, sum inputs, push sum to end of output vector
s.add_rule('interact',
           #'print $get_inputs()',
           '$temp_data = sum($get_inputs())')
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
s.init_simulation()

# make connections between necessary populations

# connect stim_points to biphasics
s.connect(['$name == "stimulus"'], 
          ['$name == "BCM"']) 

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


#s.focus.show_cg()






# prepare plotting stuff

s.set_focus('root')
s.set_focus('$name == "stimulus"')
stim = s.focus

s.set_focus('root')


# NOTE: (for convolution) only need extension on one side - because IRF makes 
#       point at only one side
# TODO: biphasic should 'value' recent time more




bcms = s.focus.filter_nodes(C(['$name == "BCM"']))
biphasics = [list(s.focus.filter_nodes(C(['$name == "biphasic"',
                                          'id($parent()) == ' + str(id(bcm))])))
             for bcm in bcms]

# select things for easier plotting
chosen_bcm = random.sample(bcms,1)[0]
chosen_biphasics = list(s.focus.filter_nodes(C(['$name == "biphasic"',
                                                'id($parent()) == ' + 
                                                str(id(chosen_bcm))])))

bcm_sum = list(s.focus.filter_nodes(C(['$name == "sum"',
                                       'id($parent()) == ' + 
                                       str(id(chosen_bcm))])))[0]
bcm_thresh = list(s.focus.filter_nodes(C(['$name == "thresh"',
                                          'id($parent()) == ' + 
                                          str(id(chosen_bcm))])))[0]

gcm_sum = list(s.focus.filter_nodes(C(['$name == "sum"',
                                       '$parent().name == "GCM"'])))[0]
gcm_thresh = list(s.focus.filter_nodes(C(['$name == "thresh"',
                                          '$parent().name == "GCM"'])))[0]



colors = ['green', 'blue', 'yellow', 'red', 'magenta', 'orange', 'beige', 'LimeGreen', 'aqua']

bcm_xs = [b.x for b in bcms]
bcm_ys = [b.y for b in bcms]
bph_xs = [[b.x for b in bph] for bph in biphasics]
bph_ys = [[b.y for b in bph] for bph in biphasics]
chosen_xs = [b.x for b in chosen_biphasics]
chosen_ys = [b.y for b in chosen_biphasics]


# step the network a few times to 'prime' things
prime_steps = 150
for i in range(prime_steps):
    print 'priming:', i+1, '/', prime_steps
    s.step_simulation()

# initialize mins/maxes
stim_min = np.min(stim.stim_data)
stim_max = np.max(stim.stim_data)
bph_min = min([min(b.get_output()) for b in chosen_biphasics])
bph_max = max([max(b.get_output()) for b in chosen_biphasics])
bcm_sum_min = min(bcm_sum.get_output())
bcm_sum_max = max(bcm_sum.get_output())
bcm_thresh_min = min(bcm_thresh.get_output())
bcm_thresh_max = max(bcm_thresh.get_output())
gcm_sum_min = min(gcm_sum.get_output())
gcm_sum_max = max(gcm_sum.get_output())
gcm_thresh_min = min(gcm_thresh.get_output())
gcm_thresh_max = max(gcm_thresh.get_output())


print stim_min, stim_max
print bph_min, bph_max


# now step some times to get better mins/maxes
range_steps = 150
for i in range(range_steps):
    print 'ranging:', i+1, '/', range_steps
    s.step_simulation()
    stim_min = min(stim_min, np.min(stim.stim_data))
    stim_max = max(stim_max, np.max(stim.stim_data))
    bph_min = min(bph_min, min([min(b.get_output()) for b in chosen_biphasics]))
    bph_max = max(bph_max, max([max(b.get_output()) for b in chosen_biphasics]))
    bcm_sum_min = min(bcm_sum_min, min(bcm_sum.get_output()))
    bcm_sum_max = max(bcm_sum_max, max(bcm_sum.get_output()))
    bcm_thresh_min = min(bcm_thresh_min, min(bcm_thresh.get_output()))
    bcm_thresh_max = max(bcm_thresh_max, max(bcm_thresh.get_output()))
    gcm_sum_min = min(gcm_sum_min, min(gcm_sum.get_output()))
    gcm_sum_max = max(gcm_sum_max, max(gcm_sum.get_output()))
    gcm_thresh_min = min(gcm_thresh_min, min(gcm_thresh.get_output()))
    gcm_thresh_max = max(gcm_thresh_max, max(gcm_thresh.get_output()))

print stim_min, stim_max
print bph_min, bph_max

plt.ion()
#plt.axis('off')

for i in range(500):
    #plt.ion()
    print 'plotting:', prime_steps+range_steps+i
    s.step_simulation()
    plt.cla()
    
    plt.subplot2grid((11,6), (0,1), colspan=4, rowspan=4)
    plt.xlim([0,19])
    plt.ylim([0,19])
    plt.axis('off')
    plt.title('Input and node locations')
    plt.imshow(stim.stim_data, cmap='Greys', vmin=stim_min, vmax=stim_max)
    for i in range(len(bcm_xs)):
        plt.plot(bcm_xs[i], bcm_ys[i], marker='x', markersize=20, 
                 color=colors[i], markeredgewidth=2)    
    for i,(x,y) in enumerate(zip(bph_xs,bph_ys)):
        plt.plot(x, y, marker='o', linestyle='none', markersize=8, 
                 color=colors[i])

    # highlight chosen biphasics    
    plt.plot(chosen_bcm.x, chosen_bcm.y, marker='x', markersize=20, 
             color='pink', markeredgewidth=2)    
    plt.plot(chosen_xs, chosen_ys, marker='o', markersize=15, 
             color='pink', linestyle='none')    

    for i in range(len(chosen_biphasics)):
        b = chosen_biphasics[i]
        plt.subplot2grid((11,7), (4,i))
        plt.ylim([-1,1])
        plt.title('biphasic irf')
        plt.plot([0]*len(b.irf))
        plt.plot(b.irf)
        plt.subplot2grid((11,7), (5,i))
        plt.axis('off')
        plt.title('biphasic input')
        plt.imshow(np.resize(b.get_sources()[0].get_output(), 
                             (10, len(b.get_output()))), 
                   cmap='Greys', vmin=stim_min, vmax=stim_max)
        plt.subplot2grid((11,7), (6,i))
        plt.axis('off')
        plt.title('biphasic output')
        plt.imshow(np.resize(b.get_output(), (10, len(b.get_output()))), 
                   cmap='Greys', vmin=bph_min, vmax=bph_max)

    plt.subplot2grid((11,7), (7, 0))
    plt.axis('off')
    plt.title('bcm sum')
    plt.imshow(np.resize(bcm_sum.get_output(), 
                         (10, len(bcm_sum.get_output()))), 
               cmap='Greys', vmin=bcm_sum_min, vmax=bcm_sum_max)

    plt.subplot2grid((11,7), (8, 0))
    plt.axis('off')
    plt.title('bcm thresh')
    plt.imshow(np.resize(bcm_thresh.get_output(),
                         (10, len(bcm_thresh.get_output()))),
               cmap='Greys', vmin=bcm_thresh_min, vmax=bcm_thresh_max)


    plt.subplot2grid((11,7), (9, 0))
    plt.axis('off')
    plt.title('gcm sum')
    plt.imshow(np.resize(gcm_sum.get_output(), 
                         (10, len(gcm_sum.get_output()))), 
               cmap='Greys', vmin=gcm_sum_min, vmax=gcm_sum_max)

    plt.subplot2grid((11,7), (10, 0))
    plt.axis('off')
    plt.title('gcm thresh')
    plt.imshow(np.resize(gcm_thresh.get_output(),
                         (10, len(gcm_thresh.get_output()))),
               cmap='Greys', vmin=gcm_thresh_min, vmax=gcm_thresh_max)


    plt.draw()
    #plt.ioff()
    raw_input()

plt.ioff()

