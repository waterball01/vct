import ijson
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import mplcursors
import seaborn as sns

def load_player_handles(players_file_path):
    """Load player handles from the players.json file and return a mapping of player ID to handle."""
    with open(players_file_path, 'r') as f:
        players_data = json.load(f)
    
    # Create a dictionary to map player IDs to player handles
    player_handles = {player['id']: player['handle'] for player in players_data}
    return player_handles

def process_json_file(file_path, platform_game_id, mapping_file_path, players_file_path):
    # Load the mapping data from the mapping file
    with open(mapping_file_path, 'r') as f:
        mapping_data = json.load(f)

    # Find the relevant participant mapping for the given platformGameId
    participant_mapping = None
    for game_data in mapping_data:
        if game_data['platformGameId'] == platform_game_id:
            participant_mapping = game_data['participantMapping']
            break

    if not participant_mapping:
        raise ValueError(f"platformGameId '{platform_game_id}' not found in mapping file.")

    # Load the player handles mapping
    player_handles = load_player_handles(players_file_path)

    # A dictionary to hold information about each player (kills, deaths, and positions)
    player_stats = defaultdict(lambda: {'kills': [], 'deaths': []})
    # A dictionary to hold the latest position of each player
    player_positions = {}
    round_number = None
    round_start_time = None
    last_event_time = None

    # Open the JSON file for reading
    with open(file_path, 'r') as f:
        # Parse through the file using ijson
        objects = ijson.items(f, 'item')
        roundStart = False
        for obj in objects:
            # Check if the object is a player
            if 'snapshot' in obj:
                for i in range(len(obj['snapshot']['players'])):
                    # Use the mapping to get the actual playerId from the participantMapping
                    player_index = str(obj['snapshot']['players'][i]['playerId']['value'])
                    player_id = participant_mapping.get(player_index)
                    player_handle = player_handles.get(player_id, "Unknown")  # Get the player handle or 'Unknown'

                    position = obj['snapshot']['players'][i]['aliveState']['position'] if 'aliveState' in obj['snapshot']['players'][i] else None
                    player_positions[player_handle] = position

            # Check if the object is a gamePhase event
            if 'gamePhase' in obj and obj['gamePhase']['phase'] == "IN_ROUND":
                round_number = obj['gamePhase']['roundNumber']
                roundStart = True

            # Check if the object is an eventTime update
            if 'metadata' in obj:
                last_event_time = obj['metadata']['eventTime']['omittingPauses']
                if roundStart:
                    round_start_time = last_event_time
                    roundStart = False

            # Check if the object has a damageEvent key
            if 'damageEvent' in obj:
                damage_event = obj['damageEvent']
                # Check if it's a kill event
                if damage_event.get('killEvent', False):
                    victim_index = str(damage_event['victimId']['value'])
                    causer_index = str(damage_event['causerId']['value'])

                    # Retrieve the actual player IDs using the participantMapping
                    victim_id = participant_mapping.get(victim_index)
                    causer_id = participant_mapping.get(causer_index)

                    # Retrieve the player handles using the loaded player_handles dictionary
                    victim_handle = player_handles.get(victim_id, "Unknown")
                    causer_handle = player_handles.get(causer_id, "Unknown")

                    # Retrieve the previous positions for the causer and victim
                    causer_position = player_positions.get(causer_handle)
                    victim_position = player_positions.get(victim_handle)

                    # Calculate the time in round for the kill/death if the round start time is available
                    time_in_round = None
                    if round_start_time is not None and last_event_time is not None:
                        time_in_round = float(last_event_time[:-1]) - float(round_start_time[:-1])

                    # Record kill and death with the position, time-in-round, and round number for the players involved
                    if causer_position:
                        player_stats[causer_handle]['kills'].append((damage_event, causer_position, time_in_round, round_number))
                    if victim_position:
                        player_stats[victim_handle]['deaths'].append((damage_event, victim_position, time_in_round, round_number))

    return player_stats

def plot_player_stats(player_stats):
    print(f"Found {len(player_stats)} players")
    for player_handle, stats in player_stats.items():
        # Extract positions, times, and round numbers for kills and deaths
        kill_positions = [(pos, time, round_num) for _, pos, time, round_num in stats['kills']]
        death_positions = [(pos, time, round_num) for _, pos, time, round_num in stats['deaths']]

        print(f"Player {player_handle} has {len(kill_positions)} kills and {len(death_positions)} deaths")
        
        if not kill_positions and not death_positions:
            continue

        # Plot kills and deaths
        plt.figure(figsize=(10, 5))
        kill_scatter = None
        death_scatter = None
        if kill_positions:
            kill_colors = ['orange' if kill[2] in {1, 13} else 'red' for kill in kill_positions]
            kill_scatter = plt.scatter([kill[0].get('x') for kill in kill_positions],
                                       [kill[0].get('y') for kill in kill_positions],
                                       color=kill_colors, alpha=0.7, label='Kills')
        if death_positions:
            death_colors = ['purple' if death[2] in {1, 13} else 'blue' for death in death_positions]
            death_scatter = plt.scatter([death[0].get('x') for death in death_positions],
                                        [death[0].get('y') for death in death_positions],
                                        color=death_colors, alpha=0.7, label='Deaths')

        plt.title(f"Player {player_handle} Kill/Death Positions")
        plt.xlabel('X Position')
        plt.ylabel('Y Position')

        # Add interactivity with mplcursors for hover info
        cursor = mplcursors.cursor(hover=True)

        @cursor.connect("add")
        def on_add(sel):
            idx = sel.index
            if sel.artist == kill_scatter:
                time_in_round = kill_positions[idx][1]
                round_num = kill_positions[idx][2]
                sel.annotation.set(text=f"Kill - Round: {round_num}, Time: {time_in_round:.2f}s" if time_in_round is not None else f"Kill - Round: {round_num}, No Time")
            elif sel.artist == death_scatter:
                time_in_round = death_positions[idx][1]
                round_num = death_positions[idx][2]
                sel.annotation.set(text=f"Death - Round: {round_num}, Time: {time_in_round:.2f}s" if time_in_round is not None else f"Death - Round: {round_num}, No Time")

        plt.show()

def get_player_handles(platform_game_id, mapping_file_path, players_file_path):
    # Load the mapping data from JSON file
    with open(mapping_file_path, 'r') as f:
        mapping_data = json.load(f)

    # Find the relevant mapping for the given platformGameId
    participant_mapping = None
    for game_data in mapping_data:
        if game_data['platformGameId'] == platform_game_id:
            participant_mapping = game_data['participantMapping']
            break

    if not participant_mapping:
        raise ValueError(f"platformGameId '{platform_game_id}' not found in mapping file.")

    # Load the player data from JSON file
    with open(players_file_path, 'r') as f:
        player_data = json.load(f)

    # Create a dictionary to map player IDs to handles
    player_handles = {}
    for player in player_data:
        player_id = player['id']
        handle = player['handle']
        if player_id in participant_mapping.values():
            player_handles[player_id] = handle

    return player_handles

def plot_player_stats_with_handles(player_stats, player_handles):
    print(f"Found {len(player_stats)} players")
    for player_id, stats in player_stats.items():
        # Extract positions, times, and round numbers for kills and deaths
        kill_positions = [(pos, time, round_num) for _, pos, time, round_num in stats['kills']]
        death_positions = [(pos, time, round_num) for _, pos, time, round_num in stats['deaths']]

        player_handle = player_handles.get(player_id, player_id)  # Fallback to player_id if handle is not found
        print(f"Player {player_handle} has {len(kill_positions)} kills and {len(death_positions)} deaths")

        if not kill_positions and not death_positions:
            continue

        # Plot kills and deaths
        plt.figure(figsize=(10, 5))
        kill_scatter = None
        death_scatter = None
        if kill_positions:
            kill_colors = ['orange' if kill[2] in {1, 13} else 'red' for kill in kill_positions]
            kill_scatter = plt.scatter([kill[0].get('x') for kill in kill_positions],
                                       [kill[0].get('y') for kill in kill_positions],
                                       color=kill_colors, alpha=0.7, label='Kills')
        if death_positions:
            death_colors = ['purple' if death[2] in {1, 13} else 'blue' for death in death_positions]
            death_scatter = plt.scatter([death[0].get('x') for death in death_positions],
                                        [death[0].get('y') for death in death_positions],
                                        color=death_colors, alpha=0.7, label='Deaths')

        plt.title(f"Player {player_handle} Kill/Death Positions")
        plt.xlabel('X Position')
        plt.ylabel('Y Position')

        # Add interactivity with mplcursors for hover info
        cursor = mplcursors.cursor(hover=True)

        @cursor.connect("add")
        def on_add(sel):
            idx = sel.index
            if sel.artist == kill_scatter:
                time_in_round = kill_positions[idx][1]
                round_num = kill_positions[idx][2]
                sel.annotation.set(text=f"Kill - Round: {round_num}, Time: {time_in_round:.2f}s" if time_in_round is not None else f"Kill - Round: {round_num}, No Time")
            elif sel.artist == death_scatter:
                time_in_round = death_positions[idx][1]
                round_num = death_positions[idx][2]
                sel.annotation.set(text=f"Death - Round: {round_num}, Time: {time_in_round:.2f}s" if time_in_round is not None else f"Death - Round: {round_num}, No Time")

        plt.legend()
        plt.show()

# Example usage

def plot_heatmap(player_stats):
    kpositions = []
    dpositions = []
    for stats in player_stats.values():
        kill_positions = [(pos, time, round_num) for _, pos, time, round_num in stats['kills']]
        death_positions = [(pos, time, round_num) for _, pos, time, round_num in stats['deaths']]
        kpositions.extend([(kill[0].get('x'), kill[0].get('y')) for kill in kill_positions])
        dpositions.extend([(death[0].get('x'), death[0].get('y'))  for death in death_positions])

    if kpositions:
        plt.figure(figsize=(10, 8))
        sns.kdeplot(x=[pos[0] for pos in kpositions], y=[pos[1] for pos in kpositions], cmap="Reds", fill=True, thresh=0)
        plt.title('Kill Density Heatmap')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.show()
    if dpositions:
        plt.figure(figsize=(10, 8))
        sns.kdeplot(x=[pos[0] for pos in dpositions], y=[pos[1] for pos in dpositions], cmap="Blues", fill=True, thresh=0)
        plt.title('Death Density Heatmap')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.show()

# Example Usage:

# Usage
file_path = '/Users/Ruhan/Desktop/val/game-changers/games/2022/val:7f95140c-d4bf-4803-827b-2128dfe24ff2.json'
platform_game_id = "val:7f95140c-d4bf-4803-827b-2128dfe24ff2"  # Sample platformGameId
mapping_file_path = "/Users/Ruhan/Desktop/val/game-changers/esports-data/mapping_data.json"
players_file_path = "/Users/Ruhan/Desktop/val/game-changers/esports-data/players.json"
player_stats = process_json_file(file_path, platform_game_id, mapping_file_path, players_file_path)
plot_heatmap(player_stats)
player_handles = get_player_handles(platform_game_id, mapping_file_path, players_file_path)
# plot_player_stats_with_handles(player_stats, player_handles)
plot_player_stats(player_stats)