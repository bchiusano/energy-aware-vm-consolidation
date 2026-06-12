def calculate_total_energy_consumption(power_readings, time_intervals):
    """
    Calculate the total energy consumption based on power readings and time intervals.
    
    Parameters:
    power_readings (list of float): The power readings in watts.
    time_intervals (list of float): The time intervals in seconds corresponding to each power reading.
    
    Returns:
    float: The total energy consumption in watt-seconds (joules).
    """
    total_energy = 0.0
    for power, interval in zip(power_readings, time_intervals):
        total_energy += power * interval
    return total_energy


'''
Tradeoff plot

x-axis:

migrations

y-axis:

energy savings.

VERY good plot.
'''