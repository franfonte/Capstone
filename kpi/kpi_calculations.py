import re
import pandas as pd
import helpers


def average_length_of_stay(dataframe):
    #calculate the average length of stay in the system of a patient including waiting list
    
    #sum all the LOS column and divide by number of unique ids
    average_los = dataframe["LOS"].sum() / dataframe["ID"].nunique()
    #return the average length of stay
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
    



