# Requirements
import pandas as pd
import os

#change the working directory
os.chdir(os.path.dirname(__file__))

# import explicit
# Internal Numerical Methods
from src.explicit.numerical_method import numerical_method_explicit
from src.implicit.numerical_method import numerical_method_implicit

# Processing functions
from src.result_processing.stability.stability import *
from src.result_processing.layer_number.layer_number_ import layer_number_f
from src.result_processing.SOC.SOC_df import *
from src.result_processing.SOC.SOC_fun import *
from src.result_processing.SOC.functions import *
from src.result_processing.QUS.iterations import *
from src.result_processing.output_signal.output_signal import *
from src.implicit.graph.graph import graph
from src.implicit.courant import courant

method_switcher = {
    "implicit": numerical_method_implicit,
    "explicit": numerical_method_explicit,
}
# Numerical Methods
main_path = os.path.dirname(__file__)
saving_path = 'src/result_processing/Simulation/Paper/fig 12 propagation lower dt'
url = './src/database/materials_properties.csv'
initial_velocity = 0
df = pd.read_csv(url, dtype=object)

indexes = [10,21] # materials definition discharged

geometry_unit = indexes # Geometry

dt = 5e-5
nodes = 1100

cfl = False
time = 0.5
n_steps = int(time/dt)
layer_number = 256 # The condition is that the half of the number must be an even number
interpolation_points = 5
rescale_t = False
rescale_x = False
name = f'100_dt_{dt}_courant_0'
nodes = method_switcher.get("implicit")(indexes, geometry_unit  ,layer_number, n_steps, dt, initial_velocity, df, name, saving_path, 
                                        main_path, interpolation_points, cfl, nodes, rescale_t, rescale_x, 
                                        rescale_thickness=False, case = False, dimensionless=False, input_plot=False, save=True, 
                                        tol = 1e-10, condition_number = True, asimetric= True)
graphic=True
if graphic:
    fig_steps, low_limit, upper_limit, interval = 1e-2/dt, -1.0, 1.0, 1e-10
    graph(nodes, name, n_steps, 1, saving_path, fig_steps, low_limit, upper_limit, interval, dt)


# QUM
# reading_path = "src/result_processing/QUM/results/"
# tof_iterative_fun(reading_path, dt, n_steps)
# signal_slice_iterative_fun(reading_path, dt)
# windowing_convolve(reading_path)
# fft_iterative_fun(reading_path)
# normalized_spectrums_iterative(reading_path)


# SOC comparison function.
# main_path = os.path.dirname(__file__)
# reading_path = 'src/result_processing/SOC/Dataset'
# saving_path = 'src/result_processing/SOC/SOC_output'
# style = 'seaborn-poster'
# SOC_comparison(reading_path, main_path, cut_imput = 14)
# n = 11
# df, n = df_creation(saving_path)
# plot(df, n, style)


# Heat map 
# iterative_stability_f(indexes, layer_number, n_steps, initial_velocity, amplitude, period, input_time, url, df, nodes_array, dt_array, save=False)
# stability_f(dt_array, n_steps, reading_path, save_path, main_path)
# equal_data_files(n_steps, dt_array, reading_path, save_path)  # Reading is where the stability_f stores the results
# heat_map_f(reading_path, saving_path)

# Layer analysis
# layer_number_f(layers, indexes, nodes, n_steps, dt, time, initial_velocity, amplitude, period, input_time, url, df, name, save=False)

# output-signal -- It works as long as graphic=False: line 47
if graphic == False:
    output  = output_signal(dt, name)
    plt.plot(output[0], output[1])
    plt.xlabel('Time (μs)')
    plt.ylabel('Deformation')
    plt.xlim(0,time)
    plt.title('Output signal: Node 0')
    plt.show()
