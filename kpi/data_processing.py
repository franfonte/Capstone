from hmac import new
from operator import ne
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def timelog_to_dataframe(timelog_path):
    dataframe = pd.read_csv(timelog_path)
    return dataframe

def add_length_of_stay(dataframe):
    # Agrego LOS a cada fila
    dataframe["LOS"] = dataframe["TF"] - dataframe["TI"]
    # Reordeno columnas
    dataframe = dataframe[["ID", "MS_GRD", "UBICACIÓN", "TI", "TF", "LOS", "HOSPITAL", "UNIDAD"]]
    return dataframe

def add_transition_rows(dataframe):
    new_rows = []
    for i in range(len(dataframe) - 1):
        row_current = dataframe.iloc[i]
        row_next = dataframe.iloc[i + 1]

        # verify if there is a gap in time between the two rows
        if row_current["TF"] < row_next["TI"] and row_current["ID"] == row_next["ID"]:
            # calculate the gap
            gap = row_next["TI"] - row_current["TF"]
            # create a new row with the gap
            new_row = {
                "ID": row_current["ID"],
                "MS_GRD": row_current["MS_GRD"],
                "UBICACIÓN":f"{row_current['UBICACIÓN']} -> {row_next['UBICACIÓN']}",
                "TI": row_current["TF"],
                "TF": row_next["TI"],
                "LOS": row_next["TI"] - row_current["TF"],
                "HOSPITAL": row_current["HOSPITAL"],
                "UNIDAD": row_current["UNIDAD"]
            }
            new_rows.append(new_row)
    # create a new dataframe with the new rows
    new_rows_df = pd.DataFrame(new_rows)
    # concatenate the new rows with the original dataframe
    dataframe = pd.concat([dataframe, new_rows_df], ignore_index=True)
    # sort the dataframe by ID and TI
    dataframe = dataframe.sort_values(by=["ID", "TI"])
    # reset the index
    dataframe = dataframe.reset_index(drop=True)
    # remove duplicates
    dataframe = dataframe.drop_duplicates(subset=["ID", "TI", "TF"], keep="last")
    
            
    return dataframe 

def process_timelog(timelog_path):
    # Load the timelog
    dataframe = timelog_to_dataframe(timelog_path)
    
    # Add length of stay
    dataframe = add_length_of_stay(dataframe)
    
    # Add transition rows
    dataframe = add_transition_rows(dataframe)
    
    return dataframe


            
        