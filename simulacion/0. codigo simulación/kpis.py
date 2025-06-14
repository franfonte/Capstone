# Librerias necesarias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import parametros as p
import os
from scipy.stats import mode
import time

"""
KPIs:
1. LOS hospitalizado
2. LOS en lista de espera
3. Costo diario promedio (social y operativo)
4. Costo de desvíos a clínicas (operativo)
5. Costo de traslados entre hospitales (operativo)
6. Costo promedio por paciente (social mas operativo)
7. Tasa de entrada vs tasa de salida (entrada wl y ed, salida sdu o ps)
8. Tasa de ocupación de camas (grafico)
9. Average LOS
10. Average LOS by hospital
11. Average LOS by unit
12. Average LOS by DRG
13. Total Cost of Derivation
14. Average Daily Cost of Derivation
15. Percentage of Patients Derived to Private System
16. Occupancy Rate
"""

def filter_by_patient_activity_period(df, start_time=10000, end_time=40000):
    """
    Optimized: Filters a DataFrame to include only patients who were active (TI–TF overlap)
    during a specified time window.
    """
    if start_time is None and end_time is None:
        return df

    condition = pd.Series(True, index=df.index)
    if start_time is not None:
        condition &= df["TF"].values >= start_time
    if end_time is not None:
        condition &= df["TI"].values <= end_time

    return df[condition]

# 1. LOS hospitalizado
def compute_los_hospitalizado(df, start_time=10000, end_time=40000):
    valid_units = ['GA', 'ED', 'OR', 'ICU', 'SDU_WARD']
    hospitals = ['Hospital_1', 'Hospital_2', 'Hospital_3']

    # Step 0: Exclude patients who ever entered PS
    ps_patients = df[df['UNIDAD'] == 'PS']['ID'].unique()

    # Step 0: Base filtering — keep only relevant units and hospitals, and exclude PS patients
    df_filtered = df[
        (df['HOSPITAL'].isin(hospitals)) &
        (df['UNIDAD'].isin(valid_units)) &
        (~df['ID'].isin(ps_patients))
    ]

    # Step 1: Base filtering — keep only relevant hospital units
    df_filtered = df[
        (df['HOSPITAL'].isin(hospitals)) &
        (df['UNIDAD'].isin(valid_units))
    ]

    # Step 2: Identify patients active within the time window
    df_filtered = filter_by_patient_activity_period(df_filtered, start_time, end_time)

    # Step 3: Calculate averages

    # LOS per hospital and unit
    los_by_hospital_unit = (
        df_filtered
        .groupby(['HOSPITAL', 'UNIDAD'])['LOS']
        .mean()
        .round(2)
        .unstack(fill_value=None)
        .to_dict(orient='index')
    )

    # Step 1: sum LOS per patient per hospital
    patient_los = (
        df_filtered
        .groupby(['ID', 'HOSPITAL'])['LOS']
        .sum()
        .reset_index()
    )

    # Step 2: average across patients per hospital
    los_by_hospital = (
        patient_los
        .groupby('HOSPITAL')['LOS']
        .mean()
        .round(2)
        .to_dict()
    )

    # LOS per unit (across all hospitals)
    los_by_unit = (
        df_filtered
        .groupby('UNIDAD')['LOS']
        .mean()
        .round(2)
        .to_dict()
    )

    return {
        "por_hospital_y_unidad": los_by_hospital_unit,
        "promedio_por_hospital": los_by_hospital,
        "promedio_por_unidad": los_by_unit
    }

# 2. LOS en lista de espera
def compute_los_lista_espera_total(df, start_time=10000, end_time=40000):
    # Step 1: filter only rows where patient is in WL
    df_filtered = df[df['UNIDAD'] == 'WL']

    # Step 2: filter by activity between start_time and end_time
    df_filtered = filter_by_patient_activity_period(df_filtered, start_time, end_time)

    # Step 3: sum LOS in WL per patient
    los_by_patient = df_filtered.groupby('ID')['LOS'].sum()

    # Step 4: compute and return the average LOS
    return round(los_by_patient.mean(), 2) if not los_by_patient.empty else None

# 3. Costos
def compute_costo_diario_promedio(df, start_time=10000, end_time=40000):
    df = df.copy()

    # Filter by patient activity during the specified period
    df = filter_by_patient_activity_period(df, start_time, end_time)

    # Total time in hours
    total_hours = (end_time - start_time) if start_time is not None and end_time is not None else df["TF"].max() - df["TI"].min()
    
    ciclos = int(total_hours // 12)  # Integer number of 12-hour cycles
    if ciclos == 0:
        return {
            "social": 0, "derivaciones_wl": 0, "derivaciones_ed": 0,
            "traslados": 0, "operativo": 0, "total": 0
        }

    # Individual cost components
    costo_social = df["COSTO ESPERA"].sum()
    costo_wl = df["COSTO DER WL"].sum()
    costo_ed = df["COSTO DER ED"].sum()
    costo_traslados = df["COSTO TRASLADO"].sum()

    # Compute average cost per 12-hour cycle
    return {
        "social": round(costo_social / ciclos, 2),
        "derivaciones_wl": round(costo_wl / ciclos, 2),
        "derivaciones_ed": round(costo_ed / ciclos, 2),
        "traslados": round(costo_traslados / ciclos, 2),
        "operativo": round((costo_wl + costo_ed + costo_traslados) / ciclos, 2),
        "total": round((costo_social + costo_wl + costo_ed + costo_traslados) / ciclos, 2)
    }

# 4. Costo promedio por paciente
def compute_costo_promedio_paciente(df, start_time=10000, end_time=40000):
    df = df.copy()
    df = filter_by_patient_activity_period(df, start_time, end_time)

    total_pacientes = df["ID"].nunique()
    if total_pacientes == 0:
        return {
            "costo_social_promedio": 0,
            "costo_operativo_promedio": 0,
            "costo_total_promedio": 0
        }

    costo_social = df["COSTO ESPERA"].sum()
    costo_operativo = (
        df["COSTO DER WL"].sum() +
        df["COSTO DER ED"].sum() +
        df["COSTO TRASLADO"].sum()
    )

    return {
        "costo_social_promedio": round(costo_social / total_pacientes, 2),
        "costo_operativo_promedio": round(costo_operativo / total_pacientes, 2),
        "costo_total_promedio": round((costo_social + costo_operativo) / total_pacientes, 2)
    }

# 5. Tasas de entrada y salida
def compute_tasa_entrada_vs_salida(df, start_time=10000, end_time=40000):
    df = df.copy()
    df = filter_by_patient_activity_period(df, start_time, end_time)

    # Total time in 12-hour cycles
    total_hours = (end_time - start_time) if start_time is not None and end_time is not None else df["TF"].max() - df["TI"].min()
    ciclos = int(total_hours // 12)
    if ciclos == 0:
        return {
            "entradas_wl_por_ciclo": 0,
            "entradas_ed_por_ciclo": 0,
            "total_entradas_por_ciclo": 0,
            "salidas_ps_por_ciclo": 0,
            "salidas_sdu_por_ciclo": 0,
            "total_salidas_por_ciclo": 0,
            "ratio_salida_entrada": 0,
            "ratio_salida_entrada_sin_ps": 0
        }

    # First and last row per patient
    first_rows = df.groupby("ID").first()
    last_rows = df.groupby("ID").last()

    # Entradas
    entradas_wl = (first_rows["HOSPITAL"] == "WL").sum()
    entradas_ed = (first_rows["UNIDAD"] == "ED").sum()
    total_entradas = entradas_wl + entradas_ed

    # Salidas
    salidas_ps = (last_rows["UNIDAD"] == "PS").sum()
    salidas_sdu = (last_rows["UNIDAD"] == "SDU_WARD").sum()
    total_salidas = salidas_ps + salidas_sdu

    # Normalize everything per cycle
    return {
        "entradas_wl_por_ciclo": round(entradas_wl / ciclos, 2),
        "entradas_ed_por_ciclo": round(entradas_ed / ciclos, 2),
        "total_entradas_por_ciclo": round(total_entradas / ciclos, 2),
        "salidas_ps_por_ciclo": round(salidas_ps / ciclos, 2),
        "salidas_sdu_por_ciclo": round(salidas_sdu / ciclos, 2),
        "total_salidas_por_ciclo": round(total_salidas / ciclos, 2),
        "ratio_salida_entrada": round(total_salidas / total_entradas, 2) if total_entradas > 0 else 0,
        "ratio_salida_entrada_sin_ps": round(salidas_sdu / total_entradas, 2) if total_entradas > 0 else 0
    }

# 6. Tasa de ocupación de camas
def unit_counts_all_hospitals_fast(df, start_time=10000, end_time=40000, grid=False, show_plot=True, save_plot=False, save_path=None, detallado=True, modelo=None, seed=None, ciclos=None):
    tl = df.copy()
    step = 6
    hospitals = ["Hospital_1", "Hospital_2", "Hospital_3"]
    T_max = tl["TF"].max()
    times = np.arange(18, T_max + 1, step)
    i_start = start_time // step
    i_end = end_time // step

    tl["TI_bin"] = tl["TI"] // step
    tl["TF_bin"] = tl["TF"] // step

    result_dict = {}
    total_slots = len(times)
    plot_data = []

    def fast_mode(array):
        if len(array) == 0:
            return None
        vals, counts = np.unique(array, return_counts=True)
        return vals[np.argmax(counts)]

    def calcular_metricas(values):
        mean = np.mean(values)
        std = np.std(values)
        if detallado:
            return {
                "avg": round(mean, 2),
                "std": round(std, 2),
                "median": round(np.median(values), 2),
                "mode": int(fast_mode(values)) if len(values) > 0 else None
            }
        else:
            return f"{mean:.2f} ± {std:.2f}"

    # WL
    wl = tl[tl["UNIDAD"].str.contains("WL")]
    counts = np.zeros(total_slots, dtype=int)
    for s, e in zip(wl["TI_bin"], wl["TF_bin"]):
        np.add.at(counts, np.arange(s, min(e, total_slots)), 1)
    values = counts[i_start:i_end]
    result_dict["WL"] = calcular_metricas(values)
    if detallado:
        plot_data.append(("WL", counts, [("WL", np.mean(values), np.std(values))]))

    # Hospitales
    for hospital in hospitals:
        hosp_data = tl[tl["HOSPITAL"] == hospital]
        unit_labels = ["SDU/WARD", "ICU", "OR", "GA", "ED"]
        unit_match = {
            "SDU/WARD": hosp_data[hosp_data["UNIDAD"].str.contains("SDU|WARD")],
            "ICU": hosp_data[hosp_data["UNIDAD"] == "ICU"],
            "OR": hosp_data[hosp_data["UNIDAD"] == "OR"],
            "GA": hosp_data[hosp_data["UNIDAD"] == "GA"],
            "ED": hosp_data[hosp_data["UNIDAD"] == "ED"]
        }

        unit_data = {}
        plot_counts = []
        plot_labels = []

        for label in unit_labels:
            sub = unit_match[label]
            counts = np.zeros(total_slots, dtype=int)
            for s, e in zip(sub["TI_bin"], sub["TF_bin"]):
                np.add.at(counts, np.arange(s, min(e, total_slots)), 1)
            values = counts[i_start:i_end]
            unit_data[label] = calcular_metricas(values)
            if detallado:
                plot_counts.append(counts)
                plot_labels.append((label, np.mean(values), np.std(values)))

        result_dict[hospital] = unit_data
        if detallado:
            plot_data.append((hospital, plot_counts, plot_labels))

    # Crear save_path si es necesario
    if save_plot and not show_plot:
        if save_path is None and modelo and seed is not None and ciclos is not None:
            folder = "plots_ocupacion"
            os.makedirs(folder, exist_ok=True)
            filename = f"{modelo.__class__.__name__}_{seed}_{ciclos}_{T_max}.png"
            save_path = os.path.join(folder, filename)

    # ----- PLOT -----
    if detallado and (show_plot or save_plot):
        if grid:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
            axes = axes.flatten()

            for idx, (title, counts, labels) in enumerate(plot_data):
                if idx >= len(axes): break
                ax = axes[idx]
                if title == "WL":
                    label, mean, std = labels[0]
                    ax.plot(times, counts, label=f"{label} ({mean:.2f} ± {std:.2f})", color="black")
                else:
                    for unit_counts, (label, mean, std) in zip(counts, labels):
                        ax.plot(times, unit_counts, label=f"{label} ({mean:.2f} ± {std:.2f})")
                ax.axvspan(start_time, end_time, color='gray', alpha=0.2)
                ax.set_title(title)
                ax.set_ylabel("Personas")
                ax.grid(True)
                ax.legend(loc='center', bbox_to_anchor=(0.5, 0.6))

            for i in range(len(plot_data), 4):
                fig.delaxes(axes[i])

            fig.supxlabel("Horas")
            plt.tight_layout()

            if save_plot and not show_plot:
                fig.savefig(save_path)
            elif show_plot:
                plt.show()

            plt.close(fig)

        else:
            for title, counts, labels in plot_data:
                fig = plt.figure(figsize=(10, 5))
                if title == "WL":
                    label, mean, std = labels[0]
                    plt.plot(times, counts, label=f"{label} ({mean:.2f} ± {std:.2f})", color="black")
                else:
                    for unit_counts, (label, mean, std) in zip(counts, labels):
                        plt.plot(times, unit_counts, label=f"{label} ({mean:.2f} ± {std:.2f})")
                plt.axvspan(start_time, end_time, color="gray", alpha=0.2)
                plt.title(title)
                plt.xlabel("Horas")
                plt.ylabel("Personas")
                plt.grid(True)
                plt.legend(loc='center', bbox_to_anchor=(0.5, 0.6))
                plt.tight_layout()

                if save_plot and not show_plot:
                    name = title.replace(" ", "_")
                    save_name = save_path.replace(".png", f"_{name}.png")
                    plt.savefig(save_name)
                elif show_plot:
                    plt.show()

                plt.close(fig)

    return result_dict

def calcular_kpis(df, start_time=10000, end_time=40000, detallado=True, show_plot=False, save_plot=False, modelo=None, seed=None, ciclos=None, save_dir=None):
    kpis = {}
    kpis["LOS_hospitalizado"] = compute_los_hospitalizado(df, start_time, end_time)
    kpis["LOS_lista_espera"] = compute_los_lista_espera_total(df, start_time, end_time)
    kpis["costo_diario_promedio"] = compute_costo_diario_promedio(df, start_time, end_time)
    kpis["costo_promedio_paciente"] = compute_costo_promedio_paciente(df, start_time, end_time)
    kpis["tasa_entrada_vs_salida"] = compute_tasa_entrada_vs_salida(df, start_time, end_time)

    save_path = None
    if save_plot and save_dir and modelo and seed is not None and ciclos is not None:
        os.makedirs(save_dir, exist_ok=True)
        T_max = df["TF"].max()
        filename = f"{seed}.png"
        save_path = os.path.join(save_dir, filename)

    kpis["ocupaciones"] = unit_counts_all_hospitals_fast(
        df, start_time, end_time,
        detallado=detallado,
        show_plot=show_plot,
        save_plot=save_plot,
        modelo=modelo,
        seed=seed,
        ciclos=ciclos,
        save_path=save_path,
        grid=True
    )
    return kpis