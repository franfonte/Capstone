from numpy import average
import data_processing
import helpers
import kpi_calculations
import os


timelogs_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'timelogs')


def main():
    selected_timelog_path = helpers.select_timelog(timelogs_folder_path)

    # Process the selected timelog
    print(f"Processing timelog: {selected_timelog_path}")
    dataframe = data_processing.process_timelog(selected_timelog_path)

    #ask user which kpis to calculate
    selected_kpis = helpers.select_kpis()
    

    kpis = kpi_calculations.calculate_kpis(dataframe,selected_kpis)


if __name__ == "__main__":
    main()
    

