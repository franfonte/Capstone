# run_sim.py
import sys
import os
import time
import json
from clases import Simulacion, Paciente, ModeloA, ModeloProactivo, ModeloBase  # o el modelo que uses
from kpis import calcular_kpis

if __name__ == "__main__":
    seed = int(sys.argv[1])
    T_max = 4500
    ciclos = 4208
    ciclo_de_cambio = 0
    pacientes_caso_base = False
    log_detallado = True
    modelo_class = ModeloProactivo
    modelo_alternativo = None

    # Output folder
    nombre_base = modelo_class.__name__
    nombre_alternativo = modelo_alternativo.__name__ if modelo_alternativo else "None"
    # carpeta_base = f"resultados simulacion/{nombre_base}_{nombre_alternativo}_T{T_max}_C{ciclos}"
    carpeta_base = f"resultados simulacion/{nombre_base}_T{T_max}_C{ciclos}"
    carpeta_logs = os.path.join(carpeta_base, "logs")
    carpeta_plots = os.path.join(carpeta_base, "plots")
    carpeta_kpis = os.path.join(carpeta_base, "kpis")
    os.makedirs(carpeta_logs, exist_ok=True)
    os.makedirs(carpeta_plots, exist_ok=True)
    os.makedirs(carpeta_kpis, exist_ok=True)

    # Reiniciar IDs
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
    nombre_csv = f"{seed}.csv"
    df.to_csv(os.path.join(carpeta_logs, nombre_csv), index=False)

    # Calcular KPIs
    t0 = time.time()
    kpis = calcular_kpis(
        df,
        save_plot=True,
        modelo=modelo,
        seed=seed,
        ciclos=ciclos,
        save_dir=carpeta_plots
    )
    print(f"✅ KPIs calculados en {time.time() - t0:.2f}s")

    # Guardar KPIs en JSON
    with open(os.path.join(carpeta_kpis, f"{seed}.json"), "w") as f:
        json.dump(kpis, f, indent=4)