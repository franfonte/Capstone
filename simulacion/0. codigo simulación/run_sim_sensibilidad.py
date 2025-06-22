import os
import sys
import time
import json
import parametros as p
from clases import Simulacion, Paciente, ModeloProactivo  # o el modelo que uses
from kpis import calcular_kpis

if __name__ == "__main__":
    seed = int(sys.argv[1])
    hospital_id = int(sys.argv[2])
    unidad_nombre = sys.argv[3]
    delta = int(sys.argv[4])

    T_max = 4500
    ciclos = 4208
    ciclo_de_cambio = 0
    pacientes_caso_base = False
    log_detallado = True
    modelo_class = ModeloProactivo
    modelo_alternativo = None

    # Construir nombre de carpeta con cambio
    nombre_base = modelo_class.__name__
    nombre_alternativo = modelo_alternativo.__name__ if modelo_alternativo else "None"
    nombre_carpeta = f"{nombre_base}_T{T_max}_C{ciclos}_H{hospital_id}_{unidad_nombre}".replace("/", "_")
    nombre_sub_carpeta = f"{'+' if delta >= 0 else ''}{delta}"
    carpeta_base = os.path.join("resultados sensibilidad", nombre_carpeta, nombre_sub_carpeta)
    # carpeta_logs = os.path.join(carpeta_base, "logs")
    # carpeta_plots = os.path.join(carpeta_base, "plots")
    carpeta_kpis = os.path.join(carpeta_base, "kpis")
    # os.makedirs(carpeta_logs, exist_ok=True)
    # os.makedirs(carpeta_plots, exist_ok=True)
    os.makedirs(carpeta_kpis, exist_ok=True)

    # Aplicar cambio temporal a parametros.py
    id_unidad = p.dict_unidades[unidad_nombre]
    original = p.dict_capacidades[hospital_id][id_unidad]
    nueva = original + delta

    if nueva < 1:
        print(f"❌ Capacidad inválida (<1): H{hospital_id} {unidad_nombre}. Se omite simulación.")
        sys.exit(1)

    p.dict_capacidades[hospital_id][id_unidad] = nueva
    print(f"📌 Capacidad modificada en parámetros: H{hospital_id} {unidad_nombre} = {nueva}")

    # Reiniciar IDs y correr simulación
    Paciente.CONTADOR_ID = 1
    modelo = modelo_class()
    alternativo = modelo_alternativo() if modelo_alternativo else None

    simu = Simulacion(
        T_max, seed, ciclos,
        modelo=modelo,
        modelo_alternativo=alternativo,
        pacientes_caso_base=pacientes_caso_base,
        ciclo_de_cambio=ciclo_de_cambio,
        log_detallado=log_detallado
    )
    df = simu.simular()

    # Guardar CSV
    # nombre_csv = f"{seed}.csv"
    # df.to_csv(os.path.join(carpeta_logs, nombre_csv), index=False) # Dejo de guardarlos, generaba demasiado archivo

    # Calcular KPIs
    t0 = time.time()
    kpis = calcular_kpis(
        df,
        save_plot=False, # No guardo ni muestros los graficos porque son miles
        modelo=modelo,
        seed=seed,
        ciclos=ciclos,
        save_dir=None
    )
    print(f"✅ KPIs calculados en {time.time() - t0:.2f}s")

    # Guardar KPIs en JSON
    with open(os.path.join(carpeta_kpis, f"{seed}.json"), "w") as f:
        json.dump(kpis, f, indent=4)

    # Restaurar capacidad original
    p.dict_capacidades[hospital_id][id_unidad] = original
    print(f"🔄 Capacidad restaurada en parámetros: H{hospital_id} {unidad_nombre} = {original}")