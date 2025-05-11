import parametros
from matplotlib.pylab import f
from numpy import average
import pandas as pd
import helpers

def lookup_cost(drg, unit_origin, hospital_origin=None,formula="average"):
    # Verificar si el DRG existe en el diccionario
    if drg not in parametros.dict_drg:
        raise ValueError(f"El DRG '{drg}' no está definido en los parámetros.")

    # Obtener la clave del DRG
    drg_key = parametros.dict_drg[drg]

    # Determinar el origen y seleccionar el diccionario de costos adecuado
    if unit_origin == "WL":  # Waiting List
        if drg_key not in parametros.dict_costo_derivar_wl:
            raise ValueError(f"No hay costos definidos para el DRG '{drg}' desde '{unit_origin}'.")
        costos = parametros.dict_costo_derivar_wl[drg_key].values()

    elif unit_origin == "ED":  # Emergency Department
        if hospital_origin is None:
            raise ValueError("El hospital debe especificarse para derivaciones desde 'ED'.")
        if hospital_origin not in parametros.dict_hospitales:
            raise ValueError(f"El hospital '{hospital_origin}' no está definido en los parámetros.")
        hospital_key = parametros.dict_hospitales[hospital_origin]
        if drg_key not in parametros.dict_costo_derivar_ed[hospital_key]:
            raise ValueError(f"No hay costos definidos para el DRG '{drg}' desde '{unit_origin}' en '{hospital_origin}'.")
        costos = parametros.dict_costo_derivar_ed[hospital_key][drg_key].values()

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

def daily_cost(dataframe,individual_costs):
    
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
    
def occupancy_rate(dataframe):
    #from parameters import dict_capacidades
    max_capacities = parametros.dict_capacidades
    max_tf = dataframe["TF"].max()
    min_ti = dataframe["TI"].min()

    daily_ocuppancy = {}

    #i need to create a dictionary with the current capacity of each hospital and unit
    current_capacity = {}
    for hospital in max_capacities:
        current_capacity[hospital] = {}
        for unit in max_capacities[hospital]:
            current_capacity[hospital][unit] = []
            #initialize the current capacity to a list
    #add the waiting list as a hospital and the unit as WL
    current_capacity["WL"] = {}
    current_capacity["WL"]["WL"] = []
    #add the emergency department as a hospital and the unit as ED
    current_capacity["PS"] = {}
    current_capacity["PS"]["PS"] = []

    for i in range(min_ti, max_tf, 24):
        filtered_df = dataframe[(dataframe["TI"] >= i) & (dataframe["TF"] < i + 24)]
        for index, row in filtered_df.iterrows():
            # get the hospital and unit of the row
            hospital = row["HOSPITAL"]
            unit = row["UNIDAD"]
            if unit == "SDU_WARD":
                unit = "SDU/WARD"
            
            if hospital != "WL" and hospital != "PS":
                hospital = parametros.dict_hospitales[hospital]
                unit = parametros.dict_unidades[unit]
            id = row["ID"]

            # check if id is in the current capacity dictionary anywhere, not just in the hospital and unit
            for h in current_capacity:
                for u in current_capacity[h]:
                    if id in current_capacity[h][u]:
                        found = True
                        print(f"ID {id} found in {h} {u}")
                        current_capacity[h][u].remove(id)
                current_capacity[hospital][unit].append(id)

        # calculate the occupancy rate for each hospital and unit
        for hospital in current_capacity:
            for unit in current_capacity[hospital]:
                if hospital != "WL" and hospital != "PS":
                    # get the maximum capacity of the hospital and unit
                    max_capacity = max_capacities[hospital][unit]
                    # get the current capacity of the hospital and unit
                    current_capacity_count = len(current_capacity[hospital][unit])
                    # calculate the occupancy rate
                    occupancy_rate = (current_capacity_count / max_capacity) * 100
                    # add the occupancy rate to the dictionary
                elif hospital == "WL" or hospital == "PS":
                    occupancy_rate = 0
                if i not in daily_ocuppancy:
                    daily_ocuppancy[i] = {}
                if hospital not in daily_ocuppancy[i]:
                    daily_ocuppancy[i][hospital] = {}
                daily_ocuppancy[i][hospital][unit] = occupancy_rate
                

    # calculate the average occupancy rate for each hospital and unit
    average_occupancy_rate = {}
    for hospital in max_capacities:
        average_occupancy_rate[hospital] = {}
        for unit in max_capacities[hospital]:
            # get the occupancy rate for the hospital and unit
            occupancy_rate = 0
            count = 0
            for i in daily_ocuppancy:
                if hospital in daily_ocuppancy[i] and unit in daily_ocuppancy[i][hospital]:
                    occupancy_rate += daily_ocuppancy[i][hospital][unit]
                    count += 1
            if count > 0:
                occupancy_rate /= count
            average_occupancy_rate[hospital][unit] = occupancy_rate
    # calculate the average occupancy rate for each hospital
    for hospital in average_occupancy_rate:
        occupancy_rate = 0
        count = 0
        for unit in average_occupancy_rate[hospital]:
            occupancy_rate += average_occupancy_rate[hospital][unit]
            count += 1
        if count > 0:
            occupancy_rate /= count
        average_occupancy_rate[hospital] = occupancy_rate
    # calculate the average occupancy rate for the entire system
    occupancy_rate = 0
    count = 0
    for hospital in average_occupancy_rate:
        occupancy_rate += average_occupancy_rate[hospital]
        count += 1
    if count > 0:
        occupancy_rate /= count
    # return the average occupancy rate for the entire system
    return occupancy_rate, average_occupancy_rate

def calculate_kpis(dataframe, selected_kpis):

    # Initialize an empty dictionary to store the KPIs
    kpis = {}

    if 0 in selected_kpis:
        # Calculate all KPIs
        selected_kpis = [1, 2, 3, 4, 5, 6, 7, 8]

    if 1 in selected_kpis:
        average_los = average_length_of_stay(dataframe)
        kpis["Average Length of Stay"] = average_los

    if 2 in selected_kpis:
        hospitals = helpers.unique_values(dataframe, "HOSPITAL")
        for hospital in hospitals:
            hospital_average_los = specific_average_length_of_stay(dataframe, "HOSPITAL", hospital)
            kpis[f"Average Length of Stay - {hospital}"] = hospital_average_los

    if 3 in selected_kpis:
        units = helpers.unique_values(dataframe, "UNIDAD")
        for unit in units:
            unit_average_los = specific_average_length_of_stay(dataframe, "UNIDAD", unit)
            kpis[f"Average Length of Stay - {unit}"] = unit_average_los

    if 4 in selected_kpis:
        drgs = helpers.unique_values(dataframe, "MS_GRD")
        for drg in drgs:
            drg_average_los = specific_average_length_of_stay(dataframe, "MS_GRD", drg)
            kpis[f"Average Length of Stay - {drg}"] = drg_average_los

    if 5 in selected_kpis:
        total_cost = derivation_cost(dataframe)
        kpis["Total Cost of Derivation"] = total_cost[0]

    if 6 in selected_kpis:
        total_cost = derivation_cost(dataframe)
        individual_costs = total_cost[1]
        average_daily_cost = daily_cost(dataframe, individual_costs)
        kpis["Average Daily Cost of Derivation"] = average_daily_cost

    if 7 in selected_kpis:
        percentage, count = patients_derived_to_private_system(dataframe)
        kpis["Percentage of Patients Derived to Private System"] = percentage
        kpis["Count of Patients Derived to Private System"] = count

    if 8 in selected_kpis:
        overall_occupancy_rate, detailed_occupancy_rate = occupancy_rate(dataframe)
        kpis["Overall Occupancy Rate"] = overall_occupancy_rate
        kpis["Detailed Occupancy Rate"] = detailed_occupancy_rate

    print("KPIs:")
    for kpi, value in kpis.items():
        print(f"{kpi}: {value}")

    return kpis




