import re
import pandas as pd
import helpers
from parametros import dict_costo_derivar_wl, dict_drg, dict_unidades

def lookup_cost(drg, formula="average"):
    """
    Calcula el costo de derivar un paciente de un DRG específico al sistema privado.
    
    Args:
        drg (str): El DRG del paciente (por ejemplo, "DRG_1").
        formula (str): La fórmula para calcular el costo. Por defecto es "average".
                       Otras opciones pueden ser implementadas en el futuro.
    
    Returns:
        float: El costo calculado según la fórmula especificada.
    """
    # Verificar si el DRG existe en el diccionario
    if drg not in dict_drg:
        raise ValueError(f"El DRG '{drg}' no está definido en los parámetros.")

    # Obtener los costos asociados al DRG
    drg_key = dict_drg[drg]
    if drg_key not in dict_costo_derivar_wl:
        raise ValueError(f"No hay costos definidos para el DRG '{drg}'.")

    costos = dict_costo_derivar_wl[drg_key].values()

    # Calcular el costo según la fórmula especificada
    if formula == "average":
        costo = sum(costos) / len(costos)
    else:
        raise ValueError(f"La fórmula '{formula}' no está implementada.")

    return costo


def average_length_of_stay(dataframe):
    #sum all the LOS column and divide by number of unique ids
    average_los = dataframe["LOS"].sum() / dataframe["ID"].nunique()
    return average_los

def specific_average_length_of_stay(dataframe, column, value, exact_match=True):
    #calculate the average length of stay for rows that match a specific value in a column
    #if exact_match is true, filter the dataframe by the column and value
    #else, filter the dataframe by the column and value using regex
    if exact_match:
        #filter the dataframe by the column and value
        filtered_df = helpers.lookup(dataframe, column, value)
    else:
        #filter the dataframe by the column and value using regex
        filtered_df = dataframe[dataframe[column].str.contains(value, regex=True)]

    average_los = filtered_df["LOS"].sum() / filtered_df["ID"].nunique()
    #return the average length of stay
    return average_los


def derivation_cost(dataframe):
    for i in range(len(dataframe)):
        # Get the current row
        current_row = dataframe.iloc[i]
    

    pass

def patients_derived_to_private_system(dataframe):
    filtered_df = helpers.lookup(dataframe, "UBICACIÓN", "PS_PS")
    count = filtered_df["ID"].nunique()
    percentage = (count / dataframe["ID"].nunique()) * 100
    return percentage,count
    
    


def calculate_kpis(dataframe):
    # Calculate the KPIs
    kpis = {}

    # Average length of stay
    average_los = average_length_of_stay(dataframe)
    kpis["Average Length of Stay"] = average_los
    

    # length of stay by hospital
    hospitals = helpers.unique_values(dataframe, "HOSPITAL")
    for hospital in hospitals:
        hospital_average_los = specific_average_length_of_stay(dataframe, "HOSPITAL", hospital)
        kpis[f"Average Length of Stay - {hospital}"] = hospital_average_los

    # percentage and count of patients derived to private system
    percentage, count = patients_derived_to_private_system(dataframe)
    kpis["Percentage of Patients Derived to Private System"] = percentage
    kpis["Count of Patients Derived to Private System"] = count

    return kpis

def print_kpis(kpis):
    # Print the KPIs
    print("KPIs:")
    for kpi, value in kpis.items():
        print(f"{kpi}: {value}")
    



