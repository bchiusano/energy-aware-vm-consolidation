from pathlib import Path
from vm_selection import LOWER_THRESHOLD, minimization_of_migrations
import pandas as pd

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


def sortDecreasingUtilization(vmList, total_vm_power):

    # Input: List of vm_ids and corresponding power usage, and total vm power for the node
    # Output: List of vm_ids sorted by decreasing load (as a percentage of total vm power)
    vmList['vm_load'] = vmList['vm_power'] / total_vm_power * 100
    sorted_vm_df = vmList.sort_values(by='vm_load', ascending=False)
    return sorted_vm_df['vm_id'].to_list(), sorted_vm_df['vm_power'].to_list(), sorted_vm_df['vm_load'].to_l



class VMConsolidation:
    def __init__(self, con, nodes, vms):
        self.con = con
        self.nodes = nodes
        self.vms = vms

    
    def host_detection(self, t, upper, lower):
        host_state = self.con.execute(open(SQL_DIR / "04_host_detection.sql").read(),
                                      [upper, lower, t]).df()
        
        overloaded = host_state[host_state["host_state"] == "overloaded"]
        underloaded = host_state[host_state["host_state"] == "underloaded"]

        overloaded['vm_loads'] = None
        underloaded['vm_loads'] = None

        for idx, row in overloaded.iterrows():
            # replace the original vm_ids and vm_powers with the sorted ones (and calculate vm load)
            vm_ids, vm_powers, vm_loads = sortDecreasingUtilization(
                pd.DataFrame({
                    'vm_id': row['vm_ids'],
                    'vm_power': row['vm_powers']
                }),
                row['total_vm_power']
            )

            overloaded.at[idx, 'vm_ids'] = vm_ids
            overloaded.at[idx, 'vm_powers'] = vm_powers
            overloaded.at[idx, 'vm_loads'] = vm_loads

        for idx, row in underloaded.iterrows():
            # replace the original vm_ids and vm_powers with the sorted ones (and calculate vm load)
            vm_ids, vm_powers, vm_loads = sortDecreasingUtilization(
                pd.DataFrame({
                    'vm_id': row['vm_ids'],
                    'vm_power': row['vm_powers']
                }),
                row['total_vm_power']
            )

            underloaded.at[idx, 'vm_ids'] = vm_ids
            underloaded.at[idx, 'vm_powers'] = vm_powers
            underloaded.at[idx, 'vm_loads'] = vm_loads

        print("OVERLOADED: ")
        print(overloaded)

        print("UNDERLOADED: ")
        print(underloaded)

        return overloaded, underloaded

        
    def vm_selection(self, underloaded, overloaded):
        vms_to_migrate = []

        # Underloaded nodes
        for _, row in underloaded.iterrows():
            if row["vm_count"] == 0:
                # TODO: should I put these nodes to sleep?
                continue
            
            for vm_id in row["vm_ids"]:
                vms_to_migrate.append({
                "vm_id": vm_id,
                "source_node": row["node_name"]
                })

        # Overloaded nodes
        for _, row in overloaded.iterrows():
            if row["vm_count"] == 0:
                continue
            
            vm_ids = row['vm_ids']
            vm_loads = row['vm_loads']
            host_util = row["cpu_usage_percent"]
            # Minimization of migrations policy

            if len(vm_ids) > 1:
                vms_to_migrate = minimization_of_migrations(vm_ids, vm_loads, host_util, vms_to_migrate, row)
            else:
                vms_to_migrate.append({
                    "vm_id": vm_ids[0],
                    "source_node": row["node_name"]
                })

        print("VMS to migrate")
        print(vms_to_migrate)
        return vms_to_migrate

    
    def vm_placement(self):
        print("VM Placement starts here - TODO")


if __name__ == "__main__":

    from preprocessing import con

    # load nodes and vms data from duckdb
    nodes = con.execute("SELECT * FROM node_snapshot").fetchdf()
    vms = con.execute("SELECT * FROM vm_final").fetchdf()

    vm_consolidation = VMConsolidation(con, nodes, vms)
    
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
    # show before consolidation
    #show_before_consolidation(vms)

    # host detection
    # TODO: maybe should calculate over/underloaded nodes and then iterate only through those timestamps?
    underutilized, overutilised = vm_consolidation.host_detection(t=t, upper=UPPER_THRESHOLD, lower=LOWER_THRESHOLD)

    # vm selection
    vms_to_migrate = vm_consolidation.vm_selection(underloaded=underutilized, overloaded=overutilised)

    # vm placement
    vm_consolidation.vm_placement()

    # show after consolidation
    #show_after_consolidation(vms)
