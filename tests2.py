

from rule import Constraint as C, ExecStep as E
import random
#from node import Node
from context import Context
import matplotlib.pyplot as plt
import numpy as np
from utils import DoG_hump

""" NOTES    
"""

# create context
s = Context()

# add stimulus sizes to root node...would be nicer if they went in stimulus node
s.add_rule('init',
           # NOTE: these are one longer than you think - fix?
           '$kernel_length = 10',
           '$output_length = 50',
           '$stim_size  = 20',
           '$p_h_radius = 500.',
           '$p_b_radius = 500.',
           '$h_b_radius = 500.',
           '$b_a_radius = 500.',
           '$b_g_radius = 500.',
           '$a_g_radius = 500.',
           '$stim_grid = Grid(xl=$stim_size, yl=$stim_size, dx=1, dy=1)',
           '$p_grid  = Grid(xl=$stim_size, yl=$stim_size, dx=1, dy=1)',
           '$h_grid  = Grid(xl=$stim_size, yl=$stim_size, dx=1, dy=1)',
           '$b_grid  = Grid(xl=$stim_size, yl=$stim_size, dx=1, dy=1)',
           '$a_grid  = Grid(xl=$stim_size, yl=$stim_size, dx=1, dy=1)',
           '$g_grid  = Grid(xl=$stim_size, yl=$stim_size, dx=1, dy=1)',
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



# add photoreceptors (don't specify connections?)
s.add_node('$name = "p_layer"')
s.set_focus('$name == "p_layer"')
s.add_node('$name = "photoreceptor"')
s.set_focus('$name == "photoreceptor"')

# read from associated position in stimulus matrix
s.add_rule('init', 
           '$x, $y = $stim_grid.get_next()',
           '$init_data($output_length)')
s.add_rule('interact',
           '$temp_data = $stim_data[$x][$y]')
s.add_rule('update',
           '$append_data($temp_data)',
           '$clean_data($output_length)')

# ADD APPROPRIATE IRF!!

s.add_rule('outgoing',
           'other.name == "horizontal"',
           'dist((other.x, other.y), ($x, $y)) < $p_h_radius')
s.add_rule('outgoing',
           'other.name == "bipolar"',
           'dist((other.x, other.y), ($x, $y)) < $p_b_radius')

# make some stim_point copies
s.copy_node(N=5) #399



# add photoreceptors???

# add horizontals
s.set_focus('root')
s.add_node('$name = "h_layer"')
s.set_focus('$name == "h_layer"')
s.add_node('$name = "horizontal"')
s.set_focus('$name == "horizontal"')
h_irf = '$irf = -1*hump($kernel_length, 1,1,.6,1)' # different params?
p_h_weight = '0.5*gauss_weight(std=40, max_d=$p_h_radius, ' #omg
h_ia  = [('photoreceptor', p_h_weight, '$p_h_radius')]
h_c   = [('bipolar', '$h_b_radius')]
s.parse_rule(DoG_hump('$h_grid', h_irf, h_ia, h_c))
s.add_rule('update',
           'print "out:", $get_output()')
s.copy_node(N=5) # 399

# add bipolars
s.set_focus('root')
s.add_node('$name = "b_layer"')
s.set_focus('$name == "b_layer"')
s.add_node('$name = "bipolar"')
s.set_focus('$name == "bipolar"')
b_irf = '$irf = hump($kernel_length, 1,1,.6,1)' # different params?
p_b_weight = '0.5*gauss_weight(std=15, max_d=$p_b_radius, ' #omg
h_b_weight = '0.5*gauss_weight(std=40, max_d=$h_b_radius, ' #omg
b_ia  = [('photoreceptor', p_b_weight, '$p_b_radius'),
         ('horizontal', h_b_weight, '$h_b_radius')]
b_c   = [('amacrine', '$b_a_radius'),
         ('ganglion', '$b_g_radius')]
s.parse_rule(DoG_hump('$b_grid', b_irf, b_ia, b_c))
s.copy_node(N=5)

# add amacrines
s.set_focus('root')
s.add_node('$name = "a_layer"')
s.set_focus('$name == "a_layer"')
s.add_node('$name = "amacrine"')
s.set_focus('$name == "amacrine"')
a_irf = '$irf = -1*hump($kernel_length, 1,1,.6,1)' # different params?
b_a_weight = '0.5*gauss_weight(std=40, max_d=$b_a_radius, ' #omg
a_ia  = [('bipolar', b_a_weight, '$b_a_radius')]
a_c   = [('ganglion', '$a_g_radius')]
s.parse_rule(DoG_hump('$a_grid', a_irf, a_ia, a_c))
s.copy_node(N=5)

# add ganglion
# NOTE: JUST HAVE ONE in center!!
s.set_focus('root')
s.add_node('$name = "g_layer"')
s.set_focus('$name == "g_layer"')
s.add_node('$name = "ganglion"')
s.set_focus('$name == "ganglion"')
g_irf = '$irf = hump($kernel_length, 1,1,.6,1)' # different params?
b_g_weight = '0.5*gauss_weight(std=15, max_d=$b_g_radius, ' #omg
a_g_weight = '0.5*gauss_weight(std=40, max_d=$a_g_radius, ' #omg
g_ia  = [('bipolar', b_g_weight, '$b_g_radius'),
         ('amacrine', a_g_weight, '$a_g_radius')]
g_c   = []
s.parse_rule(DoG_hump('$g_grid', g_irf, g_ia, g_c))
s.copy_node(N=5)






# Re-initialize entire circuit
# really need to do before and after connection?...
s.init_simulation()

# make connections between necessary populations

# connect photoreceptor to horizontal
s.connect(['$name == "photoreceptor"'], 
          ['$name == "horizontal"']) 

# connect photoreceptor to bipolar
s.connect(['$name == "photoreceptor"'], 
          ['$name == "bipolar"']) 

# connect horizontal to bipolar
s.connect(['$name == "horizontal"'], 
          ['$name == "bipolar"']) 

# connect bipolar to amacrine
s.connect(['$name == "bipolar"'], 
          ['$name == "amacrine"']) 

# connect bipolar to ganglion
s.connect(['$name == "bipolar"'], 
          ['$name == "ganglion"']) 

# connect amacrine to ganglion
s.connect(['$name == "amacrine"'], 
          ['$name == "ganglion"']) 

# Re-initialize entire circuit
# need something to reset grids too if doing this...
#s.init_simulation()

#s.focus.show_cg()
#s.focus.show_hg()


# step the network a few times to 'prime' things
prime_steps = 50
for i in range(prime_steps):
    print 'priming:', i+1, '/', prime_steps
    s.step_simulation()


"""

# prepare plotting stuff

s.set_focus('root')
s.set_focus('$name == "stimulus"')
stim = s.focus

s.set_focus('root')



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


"""
