import numpy as np
from .fdm_constructors import input_f
from .fdm_constructors import InputWave_3, InputWave_5  # Traveling wave
# from .fdm_constructors import InputWave_3  # Traveling wave
from .statusbar.statusbar import status_bar

from scipy.sparse.linalg import bicgstab
from scipy.sparse import csc_matrix


def fdm_implicit(interphase_position, nodes, x, n_steps, dt, initial_velocity, battery_map, _e_modulus_dict, _thickness_dict, 
                    gamma_map, phi_map, interpolation_points, plot, rescale_x, rescale_thickness, tol, condition_number,dx,_rho_dict):

    sb = status_bar(n_steps)
    # Matrix definition and vectors
    a = np.zeros((nodes, nodes))
    b = np.zeros(nodes)
    uj0 = np.zeros(nodes)  # Deformation in the present u^j
    uj1 = np.zeros(nodes)  # Deformation in the future u^j+1
    uj_1 = np.zeros(nodes)  # Deformation in the past u^j-1
    h = np.zeros((nodes, n_steps + 1))  # Matrix where the solution is stored after iteration

    interphase_node = []
    for _interphase_position in range(len(interphase_position)):  # compute an integer value for each interphase
        # value = round((round(interphase_position[_interphase_position], 3)) * nodes, 0)
        value = interphase_position[_interphase_position]/dx
        if rescale_x:
            value = int(value/rescale_x)
        value = int(value)
        interphase_node.append(value)

    _y = input_f(dt, plot)

    if interpolation_points == 5:
        for j in range(0, n_steps):  # Implicit Finite Difference Method implementation
            
            condition = True  # Used to know when is the last material
            formulation = InputWave_5()  # Wave that get into the domain

            if j == 0:
                u_left: float = _y[j+1]
                interphase_count = 0
                for node_count in range(0, nodes):
                    if (interphase_node[interphase_count] < interphase_node[-1] + 1) and (condition is True):  # Perform at
                        # all but the last material
                        if node_count == 0:
                            formulation.node_0_dirichlet(u_left)
                            a[node_count, node_count] = formulation.a_i_i
                            b[node_count] = formulation.b

                        if node_count == 1:  # first node
                            gamma = gamma_map[interphase_count]
                            formulation.time_0_node_1_dirichlet(gamma, u_left, initial_velocity, dt, uj0[node_count])
                            a[node_count, (node_count):(node_count+2)] = [formulation.a_i_i, formulation.a_i_i1]
                            b[node_count] = formulation.b

                        if node_count == 2:  # second node
                            phi = phi_map[interphase_count]
                            formulation.time_0_node_2_dirichlet(phi, u_left, initial_velocity, dt, uj0[node_count])
                            a[node_count, (node_count - 1):(node_count + 3)] = [formulation.a_i_i_1, formulation.a_i_i, formulation.a_i_i1, formulation.a_i_i2]
                            b[node_count] = formulation.b

                        if (node_count > 2) and (node_count < interphase_node[interphase_count] - 1) and \
                                (node_count != interphase_node[interphase_count - 1] + 1):  # central nodes
                            phi = phi_map[interphase_count]
                            formulation.time_0_internal_node(phi, initial_velocity, dt, uj0[node_count])
                            a[node_count, (node_count - 2):(node_count + 3)] = [
                                    formulation.a_i_i_2, 
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1, 
                                    formulation.a_i_i2
                                ]
                            b[node_count] = formulation.b

                        if node_count == interphase_node[interphase_count] - 1:  # node that takes the interphase right
                            gamma = gamma_map[interphase_count]
                            formulation.time_0_node__1_interphase(gamma, initial_velocity, dt, uj0[node_count])
                            a[node_count, (node_count - 1):(node_count + 2)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                            b[node_count] = formulation.b

                        if node_count == interphase_node[interphase_count]:  # interphase
                            material_1 = battery_map[interphase_count]
                            e_modulus_1 = _e_modulus_dict[material_1]
                            rho_1 = _rho_dict[material_1]

                            material_2 = battery_map[interphase_count + 1]
                            e_modulus_2 = _e_modulus_dict[material_2]
                            rho_2 = _rho_dict[material_2]

                            formulation.alpha_m(e_modulus_1, e_modulus_2,rho_1,rho_2)
                            alpha = formulation.alpha
                            formulation.time_0_interphase(alpha)
                            a[node_count, (node_count - 2):(node_count + 3)] = [
                                    formulation.a_i_i_2, 
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1, 
                                    formulation.a_i_i2
                                ]
                            b[node_count] = formulation.b
                            interphase_count += 1

                        if node_count == interphase_node[interphase_count - 1] + 1:  # node that takes the interphase left
                            gamma = gamma_map[interphase_count]
                            formulation.time_0_node_1_interphase(gamma, initial_velocity, dt, uj0[node_count])
                            a[node_count, (node_count - 1):(node_count + 2)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                            b[node_count] = formulation.b

                        if interphase_count == len(interphase_node):
                            condition = False
                            interphase_count -= 1

                    else:  # last material
                        if node_count == interphase_node[interphase_count] + 1:  # takes a node at its left interphase
                            gamma = gamma_map[interphase_count+1]
                            formulation.time_0_node_1_interphase(gamma, initial_velocity, dt, uj0[node_count])
                            a[node_count, (node_count - 1):(node_count + 2)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                            b[node_count] = formulation.b

                        if (node_count > interphase_node[-1] + 1) and (node_count < nodes - 2):  # central nodes
                            phi = phi_map[interphase_count+1]
                            formulation.time_0_internal_node(phi, initial_velocity, dt, uj0[node_count])
                            a[node_count, (node_count - 2):(node_count + 3)] = [
                                    formulation.a_i_i_2,
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1,
                                    formulation.a_i_i2
                                ]
                            b[node_count] = formulation.b

                        if node_count == nodes - 2:  # Penultimate node
                            gamma = gamma_map[interphase_count+1]
                            formulation.time_0_penultimate_node(gamma, initial_velocity, dt, uj0[node_count])
                            a[node_count, (node_count - 1):(node_count + 2)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                            b[node_count] = formulation.b

                        if node_count == nodes - 1:  # last node
                            gamma = gamma_map[interphase_count+1]
                            formulation.time_0_last_node()
                            a[node_count, (node_count - 1):(node_count + 1)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i
                                ]
                            b[node_count] = formulation.b

                a_inverse = np.linalg.pinv(a) #Descomentado
                uj1 = np.dot(a_inverse, b) #Descomentado
                #uj1 = bicgstab(csc_matrix(a), b,rtol=tol)[0] #comentado
                h[:, j+1] = uj1[:]
                uj_1 = uj0
                uj0 = uj1

            if j > 0:
                interphase_count = 0
                for node_count in range(0, nodes):
                    if (interphase_node[interphase_count] < interphase_node[-1] + 1) and (condition is True):  # Perform at
                        # all but the last material

                        if node_count == 0:
                            if j < (len(_y)-1):  # Input
                                u_left: float = _y[j+1]
                                formulation.node_0_dirichlet(u_left)
                                a[node_count, node_count] = formulation.a_i_i
                                b[node_count] = formulation.b

                            if j >= (len(_y)):  # Neumann
                                gamma = gamma_map[interphase_count]
                                formulation.node_0_neumann()
                                a[node_count, (node_count):(node_count + 2)] = [
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                                b[node_count] = formulation.b

                        if node_count == 1:

                            if j < (len(_y)-1):  # Input
                                u_left: float = _y[j+1]
                                gamma = gamma_map[interphase_count]
                                formulation.node_1_dirichlet(gamma, uj0[node_count], uj_1[node_count], u_left)
                                a[node_count, (node_count):(node_count + 2)] = [
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                                b[node_count] = formulation.b

                            if j >= (len(_y)):  # Neumann
                                gamma = gamma_map[interphase_count]
                                formulation.node_1_neumann(gamma, uj0[node_count], uj_1[node_count])
                                a[node_count, (node_count-1):(node_count + 2)] = [
                                    formulation.a_i_i_1,
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                                b[node_count] = formulation.b

                        if node_count == 2:

                            if j < (len(_y)-1):  # Input
                                u_left: float = _y[j+1]
                                phi = phi_map[interphase_count]
                                formulation.node_2_dirichlet(phi, uj0[node_count], uj_1[node_count], u_left)
                                a[node_count, (node_count - 1):(node_count + 3)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1,
                                    formulation.a_i_i2
                                ]
                                b[node_count] = formulation.b

                            if j >= (len(_y)):
                                phi = phi_map[interphase_count]
                                formulation.internal_node(phi, uj0[node_count], uj_1[node_count])
                                a[node_count, (node_count - 2):(node_count + 3)] = [
                                    formulation.a_i_i_2,
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1,
                                    formulation.a_i_i2
                                ]
                                b[node_count] = formulation.b

                        if (node_count > 2) and (node_count < interphase_node[interphase_count] - 1) and \
                                (node_count != interphase_node[interphase_count - 1] + 1):  # central nodes
                            phi = phi_map[interphase_count]
                            formulation.internal_node(phi, uj0[node_count], uj_1[node_count])
                            a[node_count, (node_count - 2):(node_count + 3)] = [formulation.a_i_i_2, formulation.a_i_i_1, formulation.a_i_i, formulation.a_i_i1, formulation.a_i_i2]
                            b[node_count] = formulation.b

                        if node_count == interphase_node[interphase_count] - 1:  # node that takes the interface right
                            gamma = gamma_map[interphase_count]
                            formulation.node__1_interphase(gamma, uj0[node_count], uj_1[node_count])
                            a[node_count, (node_count -1):(node_count + 2)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                            b[node_count] = formulation.b

                        if node_count == interphase_node[interphase_count]:  # interface
                            material_1 = battery_map[interphase_count]
                            e_modulus_1 = _e_modulus_dict[material_1]
                            rho_1 = _rho_dict[material_1]

                            material_2 = battery_map[interphase_count + 1]
                            e_modulus_2 = _e_modulus_dict[material_2]
                            rho_2 = _rho_dict[material_2]

                            formulation.alpha_m(e_modulus_1, e_modulus_2,rho_1,rho_2)
                            alpha = formulation.alpha
                            formulation.interphase(alpha)
                            a[node_count, (node_count - 2):(node_count + 3)] = [
                                    formulation.a_i_i_2,
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1,
                                    formulation.a_i_i2
                                ]
                            b[node_count] = formulation.b
                            interphase_count += 1

                        if node_count == interphase_node[interphase_count - 1] + 1:  # node that takes the interphase left
                            gamma = gamma_map[interphase_count]
                            formulation.node_1_interphase(gamma, uj0[node_count], uj_1[node_count])
                            a[node_count, (node_count - 1):(node_count + 2)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                            b[node_count] = formulation.b

                        if interphase_count == len(interphase_node):
                            condition = False
                            interphase_count -= 1

                    else:
                        if node_count == interphase_node[interphase_count] + 1:  # takes a node at its left interphase
                            gamma = gamma_map[interphase_count+1]
                            formulation.node_1_interphase(gamma, uj0[node_count], uj_1[node_count])
                            a[node_count, (node_count - 1):(node_count + 2)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                            b[node_count] = formulation.b

                        if (node_count > interphase_node[-1] + 1) and (node_count < nodes - 2):  # central nodes
                            phi = phi_map[interphase_count+1]
                            formulation.internal_node(phi, uj0[node_count], uj_1[node_count])
                            a[node_count, (node_count - 2):(node_count + 3)] = [
                                    formulation.a_i_i_2,
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1,
                                    formulation.a_i_i2
                                ]
                            b[node_count] = formulation.b

                        if node_count == nodes - 2:
                            phi = phi_map[interphase_count+1]
                            formulation.penultimate_node(gamma, uj0[node_count], uj_1[node_count])
                            a[node_count, (node_count - 1):(node_count + 2)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i, 
                                    formulation.a_i_i1
                                ]
                            b[node_count] = formulation.b

                        if node_count == nodes - 1:
                            gamma = gamma_map[interphase_count+1]
                            formulation.last_node()
                            a[node_count, (node_count - 1):(node_count + 1)] = [
                                    formulation.a_i_i_1, 
                                    formulation.a_i_i
                                ]
                            b[node_count] = formulation.b
                
                
                if j == 1 and condition_number:
                    a_inverse = np.linalg.pinv(a)
                    cond_num = np.linalg.cond(a_inverse)
                    cond_num = np.linalg.cond(a) # No es necesario calcular la inversa
                    print("Condition number: ", cond_num)

                #uj1,trace = bicgstab(csc_matrix(a), b,x0=uj0,rtol=tol) # comentado
                a_inverse = np.linalg.pinv(a) #Descomentado
                uj1 = np.dot(a_inverse, b) #Descomentado
                h[:, j + 1] = uj1[:]
                uj_1 = uj0
                uj0 = uj1
                if j%100 == 0:
                    if np.max(np.abs(uj1)) > 1.0:
                        print(f"WARNING!! Max amplitude: {np.max(np.abs(uj1))} at step {j}")

                #if trace > 0:
                 #   print(f"WARNING!!: bicgstab did not converge at step {j} with {trace} iterations.")

                sb.update(j+1)

    if interpolation_points == 3:
        for j in range(0, n_steps):  # Implicit Finite Difference Method implementation
            
            condition = True  # Used to know when is the last material
            formulation = InputWave_3()  # Wave that get into the domain

            if j == 0:
                u_left: float = _y[j+1]
                interphase_count = 0
                for node_count in range(0, nodes):
                    if (interphase_node[interphase_count] < interphase_node[-1] + 1) and (condition is True):  # Perform at
                        # all but the last material
                        if node_count == 0:
                            formulation.node_0_dirichlet(u_left)
                            a[node_count, node_count] = formulation.a_i_i
                            b[node_count] = formulation.b

                        if node_count == 1:  # first node
                            gamma = gamma_map[interphase_count]
                            formulation.time_0_node_1_dirichlet(gamma, u_left, initial_velocity, dt, uj0[node_count])
                            a[node_count, node_count] = formulation.a_i_i
                            a[node_count, node_count+1] = formulation.a_i_i1
                            b[node_count] = formulation.b

                        if (node_count > 1) and (node_count < interphase_node[interphase_count]):  # central nodes
                            gamma = gamma_map[interphase_count]
                            formulation.time_0_internal_node( gamma, initial_velocity, dt, uj0[node_count])
                            a[node_count, node_count-1] = formulation.a_i_i_1
                            a[node_count, node_count] = formulation.a_i_i
                            a[node_count, node_count+1] = formulation.a_i_i1
                            b[node_count] = formulation.b

                        if node_count == interphase_node[interphase_count]:  # interphase
                            material_1 = battery_map[interphase_count]
                            e_modulus_1 = _e_modulus_dict[material_1]
                            l_1 = _thickness_dict[material_1]
                            material_2 = battery_map[interphase_count + 1]
                            e_modulus_2 = _e_modulus_dict[material_2]
                            l_2 = _thickness_dict[material_2]
                            formulation.alpha_m(e_modulus_1, e_modulus_2, l_1, l_2, rescale_x)
                            alpha = formulation.alpha
                            formulation.time_0_interphase(alpha)
                            a[node_count, node_count - 2] = formulation.a_i_i_2
                            a[node_count, node_count - 1] = formulation.a_i_i_1
                            a[node_count, node_count] = formulation.a_i_i
                            a[node_count, node_count + 1] = formulation.a_i_i1
                            a[node_count, node_count + 2] = formulation.a_i_i2
                            b[node_count] = formulation.b
                            interphase_count += 1

                        if interphase_count == len(interphase_node):
                            condition = False
                            interphase_count -= 1

                    else:  # last material
                        if (node_count >= interphase_node[interphase_count] + 1) and (node_count < nodes - 1):  # takes a node at its left interphase
                            gamma = gamma_map[interphase_count]
                            formulation.time_0_internal_node(gamma, initial_velocity, dt, uj0[node_count])
                            a[node_count, node_count - 1] = formulation.a_i_i_1
                            a[node_count, node_count] = formulation.a_i_i
                            a[node_count, node_count + 1] = formulation.a_i_i1
                            b[node_count] = formulation.b

                        if node_count == nodes - 1:  # last node
                            gamma = gamma_map[interphase_count]
                            formulation.time_0_last_node()
                            a[node_count, node_count - 1] = formulation.a_i_i_1
                            a[node_count, node_count] = formulation.a_i_i
                            b[node_count] = formulation.b

                a_inverse = np.linalg.pinv(a)
                uj1 = np.dot(a_inverse, b)
                h[:, j+1] = uj1[:]
                uj_1 = uj0
                uj0 = uj1

            if j > 0:
                interphase_count = 0
                for node_count in range(0, nodes):
                    if (interphase_node[interphase_count] < interphase_node[-1] + 1) and (condition is True):  # Perform at
                        # all but the last material

                        if node_count == 0:
                            if j < (len(_y)-1):  # Input
                                u_left: float = _y[j+1]
                                formulation.node_0_dirichlet(u_left)
                                a[node_count, node_count] = formulation.a_i_i
                                b[node_count] = formulation.b

                            if j >= (len(_y)):  # Neumann
                                gamma = gamma_map[interphase_count]
                                formulation.node_0_neumann()
                                a[node_count, node_count] = formulation.a_i_i
                                a[node_count, node_count + 1] = formulation.a_i_i1
                                b[node_count] = formulation.b

                        if node_count == 1:

                            if j < (len(_y)-1):  # Input
                                u_left: float = _y[j+1]
                                gamma = gamma_map[interphase_count]
                                formulation.node_1_dirichlet(gamma, uj0[node_count], uj_1[node_count], u_left)
                                a[node_count, node_count] = formulation.a_i_i
                                a[node_count, node_count + 1] = formulation.a_i_i1
                                b[node_count] = formulation.b

                            if j >= (len(_y)):  # Neumann
                                gamma = gamma_map[interphase_count]
                                formulation.internal_node(gamma, uj0[node_count], uj_1[node_count])
                                a[node_count, node_count - 1] = formulation.a_i_i_1
                                a[node_count, node_count] = formulation.a_i_i
                                a[node_count, node_count + 1] = formulation.a_i_i1
                                b[node_count] = formulation.b

                        if (node_count > 1) and (node_count < interphase_node[interphase_count]):  # central nodes
                            formulation.internal_node(gamma, uj0[node_count], uj_1[node_count])
                            a[node_count, node_count - 1] = formulation.a_i_i_1
                            a[node_count, node_count] = formulation.a_i_i
                            a[node_count, node_count + 1] = formulation.a_i_i1
                            b[node_count] = formulation.b    

                        if node_count == interphase_node[interphase_count]:  # interface
                            material_1 = battery_map[interphase_count]
                            e_modulus_1 = _e_modulus_dict[material_1]
                            material_2 = battery_map[interphase_count + 1]
                            e_modulus_2 = _e_modulus_dict[material_2]
                            formulation.alpha_m(e_modulus_1, e_modulus_2)
                            alpha = formulation.alpha
                            formulation.interphase(alpha)
                            a[node_count, node_count - 2] = formulation.a_i_i_2
                            a[node_count, node_count - 1] = formulation.a_i_i_1
                            a[node_count, node_count] = formulation.a_i_i
                            a[node_count, node_count + 1] = formulation.a_i_i1
                            a[node_count, node_count + 2] = formulation.a_i_i2
                            b[node_count] = formulation.b
                            interphase_count += 1

                        if interphase_count == len(interphase_node):
                            condition = False
                            interphase_count -= 1

                    else:
                        if (node_count >= interphase_node[interphase_count] + 1) and (node_count < nodes - 1):  # takes a node at its left interphase
                            gamma = gamma_map[interphase_count]
                            formulation.internal_node(gamma, uj0[node_count], uj_1[node_count])
                            a[node_count, node_count - 1] = formulation.a_i_i_1
                            a[node_count, node_count] = formulation.a_i_i
                            a[node_count, node_count + 1] = formulation.a_i_i1
                            b[node_count] = formulation.b

                        if node_count == nodes - 1:  # last node
                            gamma = gamma_map[interphase_count]
                            formulation.last_node()
                            a[node_count, node_count - 1] = formulation.a_i_i_1
                            a[node_count, node_count] = formulation.a_i_i
                            b[node_count] = formulation.b

                #  uj1 = np.linalg.solve(a, b)
                a_inverse = np.linalg.pinv(a)
                if j == 1:
                    cond_num = np.linalg.cond(a_inverse)
                    print("condition number is", cond_num)                
                uj1 = np.dot(a_inverse, b)
                h[:, j + 1] = uj1[:]
                uj_1 = uj0
                uj0 = uj1

                sb.update(j+1)

    
    return h
