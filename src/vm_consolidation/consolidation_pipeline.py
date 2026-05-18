from pathlib import Path
import pandas as pd
from vm_selection import select_underloaded_vms, minimization_of_migrations
from vm_placement import best_fit_placement


# helper functions for vm consolidation
# show before consolidation
# show after consolidation

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "src/sql"
DATA_DIR = ROOT / "datasets/cloud_energy_consumption"

UPPER_THRESHOLD = 90
LOWER_THRESHOLD = 10

# for testing purposes
TIMESTAMP = '2025-01-16 08:33:00'


# print or display the resource utilization of hosts at a specific time or date
# show the placement of vms on hosts at a specific time or date
# also print or display users, projects, images. 
def show_before_consolidation(vm_list):
    # some sort of visualisation
    pass

def show_after_consolidation(vm_list):
    # some sort of visualisation
    pass


class VMConsolidation:
    def __init__(self, con):
        self.con = con

    
    def host_detection(self, host_state):
        
        print("in host detection")
        # these should already be sorted by decreasing vm power
        overloaded = host_state[host_state["host_state"] == "overloaded"]
        underloaded = host_state[host_state["host_state"] == "underloaded"]
        targets = host_state[host_state["host_state"] == "normal"]

        return overloaded, underloaded, targets

        
    def vm_selection(self, underloaded, overloaded):
        
        print("in vm selection")
        underloaded_vms = select_underloaded_vms(underloaded=underloaded)
        overloaded_vms = minimization_of_migrations(overloaded=overloaded, UPPER_THRESHOLD=UPPER_THRESHOLD)

        return underloaded_vms + overloaded_vms

    
    def vm_placement(self, migration_list, hosts):
        print("VM Placement starts here:")
        placements = best_fit_placement(vms_to_migrate=migration_list, hosts=hosts)
        print("PLACEMENTS: ")
        print(placements)



if __name__ == "__main__":

    from preprocessing import con

    # load nodes and vms data from duckdb
    # TODO: not sure if this is needed 
    #nodes = con.execute("SELECT * FROM node_snapshot").fetchdf()
    #vms = con.execute("SELECT * FROM vm_final").fetchdf()

    vm_consolidation = VMConsolidation(con)
    
    '''
    timestamps = con.execute("""
        SELECT DISTINCT timestamp AT TIME ZONE 'UTC'
        FROM vm_final
        ORDER BY timestamp
    """).fetchall()
    
    for (t,) in timestamps:
    '''

    t = TIMESTAMP
    t = t + " UTC"
    print("TIMESTAMP: " , t)
        # show before consolidation
        #show_before_consolidation(vms)

    # host detection - where placement_targets are the "normal" nodes in the host state
    host_df = con.execute(f"SELECT * FROM node_snapshot WHERE timestamp = '{t}'").df()
    overutilised, underutilized, placement_targets = vm_consolidation.host_detection(host_state=host_df)

    print("UNDERUTILISED")
    print(underutilized.head(10))

    print("OVERUTILISED")
    print(overutilised.head(10))

    print("Targets:")
    print(placement_targets.head(10))

    # vm selection
    vms_to_migrate = vm_consolidation.vm_selection(underloaded=underutilized, overloaded=overutilised)

    # vm placement
    vm_consolidation.vm_placement(migration_list=vms_to_migrate, hosts=placement_targets)

    # TODO: when to update the source nodes (put them to sleep or new power)
    # TODO: might have to calculate the power and energy with the formula and then compare it to my measurements

        # show after consolidation
        #show_after_consolidation(vms)
