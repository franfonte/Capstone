from hmac import new
from operator import ne
import pandas as pd
import numpy as np
from scipy import special, stats
import matplotlib.pyplot as plt


def timelog_to_dataframe(timelog_path):
    dataframe = pd.read_csv(timelog_path)
    return dataframe

def add_length_of_stay(dataframe):
    # Agrego LOS a cada fila
    dataframe["LOS"] = dataframe["TF"] - dataframe["TI"]
    return dataframe

def add_transition_rows(dataframe):
    new_rows = []
    for i in range(len(dataframe) - 1):
        row_current = dataframe.iloc[i]
        # get the next row
        row_next = dataframe.iloc[i + 1]

        same_id = row_current['ID'] == row_next['ID']
        same_ms = row_current['MS_GRD'] == row_next['MS_GRD']
        time_gap = row_current['TF'] < row_next['TI']
        same_hospital = row_current['HOSPITAL'] == row_next['HOSPITAL']

        if same_id and same_ms and time_gap:
            # Crear fila intermedia
            new_row = {
                'ID': row_current['ID'],
                'MS_GRD': row_current['MS_GRD'],
                'UBICACIÓN': f"{row_current['UBICACIÓN']} -> {row_next['UBICACIÓN']}",
                'TI': row_current['TF'],
                'TF': row_next['TI'],
                'LOS': row_next['TI'] - row_current['TF'],
                'HOSPITAL': row_current['HOSPITAL'],
                'UNIDAD': row_current['UNIDAD']
            }
            new_rows.append((i + 1, new_row))  # guardar con índice de inserción
    
    new_rows_list = [fila[1] for fila in new_rows]

    # Convertir todo a un DataFrame una sola vez
    new_rows_df = pd.DataFrame(new_rows_list)

    # Concatenar en una sola pasada
    dataframe = pd.concat([dataframe, new_rows_df], ignore_index=True)

    # Reordenar filas para meter filas entremedio
    dataframe = dataframe.sort_values(["ID", "TI"])

    # Resetear index pra que se vea ordenado
    dataframe = dataframe.reset_index(drop=True)

    return dataframe

def process_timelog(timelog_path):
    # Load the timelog
    dataframe = timelog_to_dataframe(timelog_path)
    
    # Add length of stay
    dataframe = add_length_of_stay(dataframe)
    
    # Add transition rows
    dataframe = add_transition_rows(dataframe)
    
    return dataframe


            
        