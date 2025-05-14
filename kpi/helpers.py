import os

def select_timelog(path):
    timelogs = [f for f in os.listdir(path) if f.endswith('.csv')]
    print("Select the timelog you want to analyze:")
    for i, timelog in enumerate(timelogs):
        print(f"{i + 1}. {timelog}")
    selected_timelog = int(input("Enter the number of the timelog: ")) - 1
    timelog_path = os.path.join(path, timelogs[selected_timelog])
    print(f"You selected: {timelogs[selected_timelog]}")
    return timelog_path

def lookup(df, column, value):
    return df[df[column] == value]

def unique_values(df, column):
    return df[column].unique()

def select_kpis():
    print("Select the KPIs you want to calculate:")
    print("0. All KPIs")
    print("1. Average LOS")
    print("2. Average LOS by hospital")
    print("3. Average LOS by unit")
    print("4. Average LOS by DRG")
    print("5. Total Cost of Derivation")
    print("6. Average Daily Cost of Derivation")
    print("7. Percentage of Patients Derived to Private System")
    print("8. Occupancy Rate")
    
    selected_kpis = input("Enter the numbers of the KPIs you want to calculate (comma separated): ")
    selected_kpis = [int(kpi) for kpi in selected_kpis.split(",")]
    
    return selected_kpis