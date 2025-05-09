import re
from matplotlib.pylab import f
from numpy import average
import pandas as pd
import helpers
from parametros import dict_costo_derivar_wl, dict_drg, dict_unidades, dict_costo_derivar_ed, dict_hospitales

def lookup_cost(drg, unit_origin, hospital_origin=None,formula="average"):
    """
    Calcula el costo de derivar un paciente de un DRG específico al sistema privado,
    teniendo en cuenta el origen de la derivación y, si es necesario, el hospital.
    
    Args:
        drg (str): El DRG del paciente (por ejemplo, "DRG_1").
        origin (str): El origen de la derivación (por ejemplo, "WL", "ED").
        formula (str): La fórmula para calcular el costo. Por defecto es "average".
                       Otras opciones pueden ser implementadas en el futuro.
        hospital (str, optional): El hospital de origen (requerido si origin es "ED").
    
    Returns:
        float: El costo calculado según la fórmula especificada.
    """
    # Verificar si el DRG existe en el diccionario
    if drg not in dict_drg:
        raise ValueError(f"El DRG '{drg}' no está definido en los parámetros.")

    # Obtener la clave del DRG
    drg_key = dict_drg[drg]

    # Determinar el origen y seleccionar el diccionario de costos adecuado
    if unit_origin == "WL":  # Waiting List
        if drg_key not in dict_costo_derivar_wl:
            raise ValueError(f"No hay costos definidos para el DRG '{drg}' desde '{unit_origin}'.")
        costos = dict_costo_derivar_wl[drg_key].values()

    elif unit_origin == "ED":  # Emergency Department
        if hospital_origin is None:
            raise ValueError("El hospital debe especificarse para derivaciones desde 'ED'.")
        if hospital_origin not in dict_hospitales:
            raise ValueError(f"El hospital '{hospital_origin}' no está definido en los parámetros.")
        hospital_key = dict_hospitales[hospital_origin]
        if drg_key not in dict_costo_derivar_ed[hospital_key]:
            raise ValueError(f"No hay costos definidos para el DRG '{drg}' desde '{unit_origin}' en '{hospital_origin}'.")
        costos = dict_costo_derivar_ed[hospital_key][drg_key].values()

    else:
        raise ValueError(f"El origen '{unit_origin}' no está soportado.")

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
    filtered_df = dataframe[dataframe["DERIVACION"] == 1]
    individual_costs = []
    #go through each row and calculate the cost of derivation, for each derivation we have to find the origin, which is the ubicacion of the row where the id is the same and tf is equal to the ti of the row
    #and the ubicacion is not PS_PS and the id is the same
    total_cost = 0
    for index, row in filtered_df.iterrows():
        #get the id of the row
        id = row["ID"]
        #get the ti of the row
        ti = row["TI"]
        #get the ubicacion of the row
        ubicacion = row["UBICACIÓN"]
        #get the drg of the row
        drg = f"DRG_{int(row['MS_GRD'])}"
        
        #find the origin of the derivation
        origin_row = dataframe[(dataframe["ID"] == id) & (dataframe["TF"] == ti) & (dataframe["UBICACIÓN"] != "PS_PS")]
        print(index)
        if not origin_row.empty:
            #get the origin of the derivation
            unit_origin = origin_row.iloc[0]["UNIDAD"]
            hospital_origin = origin_row.iloc[0]["HOSPITAL"]

            #calculate the cost of derivation
            cost = lookup_cost(drg, unit_origin, hospital_origin)
            individual_costs.append([cost,id, ti,unit_origin,hospital_origin])
            total_cost += cost



    return total_cost, individual_costs

def daily_derivation_cost(dataframe,individual_costs):
    
    daily_costs = {}
    # calculate daily costs (24 hours).
    #for this we use the filtered_df and check if there are any rows with ti between 0 and 24,then for those rows we sum the cost of derivation and
    # that is the cost of derivation for that day, we keep going by 24 hour increments until the increment is greater than the tf of the maximum row in the main dataframe
    # get the maximum tf of the dataframe
    max_tf = dataframe["TF"].max()
    # get the minimum ti of the dataframe
    min_ti = dataframe["TI"].min()

    for i in range(min_ti, max_tf, 24):
        # get the items in the individual_costs list that have a ti between i and i+24
        daily_costs[i] = 0
        for cost in individual_costs:
            if cost[2] >= i and cost[2] < i + 24:
                daily_costs[i] += cost[0]

    average_daily_cost = sum(daily_costs.values()) / len(daily_costs)
    return average_daily_cost


        


def patients_derived_to_private_system(dataframe):
    filtered_df = helpers.lookup(dataframe, "DERIVACION", 1)
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

    # length of stay by unit
    units = helpers.unique_values(dataframe, "UNIDAD")
    for unit in units:
        unit_average_los = specific_average_length_of_stay(dataframe, "UNIDAD", unit)
        kpis[f"Average Length of Stay - {unit}"] = unit_average_los

    # length of stay by DRG
    drgs = helpers.unique_values(dataframe, "MS_GRD")
    for drg in drgs:
        drg_average_los = specific_average_length_of_stay(dataframe, "MS_GRD", drg)
        kpis[f"Average Length of Stay - {drg}"] = drg_average_los

    #cost of derivation
    total_cost = derivation_cost(dataframe)
    kpis["Total Cost of Derivation"] = total_cost[0]

    #daily average costs of derivation
    individual_costs = total_cost[1]
    average_daily_cost = daily_derivation_cost(dataframe, individual_costs)
    kpis["Average Daily Cost of Derivation"] = average_daily_cost
    

    #daily cost of derivation


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
    



