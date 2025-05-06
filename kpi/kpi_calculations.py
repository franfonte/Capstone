
def average_length_of_stay(dataframe):
    #calculate the average length of stay in the system of a patient including waiting list
    
    #sum all the LOS column and divide by number of unique ids
    average_los = dataframe["LOS"].sum() / dataframe["ID"].nunique()
    #return the average length of stay
    return average_los



def calculate_kpis(dataframe):
    # Calculate the KPIs
    average_los = average_length_of_stay(dataframe)
    
    # Create a dictionary with the KPIs
    kpis = {
        "Average Length of Stay": average_los,
        # Add more KPIs here
    }
    return kpis

def print_kpis(kpis):
    # Print the KPIs
    print("KPIs:")
    for kpi, value in kpis.items():
        print(f"{kpi}: {value}")

