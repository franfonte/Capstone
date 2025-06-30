En primer lugar en el directorio simulacion/1. codigo analisis contiene todos los archivos que ajustan los datos historicos a distribuciones, generan también las matrices de transición. (analisis_matrices_transición.ipynb, analisis_tasas_llegada_kde_discreto.ipynb, analisis_tiempos_estadia_kde_discreto.ipynb, analisis_tiempos_estadia_OR.ipynb)

Una vez generado el directorio simulacion/1. codigo analisis/resultados incertidumbre este es utilizado al momento de simular.

Para la simulación todo el codigo se encuentra contenido en simulacion/0. codigo simulación donde el archivo mas importantes es clases.py el cual contiene todas las clases del codigo y en especifico los modelos y su logica.

Para correr una simulación se puede hacer uso del archivo simulacion/0. codigo simulación/correr_simulacion.ipynb, donde se modifican los parametros como cantidad de simulaciones, cantidad de ciclos, etc.

Los resultados de las simulaciones se almacenan en simulacion/0. codigo simulación/resultados simulacion dentro del directorio con el nombre del modelo.
