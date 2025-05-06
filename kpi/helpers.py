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
