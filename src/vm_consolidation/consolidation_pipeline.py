from pathlib import Path
import pandas as pd
from vm_selection import select_underloaded_vms, minimization_of_migrations
from vm_placement_debug import best_fit_placement
from tqdm import tqdm


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
        
        #print("in host detection")
        # these should already be sorted by decreasing vm power
        overloaded = host_state[host_state["host_state"] == "overloaded"]
        underloaded = host_state[host_state["host_state"] == "underloaded"]
        targets = host_state[host_state["host_state"] == "normal"]

        return overloaded, underloaded, targets

        
    def vm_selection(self, underloaded, overloaded):
        
        #print("in vm selection")
        underloaded_vms = select_underloaded_vms(underloaded=underloaded)
        overloaded_vms = minimization_of_migrations(overloaded=overloaded, UPPER_THRESHOLD=UPPER_THRESHOLD)

        return underloaded_vms + overloaded_vms

    
    def vm_placement(self, migration_list, hosts):
        #print("VM Placement starts here:")
        placements = best_fit_placement(vms_to_migrate=migration_list, hosts=hosts)
        #print("PLACEMENTS: ")
        #print(placements)
        return placements
    

    def update_host_state_after_migration(self, hosts, placements):
        # remove vms form source host and add to target host
        for placement in placements:
            
            source_idx = hosts[hosts["node_name"] == placement["source_node"]].index[0]
            target_idx = hosts[hosts["node_name"] == placement["target_node"]].index[0]
            
            # Remove VM resources from source host
            hosts.at[source_idx, "cpu_allocated"] -= placement["vm_cpu"]
            hosts.at[source_idx, "memory_allocated_mb"] -= placement["vm_memory_mb"]
            hosts.at[source_idx, "vm_power_allocated"] -= placement["vm_power"]

            # Add VM resources to target host
            hosts.at[target_idx, "cpu_allocated"] += placement["vm_cpu"]
            hosts.at[target_idx, "memory_allocated_mb"] += placement["vm_memory_mb"]
            hosts.at[target_idx, "vm_power_allocated"] += placement["vm_power"]

            # Recompute simulated power for both hosts
            hosts.at[source_idx, "simulated_power"] = (hosts.loc[source_idx, "baseline_power"]
                                                       + hosts.loc[source_idx, "vm_power_allocated"])
            hosts.at[target_idx, "simulated_power"] = (hosts.loc[target_idx, "baseline_power"]
                                                       + hosts.loc[target_idx, "vm_power_allocated"])
        
        # Detect empty hosts after migration and set simulated power to 0
        hosts.loc[hosts["vm_power_allocated"] <= 0, "simulated_power"] = 0
        
        return hosts



if __name__ == "__main__":

    from preprocessing import con

    vm_consolidation = VMConsolidation(con)
    
    simulated_frames = []
    
    timestamps = con.execute("""
        SELECT DISTINCT timestamp AT TIME ZONE 'UTC'
        FROM vm_final
        ORDER BY timestamp
    """).fetchall()
    
    # TODO: is it correct that I'm iterating through the vm_final timestamps? Should I be iterating through the node_snapshot timestamps instead? 
    for t, in tqdm(timestamps, desc="Processing timestamps"):
    
        #t = t + " UTC"
        #print("TIMESTAMP: " , t)

        # host detection - where placement_targets are the "normal" nodes in the host state
        host_df = con.execute(f"SELECT * FROM node_snapshot WHERE timestamp = '{t}'").df()

        # Fetch VMs for that timestamp and group by host
        vm_df = con.execute(f"""
            SELECT 
                hypervisor_name,
                vm_id, vm_cpu, vm_memory_mb, vm_power
            FROM vm_final
            WHERE timestamp = '{t}'
            ORDER BY hypervisor_name, vm_power DESC
        """).df()

        vms_by_host = {}
        for host, group in vm_df.groupby('hypervisor_name'):
            vms_by_host[host] = group[['vm_id', 'vm_cpu', 'vm_memory_mb', 'vm_power']].to_dict('records')

        # Now populate the host_df with this data
        host_df['vm_ids'] = host_df['node_name'].map(lambda x: [v['vm_id'] for v in vms_by_host.get(x, [])])
        host_df['vm_cpus'] = host_df['node_name'].map(lambda x: [v['vm_cpu'] for v in vms_by_host.get(x, [])])
        host_df['vm_memories_mb'] = host_df['node_name'].map(lambda x: [v['vm_memory_mb'] for v in vms_by_host.get(x, [])])
        host_df['vm_powers'] = host_df['node_name'].map(lambda x: [v['vm_power'] for v in vms_by_host.get(x, [])])

        # new version of the host_df that I will mutate after placements
        simulated_df_at_t = host_df.copy(deep=True)
        
        # host detection
        overutilised, underutilized, placement_targets = vm_consolidation.host_detection(host_state=host_df)

        # vm selection
        vms_to_migrate = vm_consolidation.vm_selection(underloaded=underutilized, overloaded=overutilised)

        # vm placement
        placements = vm_consolidation.vm_placement(migration_list=vms_to_migrate, hosts=placement_targets)

        # Update
        simulated_df_at_t= vm_consolidation.update_host_state_after_migration(simulated_df_at_t, placements)

        # Save
        simulated_frames.append(simulated_df_at_t)
    
    # Concatenate all simulated frames into a single DataFrame
    simulated_df = pd.concat(simulated_frames, ignore_index=True)
    simulated_df.to_parquet(f'{DATA_DIR}/processed/simulated_consolidation.parquet', index=False)
