# -*- coding: utf-8 -*-
"""
Created on Mon Apr  4 10:19:04 2022

@author: EQ01
"""

import pandas as pd
from matplotlib import pyplot as plt, animation
import numpy as np
import os


def graph(nodes, file, n_steps, dimensionless_length, path, fig_steps, low_limit, upper_limit, interval,dt):
    os.chdir(path)
    h = np.load(file + '.npy')
    x = np.linspace(0, dimensionless_length, nodes)

    fig, ax = plt.subplots()
    line = ax.plot(x, h[:, -1], label='Time: 0')[0]
    legend = plt.legend(loc='upper right')
    def animate(i):
        line.set_ydata(h[:, i])
        label = f't = {i*dt:.2f} µs'
        legend.get_texts()[0].set_text(label)
    anim = animation.FuncAnimation(fig, animate, frames=range(0,n_steps,int(fig_steps)), interval=interval)
    plt.ylim(low_limit, upper_limit)
    plt.xlabel('x')
    plt.ylabel('Deformation')
    plt.grid()
    #save animation
    anim.save(f'{file}.gif', fps=60)
    print(f'Saved animation: wave_implicit{file}.gif')
