# Librerias necesarias
import os
import sys
import json
import time
import pandas as pd
from copy import deepcopy
from generacion_pacientes import generar_pacientes
from collections import deque
# Add the parent directory to sys.path to allow relative imports
sys.path.append(os.path.abspath(os.path.join('..', '1. codigo analisis')))
import parametros as p
from kpis import * # Mala practica pero facil

class Paciente: # Revisado, funciona bien
    CONTADOR_ID = 1  # Variable de clase para contar el número de Pacientes creados

    def __init__(self, hospital_llegada, requerimiento_inicial, grd, datos_incertidumbre):
        # Atributos del paciente al llegar, no cambian
        self.id = Paciente.CONTADOR_ID  # Asigna un ID único al Paciente
        self.hospital_llegada = hospital_llegada
        self.requerimiento_inicial = requerimiento_inicial
        self.grd = grd
        self.ti_inicial = datos_incertidumbre["TI"]
        self.datos_incertidumbre = datos_incertidumbre
        self.camino = deepcopy(datos_incertidumbre["camino"])
        self.espera = deepcopy(datos_incertidumbre["espera"])
        if datos_incertidumbre.get("decisiones") is not None: # Revisar esto nuevo
            self.decisiones = deepcopy(datos_incertidumbre["decisiones"])
            self.id = datos_incertidumbre["id"]  # Asigna el ID del paciente a partir de las decisiones
                
        else:
            self.decisiones = None
        Paciente.CONTADOR_ID += 1  # Incrementa el contador de Pacientes

        # Diccionarios parametros unidades y hospitales inverso (para simplificar el acceso)
        self.dict_hospitales = self.invertir_dict(p.dict_hospitales)
        self.dict_unidades = self.invertir_dict(p.dict_unidades)

        # Atributos que cambian a lo largo de la simulación
        self.log_eventos = []
        self.ti_evento_actual = datos_incertidumbre["TI"]
        self.tiempo_actual = datos_incertidumbre["TI"]
        self.tiempo_ultima_evolucion = 0
        self.hospital_actual = hospital_llegada
        self.unidad_actual = self.unidad_llegada()
        self.unidad_requerida = self.requerimiento_inicial
        self.esperando = True # True si esta esperando y no siendo tratado (revisar en cada ciclo)
        self.costo_social = 0
        self.costos_operativos = 0
        
    # Necesarias para cuando se crean los pacientes
    def invertir_dict(self, diccionario): # Revisado, funciona bien
        invertido = {v: k for k, v in diccionario.items()}
        return invertido
    
    def unidad_llegada(self): # Revisado, funciona bien 
        if self.hospital_llegada == 0:
            unidad_actual = p.dict_unidades["WL"]
        else:
            unidad_actual = p.dict_unidades["ED"]
        return unidad_actual
    
    # Necesarias durante la simulación
    # Guarda los eventos que le ocurren al paciente en el log_eventos
    def agregar_log_evento(self): # Revisado, funciona bien

        if self.hospital_actual == 0 and self.unidad_actual == p.dict_unidades["WL"]:
            hospital = "WL"
        elif self.unidad_actual == p.dict_unidades["PS"]:
            hospital = "PS"
        else:
            hospital = self.dict_hospitales[self.hospital_actual]

        if self.tiempo_ultima_evolucion == 0:
            tiempo_final = self.tiempo_actual
        elif self.tiempo_ultima_evolucion != 0:
            tiempo_final = self.ti_evento_actual + self.tiempo_ultima_evolucion
        
        unidad = self.dict_unidades[self.unidad_actual]
        if unidad == "SDU/WARD":
            unidad = "SDU_WARD"

        new_row = {
            'ID': self.id,
            'MS_GRD': self.grd,
            'UBICACIÓN': hospital + "_" + unidad,
            'TI': self.ti_evento_actual,
            'TF': tiempo_final,
            'HOSPITAL': hospital,
            'UNIDAD': unidad
        }
        self.log_eventos.append(new_row)
    
    # Metodos para calcular los distintos costos en los que incurre el paciente (social y operativo)
    def costo_espera(self, tiempo_espera = 1, agregar = False): # Revisado, funciona bien
        if self.unidad_actual == p.dict_unidades["WL"]: 
            costo = p.dict_costo_espera_wl[self.grd][self.requerimiento_inicial] * tiempo_espera
        elif self.unidad_actual == p.dict_unidades["GA"]: 
            costo = p.dict_costo_espera_ga[self.hospital_actual][self.grd][self.requerimiento_inicial] * tiempo_espera
        elif self.unidad_actual == p.dict_unidades["ED"]: 
            costo = p.dict_costo_espera_ed[self.hospital_actual][self.grd][self.requerimiento_inicial] * tiempo_espera
        elif self.unidad_actual in (p.dict_unidades["OR"], p.dict_unidades["ICU"], p.dict_unidades["SDU/WARD"]): # (1, 2, 3)
            costo = p.dict_costo_espera_hospitalizado[self.hospital_actual][self.grd][self.unidad_actual][self.unidad_requerida] * tiempo_espera
        else:
            costo = 0
        if agregar:
            self.costo_social += costo
        return costo

    def costo_traslado(self, hospital_destino, agregar = False): # Revisado, funciona bien
        costo = p.dict_costo_traslado[self.hospital_actual][hospital_destino][self.grd][self.requerimiento_inicial]
        if agregar:
            self.costos_operativos += costo
        return costo
    
    def costo_desvio(self, agregar = False): # Revisado, funciona bien
        if self.unidad_actual == p.dict_unidades["ED"]:
            costo = p.dict_costo_derivar_ed[self.hospital_actual][self.grd][self.requerimiento_inicial]
        elif self.unidad_actual == p.dict_unidades["WL"]: 
            costo = p.dict_costo_derivar_wl[self.grd][self.requerimiento_inicial]
        if agregar:
            self.costos_operativos += costo
        return costo

    # Metodo para cambio de unidad o PS, creo el log correspondiente antes de cambiar la unidad
    def cambiar_unidad(self, hospital: int, id_unidad: int): # Revisado, funciona bien
        # Agrego el evento al log
        # Esto toma como TF el tiempo actual que es el TI de la unidad destino
        self.agregar_log_evento()

        # Antes de cambiar cualquier valor, veo si hubieron gastos operativos
        if id_unidad == p.dict_unidades["PS"]:
            self.costo_desvio(agregar = True)
        elif self.unidad_actual == p.dict_unidades["ED"] and self.hospital_actual != hospital and id_unidad == p.dict_unidades["ED"]:
            self.costo_traslado(hospital, agregar = True)

        # Actualizo todo lo necesario para el cambio de unidad
        # Actualizo el tiempo de evento actual, osea el TI en la nueva unidad
        self.ti_evento_actual = self.tiempo_actual
        # Actualizo el hospital actual
        self.hospital_actual = hospital
        # Actualizo la unidad actual
        self.unidad_actual = id_unidad
        # Caso de termino de la simulacion
        if self.unidad_actual == p.dict_unidades["PS"]:
            self.agregar_log_evento()
        # Corroborar si el cambio modifico el estado de espera o tratamiento
        self.espera_o_tratamiento()

    # Actualizar el tiempo implica si o si que el paciente estuvo un ciclo mas en la unidad actual
    # Nunca se debera actualizar el tiempo si ya esta en PS o END
    # Nunca se debera actualizar el tiempo si su unidad requerida es END
    def actualizar_tiempo(self): # Revisado, funciona bien
        self.tiempo_actual += 1
        if self.esperando:
            self.costo_espera(agregar = True)
        self.espera_o_tratamiento()
    
    # Ve estado actual, requerimiento y modifica esperando acordemente, tambien modifica unidad_requerida
    def espera_o_tratamiento(self): # Revisado, funciona bien
        if self.unidad_actual  in (p.dict_unidades["OR"], p.dict_unidades["ICU"], p.dict_unidades["SDU/WARD"]):
            if self.unidad_requerida == self.unidad_actual:
                tiempo_siendo_atendido = self.tiempo_actual - self.ti_evento_actual
                if tiempo_siendo_atendido <  self.espera[self.hospital_actual][0]:
                    self.esperando = False
                elif tiempo_siendo_atendido ==  self.espera[self.hospital_actual][0]:
                    self.esperando = True

                    # Elimino la unidad anteriormente requerida y su tiempo de evolucion (este lo guardo)
                    self.camino[self.hospital_actual].pop(0)
                    self.tiempo_ultima_evolucion = self.espera[self.hospital_actual].pop(0)
                    if len(self.camino[self.hospital_actual]) > 0:
                        self.unidad_requerida = self.camino[self.hospital_actual][0]
                    # Si no hay mas unidades en la lista, el paciente es dado de alta, requiere END que es salir
                    else:
                        self.unidad_requerida = p.dict_unidades["END"]
            else:
                self.esperando = True
        elif self.unidad_actual  in (p.dict_unidades["WL"], p.dict_unidades["GA"], p.dict_unidades["ED"]):
            self.esperando = True
        else: # Para PS y END, nunca deberia ser llamada esta funcion desde esas unidades
            pass

    def __str__(self): # Revisado, funciona bien
        if self.hospital_actual == 0 and self.unidad_actual == p.dict_unidades["WL"]:
            hospital = "WL"
        elif self.unidad_actual == p.dict_unidades["PS"]:
            hospital = "PS"
        else:
            hospital = self.dict_hospitales[self.hospital_actual]
        return f"Paciente {self.id} | Requerimiento: {self.dict_unidades[self.unidad_requerida]} | GRD: {self.grd} | {hospital} | Unidad: {self.dict_unidades[self.unidad_actual]} | Social: {self.costo_social} y Operativo: {self.costos_operativos} | Tiempo actual: {self.tiempo_actual}"

class WL: # Revisado, funciona bien
    """Funciona con varias sublistas, una por cada combinacion de requerimiento y grd,
    al usar deques las operaciones de append y popleft son O(1), lo cual lo hace mas eficiente
    al ser un sistema de colas FIFO"""
    def __init__(self, requerimientos: list, grds: list):
        self.sub_listas = {}
        self.costo_acumulado_sub_listas = {}
        self.crear_sublistas(requerimientos, grds)
    
    def crear_sublistas(self, requerimientos: list, grds: list): # Revisado, funciona bien
        for requerimiento in requerimientos:
            self.sub_listas[requerimiento] = {}
            self.costo_acumulado_sub_listas[requerimiento] = {}
            for grd in grds:
                self.sub_listas[requerimiento][grd] = deque()
                self.costo_acumulado_sub_listas[requerimiento][grd] = 0
    
    def agregar_paciente(self, paciente: Paciente): # Revisado, funciona bien
        self.sub_listas[paciente.requerimiento_inicial][paciente.grd].append(paciente)
    
    def sacar_paciente(self, paciente): # Revisado, funciona bien
        requerimiento = paciente.requerimiento_inicial
        grd = paciente.grd
        if paciente in self.sub_listas[requerimiento][grd]:
            self.sub_listas[requerimiento][grd].remove(paciente)
            return paciente
        else:
            return None
        
    def actualizar_tiempo(self): # Revisado, funciona bien
        # Llama al método actualizar_tiempo de cada paciente de cada sublista
        for requerimiento in self.sub_listas:
            for grd in self.sub_listas[requerimiento]:
                if self.sub_listas[requerimiento][grd]:
                    for paciente in self.sub_listas[requerimiento][grd]:
                        paciente.actualizar_tiempo()
        self.acumular_costo_ciclo()      
    
    def acumular_costo_ciclo(self): # Revisado, funciona bien
        for requerimiento in self.sub_listas:
            for grd in self.sub_listas[requerimiento]:
                if self.sub_listas[requerimiento][grd]:
                    for paciente in self.sub_listas[requerimiento][grd]:
                        self.costo_acumulado_sub_listas[requerimiento][grd] += paciente.costo_espera()
                else:
                    self.costo_acumulado_sub_listas[requerimiento][grd] += 0

    def __str__(self):
        texto = "Sublistas de WL:"
        for requerimiento in self.sub_listas:
            texto += f"\nRequerimiento {requerimiento}:"
            for grd in self.sub_listas[requerimiento]:
                texto += f"\nGRD {grd}: {len(self.sub_listas[requerimiento][grd])} pacientes"
                if self.sub_listas[requerimiento][grd]:
                    texto += f" | ID Primer paciente: {self.sub_listas[requerimiento][grd][0].id}"
                else:
                    texto += " | Sin pacientes"
        
        texto += "\n\nCostos acumulados de WL:"
        for requerimiento in self.costo_acumulado_sub_listas:
            texto += f"\nRequerimiento {requerimiento}:"
            for grd in self.costo_acumulado_sub_listas[requerimiento]:
                texto += f"\nGRD {grd}: {self.costo_acumulado_sub_listas[requerimiento][grd]} pesos"
        
        return texto

class PS: # Revisado, funciona bien
    """Funciona con varias sublistas, una por cada combinacion de requerimiento y grd,
    funciona simplemente como un sumidero de pacientes"""
    def __init__(self, requerimientos: list, grds: list):
        self.id_unidad = p.dict_unidades["PS"]
        self.sub_listas = {}
        self.costo_acumulado_sub_listas = {}
        self.crear_sublistas(requerimientos, grds)
    
    def crear_sublistas(self, requerimientos: list, grds: list): # Revisado, funciona bien
        for requerimiento in requerimientos:
            self.sub_listas[requerimiento] = {}
            self.costo_acumulado_sub_listas[requerimiento] = {}
            for grd in grds:
                self.sub_listas[requerimiento][grd] = deque()
                self.costo_acumulado_sub_listas[requerimiento][grd] = 0
    
    def agregar_paciente(self, paciente: Paciente): # Revisado, funciona bien
        self.sub_listas[paciente.requerimiento_inicial][paciente.grd].append(paciente)
        self.costo_acumulado_sub_listas[paciente.requerimiento_inicial][paciente.grd] += paciente.costo_desvio()
        paciente.cambiar_unidad(paciente.hospital_actual, self.id_unidad)

    def __str__(self):
        texto = "Sublistas de PS:"
        for requerimiento in self.sub_listas:
            texto += f"\nRequerimiento {requerimiento}:"
            for grd in self.sub_listas[requerimiento]:
                texto += f"\nGRD {grd}: {len(self.sub_listas[requerimiento][grd])} pacientes"
                if self.sub_listas[requerimiento][grd]:
                    texto += f" | {self.sub_listas[requerimiento][grd][0].id}"
                else:
                    texto += " | 0 pacientes"
        texto += "\n\nCostos acumulados de PS:"
        for requerimiento in self.costo_acumulado_sub_listas:
            texto += f"\nRequerimiento {requerimiento}:"
            for grd in self.costo_acumulado_sub_listas[requerimiento]:
                texto += f"\nGRD {grd}: {self.costo_acumulado_sub_listas[requerimiento][grd]} pesos"
                if self.costo_acumulado_sub_listas[requerimiento][grd]:
                    texto += f" | {self.sub_listas[requerimiento][grd][0].id}"
                else:
                    texto += " | 0 pacientes"
        return texto

class END: # Revisado, funciona bien
    """
    Funciona con varias sublistas, una por cada combinación de requerimiento y grd,
    almacena pacientes terminados.
    """
    def __init__(self, requerimientos: list, grds: list):
        self.id_unidad = p.dict_unidades["END"]
        self.sub_listas = {}
        self.crear_sublistas(requerimientos, grds)

    def crear_sublistas(self, requerimientos: list, grds: list): # Revisado, funciona bien
        for requerimiento in requerimientos:
            self.sub_listas[requerimiento] = {}
            for grd in grds:
                self.sub_listas[requerimiento][grd] = deque()

    def agregar_paciente(self, paciente: Paciente): # Revisado, funciona bien
        """
        Agrega un paciente a la sublista correspondiente según su requerimiento_inicial y grd.
        """
        self.sub_listas[paciente.requerimiento_inicial][paciente.grd].append(paciente)
        paciente.cambiar_unidad(paciente.hospital_actual, self.id_unidad)

    def __str__(self):
        lines = ["Sublistas de Termino:"]
        for req, dict_grd in self.sub_listas.items():
            for grd, dq in dict_grd.items():
                lines.append(f"  - Requerimiento {req} GRD {grd}: {len(dq)} pacientes")
        return "\n".join(lines)

class Unidad: # Revisado, funciona bien
    """Clase para las unidades, se usan listas para almacenar pacientes debido a su pequeño tamaño, 
    en el peor de los casos el SDU/WARD tiene 165 pacientes, por lo que una lista es suficiente y
    es facil de iterar sobre ella. Todas las unidades de los hospitales heredan de la clase Unidad, 
    se comportan exactamente igual solo varia el id de la unidad y la capacidad, que se obtiene del 
    diccionario de capacidades"""
    def __init__(self, id_unidad, hospital, capacidad):
        self.id_unidad = id_unidad
        self.hospital = hospital
        self.capacidad = capacidad
        self.pacientes = []

    @property # Revisado, funciona bien
    def ocupacion(self):
        return len(self.pacientes)
    
    @property # Revisado, funciona bien
    def ocupacion_porcentual(self):
        return len(self.pacientes)/self.capacidad
    
    def agregar_paciente(self, paciente: Paciente): # Revisado, funciona bien
        # Si el paciente es None, no se agrega, osea que no estaba donde se queria sacar
        if paciente:
            if self.ocupacion < self.capacidad and paciente not in self.pacientes:
                # Si el paciente ya esta en la lista, no se agrega
                # Si la ocupacion es menor a la capacidad, se agrega el paciente
                self.pacientes.append(paciente)
                # Al agregar el paciente, se actualiza su unidad actual con el metodo de la clase
                paciente.cambiar_unidad(self.hospital, self.id_unidad)
                return True
            else:
                return False
        else:
            return False
        
    def sacar_paciente(self, paciente): # Revisado, funciona bien
        if self.ocupacion > 0 and paciente in self.pacientes:
            # Si el paciente no esta en la lista, no se saca
            # Si la ocupacion es mayor a 0, se saca el paciente
            # Cada instancia de paciente es unica, por lo que no hay problema al usar remove
            self.pacientes.remove(paciente) 
            return paciente
        else:
            return None
    
    def actualizar_tiempo(self): # Revisado, funciona bien
        # Llama al método actualizar_tiempo de cada paciente de la unidad
        for paciente in self.pacientes:
            paciente.actualizar_tiempo()
    
    def __str__(self):
        # Diccionario invertido para obtener el nombre de la unidad
        unit_names = {
            p.dict_unidades["OR"]: "OR",
            p.dict_unidades["ICU"]: "ICU",
            p.dict_unidades["SDU/WARD"]: "SDU/WARD",
            p.dict_unidades["GA"]: "GA",
            p.dict_unidades["ED"]: "ED"
        }
        unit_name = unit_names.get(self.id_unidad, f"Unidad {self.id_unidad}")
        description = f"{unit_name} (Hospital {self.hospital}): {self.ocupacion}/{self.capacidad} pacientes"
        if self.pacientes:
            description += f"\nPacientes: {len(self.pacientes)}, {self.ocupacion_porcentual:.2%} ocupación"
            if len(self.pacientes) <= 20:  # Only show details for a small number of patients
                for i, paciente in enumerate(self.pacientes):
                    description += f"\n  {i+1}. Paciente ID {paciente.id}, GRD {paciente.grd}"
        return description

class Or(Unidad): # Revisado, funciona bien
    def __init__(self, hospital):
        id_unidad = p.dict_unidades["OR"]
        capacidad = p.dict_capacidades[hospital][id_unidad]
        super().__init__(id_unidad, hospital, capacidad)

class Icu(Unidad): # Revisado, funciona bien
    def __init__(self, hospital):
        id_unidad = p.dict_unidades["ICU"]
        capacidad = p.dict_capacidades[hospital][id_unidad]
        super().__init__(id_unidad, hospital, capacidad)

class SduWard(Unidad): # Revisado, funciona bien
    def __init__(self, hospital):
        id_unidad = p.dict_unidades["SDU/WARD"]
        capacidad = p.dict_capacidades[hospital][id_unidad]
        super().__init__(id_unidad, hospital, capacidad)

"""Se redefine el metodo para que no considere la capacidad maxima de la unidad, solo para ED y GA.
El modelo tomador de decisiones te tiene que encargar que esta no sea sobrepasada despues de todas
las decisiones de cada ciclo"""

class Ga(Unidad): # Revisado, funciona bien
    def __init__(self, hospital):
        id_unidad = p.dict_unidades["GA"]
        capacidad = p.dict_capacidades[hospital][id_unidad]
        super().__init__(id_unidad, hospital, capacidad)
    
    def agregar_paciente(self, paciente: Paciente): # Revisado, funciona bien
        # Si el paciente es None, no se agrega, osea que no estaba donde se queria sacar
        if paciente:
            if paciente not in self.pacientes:
                # Si el paciente ya esta en la lista, no se agrega
                # Si la ocupacion es menor a la capacidad, se agrega el paciente
                self.pacientes.append(paciente)
                # Al agregar el paciente, se actualiza su unidad actual con el metodo de la clase
                paciente.cambiar_unidad(self.hospital, self.id_unidad)
                return True
            else:
                return False
        else:
            return False

class Ed(Unidad): # Revisado, funciona bien
    def __init__(self, hospital):
        id_unidad = p.dict_unidades["ED"]
        capacidad = p.dict_capacidades[hospital][id_unidad]
        super().__init__(id_unidad, hospital, capacidad)
    
    # Se redefine el metodo para que no considere la ocupacion de la unidad, solo para ED
    def agregar_paciente(self, paciente: Paciente): # Revisado, funciona bien
        # Si el paciente es None, no se agrega, osea que no estaba donde se queria sacar
        if paciente:
            if paciente not in self.pacientes:
                # Si el paciente ya esta en la lista, no se agrega
                # Si la ocupacion es menor a la capacidad, se agrega el paciente
                self.pacientes.append(paciente)
                # Al agregar el paciente, se actualiza su unidad actual con el metodo de la clase
                # El log se hace cuando se sale de la unidad, por eso cuando entra por primera vez no se agrega, no se
                # cambia de unidad sino que parte en la unidad, revisado con el log
                if not paciente.hospital_actual == self.hospital and paciente.unidad_actual == self.id_unidad:
                    paciente.cambiar_unidad(self.hospital, self.id_unidad)
                return True
            else:
                return False
        else:
            return False

class Hospital: # Revisado, funciona bien
    """Representa un hospital con una instancia de cada unidad disponible."""
    def __init__(self, hospital_id):
        self.hospital = hospital_id
        # Instanciar una unidad de cada tipo
        self.OR = Or(hospital_id)
        self.ICU = Icu(hospital_id)
        self.SDU_WARD = SduWard(hospital_id)
        self.GA = Ga(hospital_id)
        self.ED = Ed(hospital_id)
        # Diccionario para acceso y recorridos
        self.unidades = {
            p.dict_unidades["OR"]: self.OR,
            p.dict_unidades["ICU"]: self.ICU,
            p.dict_unidades["SDU/WARD"]: self.SDU_WARD,
            p.dict_unidades["GA"]: self.GA,
            p.dict_unidades["ED"]: self.ED,
        }

    def actualizar_tiempo(self): # Revisado, funciona bien
        # Llama al método actualizar_tiempo de cada unidad del hospital
        for unidad in self.unidades.values():
            unidad.actualizar_tiempo()
    
    def ocupacion(self): # Revisado, funciona bien (nunca la use creo)
        # Devuelve la ocupación de todo el hospital
        ocupacion = {
            unidad_id: {"ocupacion": unidad.ocupacion, "capacidad": unidad.capacidad, "porcentual": unidad.ocupacion_porcentual,}
            for unidad_id, unidad in self.unidades.items()
        }
        return ocupacion
    
    
    def agregar_paciente(self, paciente: Paciente, unidad: int): # Revisado, funciona bien
        # Agrega un paciente a la unidad correspondiente.
        if unidad in self.unidades:
            return self.unidades[unidad].agregar_paciente(paciente)
        else:
            raise ValueError(f"Unidad {unidad} no válida en el hospital {self.hospital}.")
    
    def sacar_paciente(self, paciente: Paciente, unidad: int): # Revisado, funciona bien
        # Saca un paciente de la unidad correspondiente.
        if unidad in self.unidades:
            return self.unidades[unidad].sacar_paciente(paciente)
        else:
            raise ValueError(f"Unidad {unidad} no válida en el hospital {self.hospital}.")
    
    def __str__(self):
        lines = [f"Hospital {self.hospital}:"]
        for unidad_id, unidad in self.unidades.items():
            lines.append(f"  - {unidad_id}: {unidad.ocupacion}/{unidad.capacidad}")
        return "\n".join(lines)

class ModeloBase:

    def __init__(self):
        self.decisiones = [{}, {}, {}, {}]
        self.ciclo = 1
        
    def cargar_decisiones(self, simulacion):
        for grd in [5, 6, 7, 8]:
            for requerimiento in [p.dict_unidades["OR"], p.dict_unidades["ICU"], p.dict_unidades["SDU/WARD"]]:
                for paciente in simulacion.wl.sub_listas[requerimiento][grd]:
                    decisiones_ciclo = paciente.decisiones.get(str(self.ciclo), None)
                    if decisiones_ciclo is not None:
                        for decision in range(len(decisiones_ciclo)):
                            self.decisiones[decision][paciente] = decisiones_ciclo[decision]
                            


        for id_hospital, hospital in simulacion.hospitales.items():
            if id_hospital != 0: # No considero WL
                for unidad_id, unidad in hospital.unidades.items():
                    for paciente in unidad.pacientes:
                        decisiones_ciclo = paciente.decisiones.get(str(self.ciclo), None)
                        if decisiones_ciclo is not None:
                            for decision in range(len(decisiones_ciclo)):
                                self.decisiones[decision][paciente] = decisiones_ciclo[decision]

    def tomar_decisiones(self, simulacion):
        # Reinicio las variables
        self.decisiones = [{}, {}, {}, {}]
        # Copio localmente las ocupaciones de cada hospital
        self.cargar_decisiones(simulacion)
        self.ciclo += 1
        return self.decisiones

class Modelo:

    def __init__(self):
        self.decisiones = []
        self.budget = p.budget # lo que puedo gastar en cada ciclo (operativo)
        self.actual = {
            "WL": [], # Solo para agregar los que si o si tienen que salir de WL
            "WL_sub_deques": {
                p.dict_unidades["OR"]: {},
                p.dict_unidades["ICU"]: {},
                p.dict_unidades["SDU/WARD"]: {}
            },
            "PS": [],
            p.dict_hospitales["Hospital_1"]: {
                p.dict_unidades["OR"]: [],
                p.dict_unidades["ICU"]: [],
                p.dict_unidades["SDU/WARD"]: [],
                p.dict_unidades["GA"]: [],
                p.dict_unidades["ED"]: []
            },
            p.dict_hospitales["Hospital_2"]: {
                p.dict_unidades["OR"]: [],
                p.dict_unidades["ICU"]: [],
                p.dict_unidades["SDU/WARD"]: [],
                p.dict_unidades["GA"]: [],
                p.dict_unidades["ED"]: []
            },
            p.dict_hospitales["Hospital_3"]: {
                p.dict_unidades["OR"]: [],
                p.dict_unidades["ICU"]: [],
                p.dict_unidades["SDU/WARD"]: [],
                p.dict_unidades["GA"]: [],
                p.dict_unidades["ED"]: []
            }
        }
        self.actual_vacio = self.actual.copy()
        self.prioridad_sacado = self.prioridad_sacado_wl()
        self.expulsados_wl_del_ciclo_actual = []
        self.wl_colapso = False
        self.ciclo = 1

    def prioridad_sacado_wl(self): # Revisado, funciona bien
        lista_prioridad = []
        for grd in (p.dict_drg["DRG_5"], p.dict_drg["DRG_6"], p.dict_drg["DRG_7"], p.dict_drg["DRG_8"]): # Solo los que estan en WL
            for requerimiento in (p.dict_unidades["OR"], p.dict_unidades["ICU"], p.dict_unidades["SDU/WARD"]): # Los tres requerimientos
                lista_prioridad.append((grd, requerimiento, p.dict_costo_espera_wl[grd][requerimiento]))
        lista_prioridad.sort(key=lambda x: x[2], reverse=True) # Quedan ordenados de mayor costo de espera a menor
        return lista_prioridad
    
    def cargar_ciclo(self, simulacion): # Revisar
        # Recorro prioridad sacado ya que en ese orden minimizo el costo social
        # Revisar si WL esta colapsada, agregarlos a self.actual["WL"]
        ocupacion_wl = 0
        for grd, requerimiento, _ in self.prioridad_sacado: # (grd, requerimiento, costo_espera)
            self.actual["WL_sub_deques"][requerimiento][grd] = simulacion.wl.sub_listas[requerimiento][grd].copy() # Evito que se modifique la lista original
            ocupacion_wl += len(simulacion.wl.sub_listas[requerimiento][grd])
            
        # Revisar los que alcanzan los 400 ciclos, agregarlos a self.actual["WL"]
        for grd, requerimiento, _ in self.prioridad_sacado:
            copia_subdeque = self.actual["WL_sub_deques"][requerimiento][grd].copy()
            for paciente in copia_subdeque:
                    ti_evento = paciente.ti_evento_actual
                    tiempo_actual = paciente.tiempo_actual
                    los_wl = tiempo_actual - ti_evento
                    if los_wl == 400:
                        # Agrego el paciente a la lista de WL que debo tratar si o si
                        self.actual["WL_sub_deques"][requerimiento][grd].remove(paciente) # Se me habia olvidado removerlos (causaba pequeño error)
                        self.actual["WL"].append(paciente)
        
        # Reviso si la WL sobrepaso su capacidad maxima de 1000
        capacidad_maxima_wl = 1000
        sobran = ocupacion_wl - capacidad_maxima_wl
        if sobran > 0:
            self.wl_colapso = True
            for grd, requerimiento, _ in self.prioridad_sacado:
                if sobran > 0:
                    cantidad_en_sublista = len(self.actual["WL_sub_deques"][requerimiento][grd])
                    if sobran <= cantidad_en_sublista:
                        sacar = sobran
                    elif sobran > cantidad_en_sublista:
                        sacar = cantidad_en_sublista
                    for i in range(sacar):
                        # Orden FIFO, el primero en entrar es el primero en salir
                        self.actual["WL"].append(self.actual["WL_sub_deques"][requerimiento][grd].popleft())
                    sobran -= sacar
        
        self.expulsados_wl_del_ciclo_actual = self.actual["WL"].copy() # Guardo los que salieron de WL en el ciclo (para no mezclar lo en GA vs los "en GA talvez")

        # Relleno localmente las unidades de cada hospital con los pacientes que hay en ese momento
        for id_hospital, hospital in simulacion.hospitales.items():
            if id_hospital != 0: # No considero WL
                for unidad_id, unidad in hospital.unidades.items():
                    self.actual[id_hospital][unidad_id] = unidad.pacientes.copy() # Evito que se modifique la lista original

    def agregar_pacientes_obligatorio_a_ga(self): # Revisado, funciona bien
        orden_entradas_a_ga = {
            p.dict_hospitales["Hospital_1"]: [],
            p.dict_hospitales["Hospital_2"]: [],
            p.dict_hospitales["Hospital_3"]: []
        }

        for hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):
            for paciente in self.actual["WL"]:
                orden_entradas_a_ga[hospital].append((paciente, p.dict_costo_espera_ga[hospital][paciente.grd][paciente.requerimiento_inicial]))
            # Ordeno la lista de pacientes por costo de espera, de menor a mayor
            orden_entradas_a_ga[hospital].sort(key=lambda x: x[1]) # menos caro a mas caro
        
        # Calculo cuanta gente hay en WL y cuantos mandare a cada hospital
        cantidad_expulsados = len(self.actual["WL"])
        h1 = int(cantidad_expulsados/3)
        h2 = int((cantidad_expulsados - h1)/2)
        h3 = cantidad_expulsados - h1 - h2

        cantidad_entradas = {
            p.dict_hospitales["Hospital_1"]: h1,
            p.dict_hospitales["Hospital_2"]: h2,
            p.dict_hospitales["Hospital_3"]: h3
        }

        ya_aceptados = []
        # Agrego los pacientes a la lista de cada hospital
        for hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):

            mantener = []
            for i in range(len(orden_entradas_a_ga[hospital])):
                if not orden_entradas_a_ga[hospital][i][0] in ya_aceptados:
                    mantener.append(orden_entradas_a_ga[hospital][i])
            orden_entradas_a_ga[hospital] = mantener.copy()


            nueva_lista = orden_entradas_a_ga[hospital][:cantidad_entradas[hospital]].copy()
            
            for paciente, _ in nueva_lista:
                paciente.unidad_actual = p.dict_unidades["GA"] # Demasiado ojo con esto, full trucho
                paciente.hospital_actual = hospital # Demasiado ojo con esto, full trucho
                self.actual[hospital][p.dict_unidades["GA"]].append(paciente)
                ya_aceptados.append(paciente)
                self.actual["WL"].remove(paciente)

            orden_entradas_a_ga[hospital] = nueva_lista.copy()
        
        return orden_entradas_a_ga
        
    def dar_de_alta(self): # Parece funcionar
        for id_hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):
            # Primero reviso que pacientes terminan su evolucion en el SDU_WARD
            pacientes_de_alta = [] # Revisar

            # Cuidado, estaba modificando una lista sobre la que estoy iterando
            lista_copia = self.actual[id_hospital][p.dict_unidades["SDU/WARD"]].copy()
            for paciente in lista_copia:
                if paciente.unidad_requerida == p.dict_unidades["END"]:
                    pacientes_de_alta.append(paciente)
                    self.actual[id_hospital][p.dict_unidades["SDU/WARD"]].remove(paciente)

            dict_temporal = {}
            for paciente in pacientes_de_alta:
                dict_temporal[paciente] = {"hospital": paciente.hospital_actual, "unidad": paciente.unidad_requerida}
            self.decisiones.append(dict_temporal)

    def cambios_internos_hospital(self, id_hospital): # Revisar
        dict_temporal_ga = {}
        dict_temporal = {}
        pacientes_que_meti_desde_ga = []
        # Pacientes que seran cambiados a camas libres
        pacientes_cambio_a_camas_libres = [] # Revisar
        # Listas de prioridad de entrada a cada unidad
        requerimientos = {
            p.dict_unidades["OR"]: [],
            p.dict_unidades["ICU"]: [],
            p.dict_unidades["SDU/WARD"]: []
        }
        camas_libres = {
            p.dict_unidades["OR"]: 0,
            p.dict_unidades["ICU"]: 0,
            p.dict_unidades["SDU/WARD"]: 0
        }
        # Capacidades de cada unidad
        capacidades = {
            p.dict_unidades["OR"]: p.dict_capacidades[id_hospital][p.dict_unidades["OR"]],
            p.dict_unidades["ICU"]: p.dict_capacidades[id_hospital][p.dict_unidades["ICU"]],
            p.dict_unidades["SDU/WARD"]: p.dict_capacidades[id_hospital][p.dict_unidades["SDU/WARD"]]
        }
        # Ahora cuento con las ocupaciones reales de cada unidad
        def ocupaciones_actuales(): # Revisar
            ocupacion_or = len(self.actual[id_hospital][p.dict_unidades["OR"]])
            ocupacion_icu = len(self.actual[id_hospital][p.dict_unidades["ICU"]])
            ocupacion_sdu_ward = len(self.actual[id_hospital][p.dict_unidades["SDU/WARD"]])
            return ocupacion_or, ocupacion_icu, ocupacion_sdu_ward
        # Funcion que agrega costos de espera extra a los que pueden liberar una cama y dejar pasar a otro
        # Modifica directamente la lista de requerimientos
        def actualizar_costo_liberar_cama(requerimientos): # Revisar
            for unidad in requerimientos:
                requerimientos[unidad].sort(key=lambda x: x["costo"]) # menos caro a mas caro

            for unidad in requerimientos:
                for i in range(len(requerimientos[unidad])):
                    paciente = requerimientos[unidad][i]["paciente"]
                    unidad_actual = paciente.unidad_actual # Unidad actual siempre distinta de la unidad requerida a los que esperan
                    if unidad_actual not in (p.dict_unidades["GA"], p.dict_unidades["ED"]): # osea los que estan usando una cama
                        if len(requerimientos[unidad_actual]) > 0:  
                            # Aca se le suma al costo de espera del paciente el costo de espera de quien podria usar su cama una vez que el paciente se va
                            requerimientos[unidad][i]["costo"] = paciente.costo_espera() + requerimientos[unidad_actual][-1]["costo"]
            
            for unidad in requerimientos:
                requerimientos[unidad].sort(key=lambda x: x["costo"]) # menos caro a mas caro
            
        # Ahora reviso los pacientes que estan esperando en cada unidad y los agrego a la lista de requerimientos
        for unidad in self.actual[id_hospital]:
            for paciente in self.actual[id_hospital][unidad]:

                # Los dado de alta ya los saque, guardo los pacientes como {"costo": costo, "paciente": paciente}
                if paciente.esperando:
                    requerimientos[paciente.unidad_requerida].append({"costo": paciente.costo_espera(), "paciente": paciente})
        
        # Ordeno la lista de requerimientos por costo de espera, de menor a mayor
        actualizar_costo_liberar_cama(requerimientos)

        def calcular_camas_libres(camas_libres, capacidades):
            # Ahora se revisa la disponibilidad de camas
            ocupacion_or, ocupacion_icu, ocupacion_sdu_ward = ocupaciones_actuales()
            camas_libres[p.dict_unidades["OR"]] = capacidades[p.dict_unidades["OR"]] - ocupacion_or
            camas_libres[p.dict_unidades["ICU"]] = capacidades[p.dict_unidades["ICU"]] - ocupacion_icu
            camas_libres[p.dict_unidades["SDU/WARD"]] = capacidades[p.dict_unidades["SDU/WARD"]] - ocupacion_sdu_ward
        calcular_camas_libres(camas_libres, capacidades)
        
        camas_libres_siguen_cambiando = True
        while camas_libres_siguen_cambiando:
            camas_libres_or_anterior = camas_libres.copy()
        
            for unidad in camas_libres: # EL orden es OR, ICU, SDU/WARD ya que asi se definio el diccionario
                for i in range(camas_libres[unidad]):
                    if len(requerimientos[unidad]) > 0:
                        ultimo_mas_caro = requerimientos[unidad].pop()
                        paciente = ultimo_mas_caro["paciente"]
                        # Lo saco de su unidad actual y lo agrego a la nueva
                        self.actual[id_hospital][paciente.unidad_actual].remove(paciente)
                        self.actual[id_hospital][unidad].append(paciente)
                        
                        # Lo agrego a la lista de pacientes que cambiaron a camas libres
                        # Pueden haber pacientes de GA que ya habian esperado ahi
                        if paciente not in self.expulsados_wl_del_ciclo_actual:
                            pacientes_cambio_a_camas_libres.append(paciente)

                        elif paciente in self.expulsados_wl_del_ciclo_actual:
                            dict_temporal_ga[paciente] = {"hospital": id_hospital, "unidad": p.dict_unidades["GA"]}
                            dict_temporal[paciente] = {"hospital": id_hospital, "unidad": paciente.unidad_requerida}
                            pacientes_que_meti_desde_ga.append(paciente)

                # Como algunas primeras prioridades ya entraron a la unidad, se vuelve a calcular
                actualizar_costo_liberar_cama(requerimientos)
            
            # Una vez que se paso por todas las unidades, se actualizan las camas libres
            calcular_camas_libres(camas_libres, capacidades)

            # Si no hubo cambios en las camas libres, se sale del while
            if camas_libres_or_anterior == camas_libres:
                camas_libres_siguen_cambiando = False

        # Agregar los pacientes que entraron a la unidad de GA
        self.decisiones.append(dict_temporal_ga)

        # Agregar a decisiones los pacientes que cambiaron a camas libres
        for paciente in pacientes_cambio_a_camas_libres:
            dict_temporal[paciente] = {"hospital": paciente.hospital_actual, "unidad": paciente.unidad_requerida}
        self.decisiones.append(dict_temporal)

        """En caso de llenarse las unidades puede darse que pacientes de distintas unidades
        intercambien camas entre si de manera simultanea, las unidades seguirian llenas
        pero tratando efectivamente a los pacientes y no teniendolos en espera, para eso
        necesito listas mas detalladas"""
        pacientes_cambios_simultaneos = [] # Revisar

        origen_requerimiento = {
            (p.dict_unidades["OR"], p.dict_unidades["ICU"]): [],
            (p.dict_unidades["ICU"], p.dict_unidades["OR"]): [],
            (p.dict_unidades["ICU"], p.dict_unidades["SDU/WARD"]): [],
            (p.dict_unidades["SDU/WARD"], p.dict_unidades["ICU"]): [],
            (p.dict_unidades["SDU/WARD"], p.dict_unidades["OR"]): [],
            (p.dict_unidades["OR"], p.dict_unidades["SDU/WARD"]): []
        }

        cambios_simultaneos = {
            (p.dict_unidades["OR"], p.dict_unidades["ICU"]): 0,
            (p.dict_unidades["ICU"], p.dict_unidades["SDU/WARD"]): 0,
            (p.dict_unidades["SDU/WARD"], p.dict_unidades["OR"]): 0,
        }

        for unidad in requerimientos:
            for paciente in requerimientos[unidad]:
                paciente = paciente["paciente"]
                unidad_actual = paciente.unidad_actual
                if unidad_actual not in (p.dict_unidades["GA"], p.dict_unidades["ED"]):
                    origen_requerimiento[(unidad_actual, unidad)].append(paciente)
        
        for camino in origen_requerimiento:
            origen_requerimiento[camino].sort(key=lambda x: x.costo_espera()) # menos caro a mas caro         
            if camino in cambios_simultaneos:    
                cambios_simultaneos[camino] = min(len(origen_requerimiento[camino]), len(origen_requerimiento[(camino[1], camino[0])]))

        for cambios in cambios_simultaneos:
            for i in range(cambios_simultaneos[cambios]):
                paciente = origen_requerimiento[cambios].pop()
                pacientes_cambios_simultaneos.append(paciente)
                self.actual[id_hospital][paciente.unidad_actual].remove(paciente)
                self.actual[id_hospital][paciente.unidad_requerida].append(paciente)

                paciente = origen_requerimiento[(cambios[1], cambios[0])].pop()
                pacientes_cambios_simultaneos.append(paciente)
                self.actual[id_hospital][paciente.unidad_actual].remove(paciente)
                self.actual[id_hospital][paciente.unidad_requerida].append(paciente)
        

        dict_temporal = {}
        for paciente in pacientes_cambios_simultaneos:
            dict_temporal[paciente] = {"hospital": paciente.hospital_actual, "unidad": paciente.unidad_requerida}
        self.decisiones.append(dict_temporal)

        # Ahora devuelvo a sus valores originales a los pacientes que pasaron por GA de este ciclo
        for paciente in pacientes_que_meti_desde_ga:
            paciente.unidad_actual = p.dict_unidades["WL"] # vuelven a wl ya que simulacion los tiene que sacar de ahi
            paciente.hospital_actual = 0 # id de la lista de espera

    def traslados(self): # Parece funcionar
        # Necesito dos listas ya que primero los paso a ED y luego a la unidad requerida
        # Por lo que tienen que estar en ED para poder sacarlos de ahi
        # Traslado a todos, los meto a ED, despues los saco y los meto a la unidad requerida
        trasladados_modo_dict = []
        internar_modo_dict = []

        pacientes_en_ed = []

        camas_libres = {
        p.dict_hospitales["Hospital_1"]: {
            p.dict_unidades["OR"]: 0,
            p.dict_unidades["ICU"]: 0,
            p.dict_unidades["SDU/WARD"]: 0
        },
        p.dict_hospitales["Hospital_2"]: {
            p.dict_unidades["OR"]: 0,
            p.dict_unidades["ICU"]: 0,
            p.dict_unidades["SDU/WARD"]: 0
        },
        p.dict_hospitales["Hospital_3"]: {
            p.dict_unidades["OR"]: 0,
            p.dict_unidades["ICU"]: 0,
            p.dict_unidades["SDU/WARD"]: 0
        }
        }

        capacidades = {
            p.dict_hospitales["Hospital_1"]: {
            p.dict_unidades["OR"]: p.dict_capacidades[p.dict_hospitales["Hospital_1"]][p.dict_unidades["OR"]],
            p.dict_unidades["ICU"]: p.dict_capacidades[p.dict_hospitales["Hospital_1"]][p.dict_unidades["ICU"]],
            p.dict_unidades["SDU/WARD"]: p.dict_capacidades[p.dict_hospitales["Hospital_1"]][p.dict_unidades["SDU/WARD"]]
            },
            p.dict_hospitales["Hospital_2"]: {
            p.dict_unidades["OR"]: p.dict_capacidades[p.dict_hospitales["Hospital_2"]][p.dict_unidades["OR"]],
            p.dict_unidades["ICU"]: p.dict_capacidades[p.dict_hospitales["Hospital_2"]][p.dict_unidades["ICU"]],
            p.dict_unidades["SDU/WARD"]: p.dict_capacidades[p.dict_hospitales["Hospital_2"]][p.dict_unidades["SDU/WARD"]]
            },
            p.dict_hospitales["Hospital_3"]: {
            p.dict_unidades["OR"]: p.dict_capacidades[p.dict_hospitales["Hospital_3"]][p.dict_unidades["OR"]],
            p.dict_unidades["ICU"]: p.dict_capacidades[p.dict_hospitales["Hospital_3"]][p.dict_unidades["ICU"]],
            p.dict_unidades["SDU/WARD"]: p.dict_capacidades[p.dict_hospitales["Hospital_3"]][p.dict_unidades["SDU/WARD"]]
            }
        }

        for hospital in camas_libres:
            for unidad in camas_libres[hospital]:
                ocupacion_unidad = len(self.actual[hospital][unidad])
                capacidad_unidad = capacidades[hospital][unidad]
                camas_libres[hospital][unidad] = capacidad_unidad - ocupacion_unidad

        for id_hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):
            for paciente in self.actual[id_hospital][p.dict_unidades["ED"]]:
                    pacientes_en_ed.append(paciente)
        pacientes_en_ed.sort(key=lambda x: x.costo_espera(), reverse=True) # mas caro a menos caro

        copia_pacientes_en_ed = pacientes_en_ed.copy()
        for paciente in copia_pacientes_en_ed:
            costo_traslado = []
            for hospital in camas_libres:
                    if hospital != paciente.hospital_actual:
                        if camas_libres[hospital][paciente.unidad_requerida] > 0: # me interesa si hay camas libres
                            costo_traslado_paciente = paciente.costo_traslado(hospital)
                            costo_traslado.append((hospital, costo_traslado_paciente))
            costo_traslado.sort(key=lambda x: x[1]) # menos caro a mas caro (costo operativo)

            if len(costo_traslado) > 0:
                if self.budget >= costo_traslado[0][1]:
                    self.budget -= costo_traslado[0][1]
                    # Si hay camas libres en otro hospital, se traslada al mas barato
                    hospital_traslado = costo_traslado[0][0] # [0] primero lista [0]id_hospital
                    pacientes_en_ed.remove(paciente) # En esta lista quedaron los que no se trasladaron
                    self.actual[paciente.hospital_actual][p.dict_unidades["ED"]].remove(paciente)
                    # Tiene que pasar por el ED del hospital de destino
                    datos_traslado = {"hospital": hospital_traslado, "unidad": p.dict_unidades["ED"]}
                    trasladados_modo_dict.append({"paciente": paciente, "datos": datos_traslado})
                    self.actual[hospital_traslado][paciente.unidad_requerida].append(paciente)
                    camas_libres[hospital_traslado][paciente.unidad_requerida] -= 1
                    # Aqui ya lo meti a su unidad requerida en el nuevo hospital
                    datos_traslado = {"hospital": hospital_traslado, "unidad": paciente.unidad_requerida}
                    internar_modo_dict.append({"paciente": paciente, "datos": datos_traslado})

        # Primero traslados
        dict_temporal = {}
        for dict_cambio in trasladados_modo_dict:
            dict_temporal[dict_cambio["paciente"]] = dict_cambio["datos"]
        self.decisiones.append(dict_temporal)
        
        # Luego internar
        dict_temporal = {}
        for dict_cambio in internar_modo_dict:
            dict_temporal[dict_cambio["paciente"]] = dict_cambio["datos"]
        self.decisiones.append(dict_temporal)

        return pacientes_en_ed

    def derivar_ed(self, pacientes_en_ed): # Parece funcionar
        datos_derivar = []
        # Ya ordenados por costo de espera mayor a menor, voy derivando a los mas caros
        copia_pacientes_en_ed = pacientes_en_ed.copy()
        for paciente in copia_pacientes_en_ed:
            if self.budget >= paciente.costo_desvio():
                self.budget -= paciente.costo_desvio()
                # Lo saco de la lista de pacientes en ED
                pacientes_en_ed.remove(paciente)
                self.actual[paciente.hospital_actual][paciente.unidad_actual].remove(paciente)
                # Lo agrego a la lista de decisiones                
                datos_traslado = {"hospital": paciente.hospital_actual, "unidad": p.dict_unidades["PS"]}
                datos_derivar.append({"paciente": paciente, "datos": datos_traslado})

        # Luego internar
        dict_temporal = {}
        for dict_cambio in datos_derivar:
            dict_temporal[dict_cambio["paciente"]] = dict_cambio["datos"]
        self.decisiones.append(dict_temporal)

    def derivar_wl(self): # Revisar
        for id_hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):
            pacientes_en_ga = []
            datos_derivar = []
            datos_dejar_en_ga = []

            for paciente in self.actual[id_hospital][p.dict_unidades["GA"]]:
                # Esto solo para los nuevos que acabo de meter a GA, tnego que decidir si efectivamente los meto o si se derivan desde WL
                # Se hace para evitar cambiar a pacientes que ya estaban en GA lo cual causa errores
                if paciente in self.expulsados_wl_del_ciclo_actual:
                    pacientes_en_ga.append(paciente)
            pacientes_en_ga.sort(key=lambda x: p.dict_costo_derivar_wl[x.grd][x.requerimiento_inicial]) # menos caro a mas caro
            extras_derivados = 0

            # Ojo que se me mezclan los que ya estaban en GA con los que acabo de "meter" entre comillas
            # Tengo que saber cuales son los del ciclo
            # Ya ordenados por costo de derivar menor a mayor, voy derivando a los mas baratos
            cantidad_en_ga = len(self.actual[id_hospital][p.dict_unidades["GA"]])
            if cantidad_en_ga > p.dict_capacidades[id_hospital][p.dict_unidades["GA"]]:
                cantidad_a_derivar = cantidad_en_ga - p.dict_capacidades[id_hospital][p.dict_unidades["GA"]]
                # Solo derivo si son mas de la capacidad del GA
                copia_pacientes_en_ga = pacientes_en_ga[:cantidad_a_derivar].copy()
                for paciente in copia_pacientes_en_ga:
                    costo_desvio = p.dict_costo_derivar_wl[paciente.grd][paciente.requerimiento_inicial]
                    if self.budget >= costo_desvio:
                        extras_derivados += 1
                        self.budget -= costo_desvio
                        # Lo saco de la lista de pacientes en GA (que en realidad nunca lo meti a GA, en teoria)
                        pacientes_en_ga.remove(paciente)
                        self.actual[paciente.hospital_actual][paciente.unidad_actual].remove(paciente)
                        # Lo agrego a la lista de decisiones, 0 de hospital WL              
                        datos_traslado = {"hospital": 0, "unidad": p.dict_unidades["PS"]}
                        datos_derivar.append({"paciente": paciente, "datos": datos_traslado})
                        # Ahora des hago lo trucho de antes y los vuelvo a su origen, nunca los meti a GA
                        paciente.unidad_actual = p.dict_unidades["WL"]
                        paciente.hospital_actual = 0

                # Una vez que se hayan derivado todos los extras que no cabian en GA
                if extras_derivados == cantidad_a_derivar:
                    # Si ya no hay que derivar, devuelvo los pacientes que quedaron en GA a su estado original y aplico los cambios
                    for paciente in pacientes_en_ga: # Los que efectivamente se quedan en GA
                        datos_traslado = {"hospital": id_hospital, "unidad": p.dict_unidades["GA"]}
                        datos_dejar_en_ga.append({"paciente": paciente, "datos": datos_traslado})
                        # Ahora des hago lo trucho de antes y los vuelvo a su origen
                        paciente.unidad_actual = p.dict_unidades["WL"]
                        paciente.hospital_actual = 0

                # Luego pasar al PS en decisiones
                dict_temporal = {}
                for dict_cambio in datos_derivar:
                    dict_temporal[dict_cambio["paciente"]] = dict_cambio["datos"]
                self.decisiones.append(dict_temporal)

                # Luego pasar al GA en decisiones
                dict_temporal = {}
                for dict_cambio in datos_dejar_en_ga:
                    dict_temporal[dict_cambio["paciente"]] = dict_cambio["datos"]
                self.decisiones.append(dict_temporal)
            
            else: # Si no hay que derivar, devuelo los pacientes a su estado original y aplico los cambios
                paciente_en_ga_copia = pacientes_en_ga.copy()
                for paciente in paciente_en_ga_copia:
                    datos_traslado = {"hospital": id_hospital, "unidad": p.dict_unidades["GA"]}
                    datos_dejar_en_ga.append({"paciente": paciente, "datos": datos_traslado})
                    # Ahora des hago lo trucho de antes y los vuelvo a su origen, nunca los meti a GA
                    paciente.unidad_actual = p.dict_unidades["WL"]
                    paciente.hospital_actual = 0
                
                # Luego pasar al GA en decisiones
                dict_temporal = {}
                for dict_cambio in datos_dejar_en_ga:
                    dict_temporal[dict_cambio["paciente"]] = dict_cambio["datos"]
                self.decisiones.append(dict_temporal)

    def asegurar_factibilidad_ed_ga(self): # Revisar
        # Caso quiebre Stock!!!!!!
        se_quebro = False
        ed_colapsado = False
        ga_colapsado = False
        pacientes_en_ed = []

        for id_hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):
            if len(self.actual[id_hospital][p.dict_unidades["ED"]]) > p.dict_capacidades[id_hospital][p.dict_unidades["ED"]]:
                # Se quebro el stock y todavia no es factible
                se_quebro = True
                ed_colapsado = True
    
   
        for id_hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):
            if len(self.actual[id_hospital][p.dict_unidades["GA"]]) > p.dict_capacidades[id_hospital][p.dict_unidades["GA"]]:
                # Se quebro el stock y todavia no es factible
                se_quebro = True
                ga_colapsado = True


        if se_quebro:
            self.budget = 100000000000 # Infinito basicamente
            if ed_colapsado:
                self.derivar_ed(pacientes_en_ed)
                print("Se quiebra el stock debido a ED, se derivan pacientes a WL")
            if ga_colapsado:
                self.derivar_wl()
                print(f"GA quiebra stock, h1: {len(self.actual[1][4])}, h2: {len(self.actual[2][4])}, h3: {len(self.actual[3][4])}")

    def atender_wl(self): # Completar
        # Meter al GA
        meter_a_ga_modo_dict = []
        internar_modo_dict = []

        primero = (self.ciclo % 3) + 1
        segundo = ((self.ciclo + 1) % 3) + 1
        tercero = ((self.ciclo + 2) % 3) + 1

        # Meto a todos los pacientes que pueda al parecer, igual extraño
        camas_libres = {
        p.dict_hospitales[f"Hospital_{primero}"]: {
            p.dict_unidades["OR"]: 0,
            p.dict_unidades["ICU"]: 0,
            p.dict_unidades["SDU/WARD"]: 0
        },
        p.dict_hospitales[f"Hospital_{segundo}"]: {
            p.dict_unidades["OR"]: 0,
            p.dict_unidades["ICU"]: 0,
            p.dict_unidades["SDU/WARD"]: 0
        },
        p.dict_hospitales[f"Hospital_{tercero}"]: {
            p.dict_unidades["OR"]: 0,
            p.dict_unidades["ICU"]: 0,
            p.dict_unidades["SDU/WARD"]: 0
        }
        }

        capacidades = {
            p.dict_hospitales["Hospital_1"]: {
            p.dict_unidades["OR"]: p.dict_capacidades[p.dict_hospitales["Hospital_1"]][p.dict_unidades["OR"]],
            p.dict_unidades["ICU"]: p.dict_capacidades[p.dict_hospitales["Hospital_1"]][p.dict_unidades["ICU"]],
            p.dict_unidades["SDU/WARD"]: p.dict_capacidades[p.dict_hospitales["Hospital_1"]][p.dict_unidades["SDU/WARD"]]
            },
            p.dict_hospitales["Hospital_2"]: {
            p.dict_unidades["OR"]: p.dict_capacidades[p.dict_hospitales["Hospital_2"]][p.dict_unidades["OR"]],
            p.dict_unidades["ICU"]: p.dict_capacidades[p.dict_hospitales["Hospital_2"]][p.dict_unidades["ICU"]],
            p.dict_unidades["SDU/WARD"]: p.dict_capacidades[p.dict_hospitales["Hospital_2"]][p.dict_unidades["SDU/WARD"]]
            },
            p.dict_hospitales["Hospital_3"]: {
            p.dict_unidades["OR"]: p.dict_capacidades[p.dict_hospitales["Hospital_3"]][p.dict_unidades["OR"]],
            p.dict_unidades["ICU"]: p.dict_capacidades[p.dict_hospitales["Hospital_3"]][p.dict_unidades["ICU"]],
            p.dict_unidades["SDU/WARD"]: p.dict_capacidades[p.dict_hospitales["Hospital_3"]][p.dict_unidades["SDU/WARD"]]
            }
        }
        
        for hospital in camas_libres: # Ojo podria quedarse en un loop infinito
            for unidad in camas_libres[hospital]:
                ocupacion_unidad = len(self.actual[hospital][unidad])
                capacidad_unidad = capacidades[hospital][unidad]
                camas_disponibles = capacidad_unidad - ocupacion_unidad
                camas_libres[hospital][unidad] = camas_disponibles

                contador = 0
                for grd, requerimiento, _ in self.prioridad_sacado:
                    if unidad == requerimiento and camas_disponibles > 0:
                        while (len(self.actual["WL_sub_deques"][requerimiento][grd]) > 0
                            and contador < camas_disponibles):
                            
                            paciente = self.actual["WL_sub_deques"][requerimiento][grd].popleft()

                            self.actual[hospital][paciente.unidad_requerida].append(paciente)

                            datos = {"hospital": hospital, "unidad": p.dict_unidades["GA"]}
                            meter_a_ga_modo_dict.append({"paciente": paciente, "datos": datos})

                            datos = {"hospital": hospital, "unidad": paciente.unidad_requerida}
                            internar_modo_dict.append({"paciente": paciente, "datos": datos})

                            contador += 1

        # Primero al GA
        dict_temporal = {}
        for dict_cambio in meter_a_ga_modo_dict:
            dict_temporal[dict_cambio["paciente"]] = dict_cambio["datos"]
        self.decisiones.append(dict_temporal)
        
        # Luego internar
        dict_temporal = {}
        for dict_cambio in internar_modo_dict:
            dict_temporal[dict_cambio["paciente"]] = dict_cambio["datos"]
        self.decisiones.append(dict_temporal)
                    
    def tomar_decisiones(self, simulacion):
        # Reinicio las variables
        self.decisiones = []
        self.expulsados_wl_del_ciclo_actual = []
        self.actual = self.actual_vacio.copy()
        self.budget = p.budget

        # Copio localmente las ocupaciones de cada hospital
        self.cargar_ciclo(simulacion)

        # Reviso si hay pacientes que estoy obligado a sacar de WL (no implementado todavia)
        self.agregar_pacientes_obligatorio_a_ga() 

        # Primero reviso si hay pacientes que deben ser dados de alta
        self.dar_de_alta()

        # Luego realizo los cambios internos de cada hospital
        for id_hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):
            self.cambios_internos_hospital(id_hospital)
        
        # Luego realizo los traslados
        pacientes_quedaron_en_ed = self.traslados()

        # Luego reviso si hay pacientes en ED que deben ser derivados a PS
        self.derivar_ed(pacientes_quedaron_en_ed)

        # Luego reviso si hay pacientes en WL que deben ser derivados a PS
        self.derivar_wl()

        # Asegurar factibilidad
        self.asegurar_factibilidad_ed_ga()

        # Luego reviso si hay pacientes en WL que pueden ser atendidos
        self.atender_wl()
        self.ciclo += 1
        return self.decisiones
    
class ModeloA(Modelo):
    """Espera hasta que la Wl se llene con mas de 1000 personas, de ahi espera 100 ciclos mas
    y luego empieza a atender pacientes de la WL directamente, por lo que esta empieza a bajar"""
    def __init__(self):
        super().__init__()
        self.t_colapso = 0
    
    def tomar_decisiones(self, simulacion):
        # Reinicio las variables
        self.decisiones = []
        self.expulsados_wl_del_ciclo_actual = []
        self.actual = self.actual_vacio.copy()
        self.budget = p.budget

        # Copio localmente las ocupaciones de cada hospital
        self.cargar_ciclo(simulacion)

        # Reviso si hay pacientes que estoy obligado a sacar de WL (no implementado todavia)
        self.agregar_pacientes_obligatorio_a_ga() 

        # Primero reviso si hay pacientes que deben ser dados de alta
        self.dar_de_alta()

        # Luego realizo los cambios internos de cada hospital
        for id_hospital in (p.dict_hospitales["Hospital_1"], p.dict_hospitales["Hospital_2"], p.dict_hospitales["Hospital_3"]):
            self.cambios_internos_hospital(id_hospital)
        
        # Luego realizo los traslados
        pacientes_quedaron_en_ed = self.traslados()

        # Luego reviso si hay pacientes en ED que deben ser derivados a PS
        self.derivar_ed(pacientes_quedaron_en_ed)

        # Luego reviso si hay pacientes en WL que deben ser derivados a PS
        self.derivar_wl()

        # Asegurar factibilidad
        self.asegurar_factibilidad_ed_ga()

        # Luego reviso si hay pacientes en WL que pueden ser atendidos
        # Se empieza a hacer cuando colapsa el sistema
        if self.wl_colapso and self.t_colapso == 0:
            self.t_colapso = self.ciclo # Guardo el ciclo en el que colapso
        
        if self.wl_colapso and self.ciclo - self.t_colapso > 100:
            self.atender_wl()
            
        self.ciclo += 1
        return self.decisiones

class Simulacion: # Revisado, funciona bien

    def __init__(self, T_max, seed, ciclos, modelo = Modelo(), modelo_alternativo = Modelo(), ciclo_de_cambio = 0, pacientes_caso_base = False, log_detallado = False):
        # Asi no vuelvo a crear el archivo de pacientes si ya existe
        """Se empieza generando los pacientes con la semilla de random
        y la cantidad de ciclos que se desean crear pacientes"""
        t0 = time.time()
        self.seed = seed
        self.pacientes_caso_base = pacientes_caso_base
        self.log_detallado = log_detallado
        if self.pacientes_caso_base == False:
            folder_path = "resultados incertidumbre"
            self.file_name = f"{self.seed}_{ciclos}.json"
            file_path = os.path.join(folder_path, self.file_name)
            if os.path.isfile(file_path):
                print(f"Se utiliza archivo existente {self.file_name} de pacientes ({time.time() - t0:.2f} segundos)")
            else:
                generar_pacientes(self.seed, ciclos)
                print(f"Se crea archivo {self.file_name} de pacientes ({time.time() - t0:.2f} segundos)")
        t0 = time.time()
        self.T_max = T_max
        self.pacientes_separados_por_llegada = self.cargar_pacientes_separados_por_llegada()
        print(f"Pacientes separados por llegada cargados ({time.time() - t0:.2f} segundos)")
        t0 = time.time()
        self.ciclos = ciclos
        self.modelo = modelo
        self.modelo_alternativo = modelo_alternativo
        self.ciclo_de_cambio = ciclo_de_cambio
        self.hospital_1 = Hospital(1)
        self.hospital_2 = Hospital(2)
        self.hospital_3 = Hospital(3)
        self.wl = WL([1, 2, 3], [5, 6, 7, 8])
        self.hospitales = { # Para acceder a los hospitales por su id
            0: self.wl,
            p.dict_hospitales["Hospital_1"]: self.hospital_1,
            p.dict_hospitales["Hospital_2"]: self.hospital_2,
            p.dict_hospitales["Hospital_3"]: self.hospital_3
        }
        self.ps = PS([1, 2, 3], [1, 2, 3, 4, 5, 6, 7, 8])
        self.end = END([1, 2, 3], [1, 2, 3, 4, 5, 6, 7, 8])
        self.unidades_termino = { # Para acceder a las unidades de termino por su id
            p.dict_unidades["PS"]: self.ps,
            p.dict_unidades["END"]: self.end
        }
        self.budget = p.budget
        self.tasa_descuento = p.tasa_descuento
        print(f"Clase Simulacion instanciada ({time.time() - t0:.2f} segundos)")

    # Funcion necesaria al momento de instanciar la clase
    def cargar_pacientes_separados_por_llegada(self): # Revisado, funciona bien
        # Cargo los datos necesarios y transformo las llaves nuevamente a int (que se habian vuelto str)
        incertidumbre = {}
        for hospital in range(0,4): # 0 son llegadas a WL
            incertidumbre[hospital] = {}
            for requerimiento in range(1,4):
                incertidumbre[hospital][requerimiento] = {}

        if self.pacientes_caso_base == False:
            with open(f"resultados incertidumbre/{self.file_name}", "r") as file:
                incertidumbre_keys_str = json.load(file)
        else:
            with open("resultados incertidumbre/incertidumbre_base.json", "r") as file:
                incertidumbre_keys_str = json.load(file)

        for hospital in range(0,4): # 0 son llegadas a WL
            for requerimiento in range(1,4):
                for grd in range(1,9):
                    incertidumbre[hospital][requerimiento][grd] = []
                    lista = incertidumbre_keys_str[str(hospital)][str(requerimiento)][str(grd)]
                    if lista != []:
                        for data in lista:
                            arreglado = {
                            'TI': data["TI"],
                            'camino': {1: data['camino']["1"], 2: data['camino']["2"], 3: data['camino']["3"]},
                            'espera': {1: data['espera']["1"], 2: data['espera']["2"], 3: data['espera']["3"]}
                            }
                            if self.pacientes_caso_base:
                                arreglado["decisiones"] = data["decisiones"]
                                arreglado["id"] = data["id"]

                            incertidumbre[hospital][requerimiento][grd].append(arreglado)
                    else:
                        incertidumbre[hospital][requerimiento][grd] = []

        # Se instancian a todos los pacientes a partir de los datos de incertidumbre
        pacientes = {}
        lista_pacientes = []
        # 0 son llegadas a WL
        for hospital in range(0,4): 
            pacientes[hospital] = {}
            for requerimiento in range(1,4):
                pacientes[hospital][requerimiento] = {}
                for grd in range(1,9):
                    pacientes[hospital][requerimiento][grd] = []
                    cantidad_pacientes = len(incertidumbre[hospital][requerimiento][grd])
                    if cantidad_pacientes != 0:
                        for i in range(cantidad_pacientes):
                            paciente = Paciente(hospital, requerimiento, grd, incertidumbre[hospital][requerimiento][grd][i]) # i es el index de la lista
                            pacientes[hospital][requerimiento][grd].append(paciente)
                            lista_pacientes.append(paciente)
                    else:
                        pacientes[hospital][requerimiento][grd] = []

        # Se generan tantas listas como dias con llegadas haya
        pacientes_separados_por_llegada = {}
        for paciente in lista_pacientes:
            ciclo = paciente.ti_inicial
            if ciclo not in pacientes_separados_por_llegada:
                pacientes_separados_por_llegada[ciclo] = []
            pacientes_separados_por_llegada[ciclo].append(paciente)

        return pacientes_separados_por_llegada
    
    # Funciones necesarias al momento de simular
    def agregar_pacientes_ciclo_a_wl(self, ciclo): # Revisado, funciona bien
        pacientes_ciclo = self.pacientes_separados_por_llegada.get(ciclo, [])
        for paciente in pacientes_ciclo:
            # hospital 0 es WL
            if paciente.hospital_llegada == 0:
                self.wl.agregar_paciente(paciente)
            else:
                pass

    def agregar_pacientes_ciclo_a_ed(self, ciclo): # Revisado, funciona bien
        pacientes_ciclo = self.pacientes_separados_por_llegada.get(ciclo, [])
        for paciente in pacientes_ciclo:
            # si hospital es 1, 2 o 3 llegan a ED
            if paciente.hospital_llegada != 0:
                self.hospitales[paciente.hospital_llegada].agregar_paciente(paciente, paciente.unidad_actual)
            else:
                pass

    def sacar_paciente(self, paciente): # Revisado, funciona bien
        # Retorna el paciente que se saca de la unidad, o None si no se pudo sacar
        if paciente.hospital_actual == 0:
            return self.hospitales[paciente.hospital_actual].sacar_paciente(paciente)  
        else:
            return self.hospitales[paciente.hospital_actual].sacar_paciente(paciente, paciente.unidad_actual)

    def agregar_paciente(self, paciente, hospital, unidad): # Revisado, funciona bien
        # Retorna True si se agrega el paciente, False si no
        if unidad not in (p.dict_unidades["PS"], p.dict_unidades["END"]):
            return self.hospitales[hospital].agregar_paciente(paciente, unidad)
        else:
            # No retornan nada porque siempre se agrega el paciente
            self.unidades_termino[unidad].agregar_paciente(paciente)
            return True

    def implementar_decisiones(self, decisiones: list): # Revisado, funciona bien
        """Las decisiones son una lista de diccionarios, cada uno con la siguiente estructura:
        {
            paciente: {"hospital": hospital, "unidad": unidad},
            ...
            paciente: {"hospital": hospital, "unidad": unidad},
        }
        Estas se deben implementar en el orden de la lista, se sacan a todos los pacientes de su
        unidad actual y se cambian a la unidad y hospital que se indica en el diccionario. Luego se 
        pasa al siguiente diccionario y se repite el proceso. Se hace de esta manera porque a veces
        puede ocurrir que dos pacientes tengan que ser cambiados entre si, por lo que los cambios
        deben ser simultaneos por cada diccionario, para sacar a un paciente no necesito saber donde
        esta ya que cada paciente contiene su unidad y hospital actual.
        """
        for decision in decisiones:
            # Saco a todos los pacientes de su unidad actual
            for paciente in decision:
                sacado = self.sacar_paciente(paciente)
                if paciente.esperando == False:
                    print(f"Error no esperando: id: {paciente.id}, h:{paciente.hospital_actual}, u: {paciente.unidad_actual}, caminos: {paciente.camino}, espera: {paciente.espera}")
                    
                if sacado == None:
                    print(f"Error al sacar paciente {paciente.id} de h:{paciente.hospital_actual}, u: {paciente.unidad_actual}")

            # Agrego a todos los pacientes a su nueva unidad
            for paciente, destino in decision.items():
                if self.agregar_paciente(paciente, destino["hospital"], destino["unidad"]):
                    pass
                else:
                    print(f"Error al agregar paciente {paciente.id} a h:{destino['hospital']}, u: {destino['unidad']}")
             
    def actualizar_tiempo(self): # Revisado, funciona bien
        self.hospital_1.actualizar_tiempo()
        self.hospital_2.actualizar_tiempo()
        self.hospital_3.actualizar_tiempo()
        self.wl.actualizar_tiempo()
        # Incrementar el tiempo del sistema
        self.T += 1

    def entregar_log_pacientes_terminados_como_data_frame(self): # Revisado, funciona bien
        t0 = time.time()
        log_completo = []
        for requerimiento in [1, 2, 3]:
            for grd in [1, 2, 3, 4, 5, 6, 7, 8]:
                for paciente in self.end.sub_listas[requerimiento][grd]:
                    contador = 0                    
                    for evento in paciente.log_eventos.copy():
                        contador += 1
                        evento["orden"] = contador
                        evento["requerimiento_inicial"] = paciente.requerimiento_inicial
                        log_completo.append(evento)
                    contador = 0

                for paciente in self.ps.sub_listas[requerimiento][grd]:
                    for evento in paciente.log_eventos.copy():
                        contador += 1
                        evento["orden"] = contador
                        evento["requerimiento_inicial"] = paciente.requerimiento_inicial
                        log_completo.append(evento)
                    
        # Convertir la lista de eventos a un DataFrame
        df_log = pd.DataFrame(log_completo)
        # Ordenar el DataFrame por ID y TI y TF
        df_log.sort_values(by=['ID', 'orden'], inplace=True)
        # Resetear el índice
        df_log.reset_index(drop=True, inplace=True)
        print(f"Log de pacientes terminado como DataFrame ({time.time() - t0:.2f} segundos)")
        return df_log

    def entregar_log_detallado_pacientes_terminados_como_data_frame(self): # En proceso
        t0 = time.time()

        def calcular_costo_espera(row):
            drg = row["MS_GRD"]
            los = row["LOS"]
            unidad = row.get("requerimiento_inicial", None)
            ubicacion = row["UBICACIÓN"]
            hospital_nombre = row["HOSPITAL"]
            hospital = p.dict_hospitales.get(hospital_nombre)

            # 1. Paciente en WL_WL (esperando en lista)
            if row["HOSPITAL"] == "WL" and ubicacion == "WL_WL":
                return p.dict_costo_espera_wl[drg][unidad] * los
                
            # 2. Paciente en GA o ED con LOS > 0
            elif row["UNIDAD"] in {"GA", "ED"} and los > 0:
                source = p.dict_costo_espera_ga if row["UNIDAD"] == "GA" else p.dict_costo_espera_ed
                return source[hospital][drg][unidad] * los
                
            # 3. Paciente hospitalizado y bloqueado
            elif row["UNIDAD"] in {"OR", "ICU", "SDU_WARD"} and "->" in ubicacion and los > 0:
                try:
                    origen_str, destino_str = ubicacion.split(" -> ")
                    unidad_actual = "_".join(origen_str.split("_")[2:])
                    unidad_requerida = "_".join(destino_str.split("_")[2:])
                    return p.dict_costo_espera_hospitalizado[hospital][drg][p.dict_unidades[unidad_actual]][p.dict_unidades[unidad_requerida]] * los
                except Exception:
                    return 0  # fallback in case of malformed UBICACION
            return 0

        def parse_hospital_number(hospital_str):
            return int(hospital_str.split("_")[1])

        log_completo = []
        for requerimiento in [1, 2, 3]:
            for grd in [1, 2, 3, 4, 5, 6, 7, 8]:
                pacientes = self.end.sub_listas[requerimiento][grd] + self.ps.sub_listas[requerimiento][grd]
                for paciente in pacientes:
                    contador = 0   
                    # for evento in paciente.log_eventos.copy():
                    tl = paciente.log_eventos.copy()
                    for i in range(len(tl) - 1):
                        evento = tl[i].copy()
                        contador += 1
                        evento["LOS"] = evento["TF"] - evento["TI"]
                        evento["COSTO DER WL"] = 0
                        evento["COSTO DER ED"] = 0
                        evento["COSTO TRASLADO"] = 0
                        evento["orden"] = contador
                        evento["requerimiento_inicial"] = paciente.requerimiento_inicial
                        evento["COSTO ESPERA"] = calcular_costo_espera(evento)
                        log_completo.append(evento)
                
                        row_current = evento.copy()
                        row_next = tl[i + 1]
                        time_gap = row_current['TF'] < row_next['TI']
                        time_gap_cero = row_current['TF'] == row_next['TI']
                        same_hospital = row_current['HOSPITAL'] == row_next['HOSPITAL']

                        new_row = {
                                'ID': row_current['ID'],
                                'MS_GRD': row_current['MS_GRD'],
                                'UBICACIÓN': f"{row_current['UBICACIÓN']} -> {row_next['UBICACIÓN']}",
                                'TI': row_current['TF'],
                                'TF': row_next['TI'],
                                'LOS': row_next['TI'] - row_current['TF'],
                                'HOSPITAL': row_current['HOSPITAL'],
                                'orden': row_current['orden'] + 0.1,  # Ajustar el orden
                                'requerimiento_inicial': row_current['requerimiento_inicial']
                        }
                        
                        if time_gap:
                            new_row.update({
                                'UNIDAD': row_current['UNIDAD']
                            })
                            
                            costo_espera = calcular_costo_espera(new_row)

                            new_row.update({
                                "COSTO DER WL": 0,
                                "COSTO DER ED": 0,
                                "COSTO TRASLADO": 0,
                                "COSTO ESPERA": costo_espera
                            })

                            log_completo.append(new_row)
                        
                        elif time_gap_cero and not same_hospital:
                            x = new_row.copy()
                            traslados = {
                                'Hospital_1_ED -> Hospital_2_ED',
                                'Hospital_1_ED -> Hospital_3_ED',
                                'Hospital_2_ED -> Hospital_1_ED',
                                'Hospital_2_ED -> Hospital_3_ED',
                                'Hospital_3_ED -> Hospital_1_ED',
                                'Hospital_3_ED -> Hospital_2_ED'
                            }
                            costo_der_wl = p.dict_costo_derivar_wl[x["MS_GRD"]][x["requerimiento_inicial"]] if x["UBICACIÓN"] == "WL_WL -> PS_PS" else 0
                            costo_der_ed = p.dict_costo_derivar_ed[p.dict_hospitales[x["HOSPITAL"]]][x["MS_GRD"]][x["requerimiento_inicial"]] if x["UBICACIÓN"] == f"{x['HOSPITAL']}_ED -> PS_PS" else 0
                            costo_traslado = (p.dict_costo_traslado[parse_hospital_number(x["UBICACIÓN"].split(" -> ")[0])]
                                              [parse_hospital_number(x["UBICACIÓN"].split(" -> ")[1])][x["MS_GRD"]][x["requerimiento_inicial"]]
                                            if x["UBICACIÓN"] in traslados else 0)

                            new_row.update({
                                'UNIDAD': "En movimiento",
                                "COSTO DER WL": costo_der_wl,
                                "COSTO DER ED": costo_der_ed,
                                "COSTO TRASLADO": costo_traslado,
                                "COSTO ESPERA": 0
                            })
                    
                            log_completo.append(new_row)
                    
                    evento = tl[-1].copy()
                    contador += 1
                    evento["LOS"] = evento["TF"] - evento["TI"]
                    evento["COSTO DER WL"] = 0
                    evento["COSTO DER ED"] = 0
                    evento["COSTO TRASLADO"] = 0
                    evento["COSTO ESPERA"] = 0
                    evento["orden"] = contador
                    evento["requerimiento_inicial"] = paciente.requerimiento_inicial
                    log_completo.append(evento)

        # Convertir la lista de eventos a un DataFrame
        df_log = pd.DataFrame(log_completo)
        # Ordenar el DataFrame por ID y TI y TF
        df_log.sort_values(by=['ID', 'orden'], inplace=True)
        df_log = df_log[['ID', 'MS_GRD', 'UBICACIÓN', 'TI', 'TF', 'LOS', 'HOSPITAL', 'UNIDAD', 'requerimiento_inicial', 'COSTO DER WL', 'COSTO DER ED', 'COSTO TRASLADO', 'COSTO ESPERA']]
        # Resetear el índice
        df_log.reset_index(drop=True, inplace=True)
        df_log[["TI", "TF", "LOS"]] = df_log[["TI", "TF", "LOS"]] * 12
        print(f"Log de pacientes terminado como DataFrame ({time.time() - t0:.2f} segundos)")
        return df_log

    def simular(self):
        t0 = time.time()
        self.T = 1  # Inicializa el tiempo del sistema en 1

        # Bucle principal de simulación
        while self.T <= self.T_max:
            if self.T % 1000 == 0:
                print(f"\nSimulando ciclo {self.T} de {self.T_max}")
            
            # Esto solo ocurre cuando quiero cambiar de modelo entremedio de la simulacion T!= 0
            if self.T == self.ciclo_de_cambio:
                self.modelo = self.modelo_alternativo
            
            # Agregar pacientes a la WL según el ciclo actual
            self.agregar_pacientes_ciclo_a_wl(self.T)

            # Agregar pacientes a las ED según el ciclo actual
            self.agregar_pacientes_ciclo_a_ed(self.T)

            # Entrego el estado de la simulación al modelo para tomar decisiones (argumento self)
            decisiones = self.modelo.tomar_decisiones(self)

            # Se implementan todas las decisiones del modelo
            self.implementar_decisiones(decisiones)

            # Actualizar el tiempo de cada unidad y paciente
            self.actualizar_tiempo()
            
        # Al finalizar la simulación, se entregan los logs de los pacientes terminados
        print(f"Simulación finalizada en ({time.time() - t0:.2f} segundos)")
        if self.log_detallado:
            return self.entregar_log_detallado_pacientes_terminados_como_data_frame()
        else:
            return self.entregar_log_pacientes_terminados_como_data_frame()
        
    def __str__(self):
        pass

