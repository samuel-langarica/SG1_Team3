import pandas as pd
from typing import Dict, List, Tuple

def calculate_overall_production(factory, simulation_time: float) -> Tuple[int, float]:
    total_production = factory.total_produced
    production_rate = total_production / simulation_time
    return total_production, production_rate

def calculate_workstation_occupancy(factory, simulation_time: float) -> Dict[int, float]:
    occupancy_rates = {}
    for station in factory.stations:
        occupancy_rate = station.busy_time / simulation_time
        occupancy_rates[station.station_id] = occupancy_rate
    return occupancy_rates

def calculate_average_waiting_time(factory) -> Dict[int, float]:
    avg_waiting_times = {}
    for station in factory.stations:
        if station.station_id == 1:  # Skip first station as per requirements
            continue
        # Calculate number of waits by dividing total waiting time by average wait time
        if factory.num_waits > 0:
            avg_wait = station.total_waiting_time / factory.num_waits
        else:
            avg_wait = 0.0
        avg_waiting_times[station.station_id] = avg_wait
    return avg_waiting_times

def get_workstation_status_partition(factory, time_intervals: List[Tuple[float, float]]) -> Dict[int, Dict[str, float]]:
    status_partitions = {}
    
    for station in factory.stations:
        station_status = {
            'Operational': 0.0,
            'Down': 0.0,
            'Waiting for restock': 0.0
        }
        
        # Calculate total time in each state
        total_time = sum(end - start for start, end in time_intervals)
        
        # Calculate operational time (busy time)
        station_status['Operational'] = station.busy_time / total_time
        
        # Calculate downtime
        station_status['Down'] = station.total_downtime / total_time
        
        # Calculate waiting for restock time
        station_status['Waiting for restock'] = station.restocking_time / total_time
        
        status_partitions[station.station_id] = station_status
    
    return status_partitions
