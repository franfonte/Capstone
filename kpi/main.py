import data_processing
import helpers
import os


timelogs_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'timelogs')


def main():
    selected_timelog_path = helpers.select_timelog(timelogs_folder_path)
    # Process the selected timelog
    dataframe = data_processing.timelog_to_dataframe(selected_timelog_path)
    
    # Add length of stay to the dataframe
    data_processing.add_length_of_stay(dataframe)

    # Add transition rows to the dataframe
    dataframe = data_processing.add_transition_rows(dataframe)
    # Save the processed dataframe to a new CSV file    
    output_path = os.path.join(timelogs_folder_path, 'processed_timelog.csv')
    dataframe.to_csv(output_path, index=False)
    

if __name__ == "__main__":
    main()
    

