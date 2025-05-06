from numpy import average
import data_processing
import helpers
import kpi_calculations
import os


timelogs_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'timelogs')


def main():
    selected_timelog_path = helpers.select_timelog(timelogs_folder_path)

    # Process the selected timelog
    dataframe = data_processing.process_timelog(selected_timelog_path)

    
    

if __name__ == "__main__":
    main()
    

