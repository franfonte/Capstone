# Librerias necesarias
import os
import json
import random

def generar_pacientes(seed = 42, cantidad_de_ciclos = 5000):
    # Archivos necesarios, cargo los diccionarios de la carpeta "resultados incertidumbre", en orden de uso
    base_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_path, "../1. codigo analisis/resultados incertidumbre/llegadas.json"), "r") as file:
        llegadas = json.load(file)
    with open(os.path.join(base_path, "../1. codigo analisis/resultados incertidumbre/matrices.json"), "r") as file:
        matrices = json.load(file)
    with open(os.path.join(base_path, "../1. codigo analisis/resultados incertidumbre/los.json"), "r") as file:
        los = json.load(file)
    with open(os.path.join(base_path, "../1. codigo analisis/resultados incertidumbre/los_OR.json"), "r") as file:
        los_OR = json.load(file)
    # Funciones utilizadas
    def test_uniforme(uniforme, final_kde_pmf, inicio):
        inicio = inicio
        cumulative_probability = 0
        for index, probability in enumerate(final_kde_pmf):
            cumulative_probability += probability
            if uniforme < cumulative_probability:
                return index + inicio
            elif uniforme == 1:
                return len(final_kde_pmf) - (1 - inicio) # En caso de que el uniforme sea 1, se devuelve el último índice

    def dict_matriz_a_pmf(matriz_dict):
        pmf = [[], [], []]
        for unidad_inicio in range(1,4):
            for unidad_termino in range(1,4):
                pmf[unidad_inicio-1].append(matriz_dict[str(unidad_inicio)][str(unidad_termino)])      
        return pmf

    # Le entrego la matriz con las transiciones posibles, la unidad donde parte y devuelve un camino
    def camino_matriz(matriz, unidad_actual):
        camino = []
        camino.append(unidad_actual)
        termino = False
        while not termino:
            uniforme = random.uniform(0, 1)
            unidad_siguiente = test_uniforme(uniforme, matriz[unidad_actual-1], 1)
            if unidad_siguiente == unidad_actual: # Solo ocurre de SDU_WARD a SDU_WARD
                termino = True
            else:
                camino.append(unidad_siguiente)
                unidad_actual = unidad_siguiente
        return camino

    # Le entrego el camino que siguio cierto paciente y me entrega el tiempo en cada unidad
    def calculo_los(los, los_OR, hospital, grd, camino):
        tiempo_en_camino = []
        pmf_OR = los_OR[str(hospital)][str(grd)]["final_kde_pmf"].copy()
        pmf_ICU = los[str(hospital)]["ICU"][str(grd)]["final_kde_pmf"].copy()
        pmf_SDU = los[str(hospital)]["SDU_WARD"][str(grd)]["final_kde_pmf"].copy()
        pmfs = {
            1: pmf_OR,
            2: pmf_ICU,
            3: pmf_SDU
        }
        for unidad in camino:
            uniforme = random.uniform(0, 1)
            tiempo_en_camino.append(test_uniforme(uniforme, pmfs[unidad], 1))
        
        return tiempo_en_camino
    """Definir semilla para random, muy importante para reproducibilidad de resultados, son 48 sub listas
    de llegadas, ya que del grd 5 al 8 tienen 3 requerimientos, osea 12 sub listas. Del 1 al 4 tienen
    3 requerimientos pero ademas llegan a 3 hospitales diferentes por lo que son 36 sub listas. Esto da
    un total de 48 sub listas. Cada sub lista se crea secuancialmente, se llena una y se pasa a la siguiente. """
    random.seed(seed)

    """En primer se simulan todas las llegadas, ya sea a WL o a los distintos ED
    Se separan por hospital (o WL), requerimiento inicial y grd"""
    llegadas_simuladas = {}
    for hospital in range(0,4): # El cero hace referencia a la WL
        llegadas_simuladas[hospital] = {}
        for requerimiento in range(1, 4):
            llegadas_simuladas[hospital][requerimiento] = {}
            for grd in range(1, 9):
                llegadas_simuladas[hospital][requerimiento][grd] = []
                if llegadas[str(hospital)][str(requerimiento)][str(grd)] != {}: # No considero los vacios de llegadas.json
                    for ciclo in range(1, cantidad_de_ciclos + 1):
                        uniforme = random.uniform(0, 1) # Genero un numero aleatorio entre 0 y 1
                        final_kde_pmf = llegadas[str(hospital)][str(requerimiento)][str(grd)]["final_kde_pmf"] # Accedo a la lista de probabilidades
                        numero_llegadas = test_uniforme(uniforme, final_kde_pmf, inicio = 0) # Parte desde las cero llegadas
                        for persona in range(numero_llegadas):    
                            llegadas_simuladas[hospital][requerimiento][grd].append(ciclo) # Agrego el ciclo al que llega la persona

    """Siguiendo la misma logica anterior, por cada paciente se generan 3 posibles caminos,
    uno por cada hospital, ya que no se sabe en que hospital terminaran siendo
    atendidos (si es que no son enviados al PS)"""
    transiciones_simuladas = {}
    for hospital in range(0,4): # 0 son llegadas a WL
        transiciones_simuladas[hospital] = {}
        for requerimiento in range(1,4):
            transiciones_simuladas[hospital][requerimiento] = {}
            for grd in range(1,9):
                transiciones_simuladas[hospital][requerimiento][grd] = []
                cantidad_pacientes = len(llegadas_simuladas[hospital][requerimiento][grd])
                if cantidad_pacientes != 0:
                    for paciente in range(cantidad_pacientes):
                        matrices_posibles = {
                            1: camino_matriz(dict_matriz_a_pmf(matrices["1"][str(grd)]), requerimiento),
                            2: camino_matriz(dict_matriz_a_pmf(matrices["2"][str(grd)]), requerimiento),
                            3: camino_matriz(dict_matriz_a_pmf(matrices["3"][str(grd)]), requerimiento)
                        }
                        transiciones_simuladas[hospital][requerimiento][grd].append(matrices_posibles)

    """Finalmente teniendo cada uno de los caminos, se calcula el tiempo que se estara en cada una
    de las unidades, de esta manera cada camino de unidades tiene asociado un camino de tiempo"""
    los_simuladas = {}
    for hospital in range(0,4): # 0 son llegadas a WL
        los_simuladas[hospital] = {}
        for requerimiento in range(1,4):
            los_simuladas[hospital][requerimiento] = {}
            for grd in range(1,9):
                los_simuladas[hospital][requerimiento][grd] = []
                cantidad_pacientes = len(llegadas_simuladas[hospital][requerimiento][grd])
                if cantidad_pacientes != 0:
                    for camino_paciente in transiciones_simuladas[hospital][requerimiento][grd]:
                        los_posibles = {
                            1: calculo_los(los, los_OR, 1, grd, camino_paciente[1]),
                            2: calculo_los(los, los_OR, 2, grd, camino_paciente[2]),
                            3: calculo_los(los, los_OR, 3, grd, camino_paciente[3])
                        }
                        los_simuladas[hospital][requerimiento][grd].append(los_posibles)

    """Uno todo por cada uno de los pacientes, de esa manera instanciar a los paciente mas adelante sera
    facil ya que cada uno cuenta con toda la información que se necesita"""
    incertidumbre_pacientes = {}
    for hospital in range(0,4): # 0 son llegadas a WL
        incertidumbre_pacientes[hospital] = {}
        for requerimiento in range(1,4):
            incertidumbre_pacientes[hospital][requerimiento] = {}
            for grd in range(1,9):
                incertidumbre_pacientes[hospital][requerimiento][grd] = []
                cantidad_pacientes = len(llegadas_simuladas[hospital][requerimiento][grd])
                if cantidad_pacientes != 0:
                    l_s = llegadas_simuladas[hospital][requerimiento][grd]
                    t_s = transiciones_simuladas[hospital][requerimiento][grd]
                    lo_s = los_simuladas[hospital][requerimiento][grd]
                    for ti, transicion, espera in zip(l_s, t_s, lo_s):
                        unido = {"TI": ti,
                        "camino": transicion,
                        "espera": espera}
                        incertidumbre_pacientes[hospital][requerimiento][grd].append(unido)

    # Asi se ven los datos para cada paciente
    # incertidumbre_pacientes
    # Guardar el diccionario en un archivo JSON
    def save_dict_as_json(data_dict, filename, folder):
        os.makedirs(folder, exist_ok=True)  # Create folder if it doesn't exist
        path = os.path.join(folder, filename)
        with open(path, 'w') as f:
            json.dump(data_dict, f, indent=4)
        # print(f"Dictionary saved to: {path}") # Esto es lo unico distinto con respecto al original
        print("La incertidumbre de los pacientes ha sido generada y guardada en el archivo JSON.")
    # Save the results to a JSON file
    # Save the results to a JSON file in a folder relative to the script's directory
    output_folder = os.path.join(base_path, "resultados incertidumbre")
    save_dict_as_json(incertidumbre_pacientes, filename="incertidumbre_simulada.json", folder=output_folder)

if __name__ == "__main__":
    # Llamar a la función para generar pacientes
    generar_pacientes(seed=42, cantidad_de_ciclos=5000)