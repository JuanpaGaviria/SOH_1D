import numpy as np

def output_signal(dt, file):

    """
    Take the signal detected where the wave is passing through the boundary at node 0
    """

    H = np.load(f'src/result_processing/Simulation/{file}.npy')
    deformation = []
    times = []

    for i in range(H.shape[1] - 2):

        iter_time = (i * dt)
        times.append(iter_time)

        deformation.append(H[-1, i])
    
    return times, deformation