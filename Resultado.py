import numpy as np
import os
import matplotlib.pyplot as plt

url = './src/result_processing/Simulation'

datos = []
mayores = []
time = []

for i, archivo in enumerate(os.listdir(url)):
    ruta = os.path.join(url, archivo)

    if os.path.isfile(ruta) and archivo.endswith('160.npy') and archivo.startswith('steps_70000_nodes_1200'):
        data = np.load(ruta)
        ultimo_nodo=data[-1,30000:40000]
        valor = ultimo_nodo.max()
        mayores.append(ultimo_nodo.max())
        pos = np.where(ultimo_nodo == valor)
        datos.append(ultimo_nodo)
        time.append(pos)

print(time)

for columna in datos:
    plt.plot(columna)

plt.title('valores del ultimo nodo')
plt.xlabel('nodo')
plt.ylabel('amplitude')
plt.legend(title='estado de carga')
plt.show()
