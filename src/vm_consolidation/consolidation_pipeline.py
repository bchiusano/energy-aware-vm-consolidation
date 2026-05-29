import pandas as pd
from vm_selection import select_underloaded_vms
#from vm_placement import bfd_placement
from vm_placement_target_groups import bfd_placement
from tqdm import tqdm
from pathlib import Path

def host_detection(host_state):
    
    overloaded = host_state[host_state["host_state"] == "overloaded"]
    underloaded = host_state[host_state["host_state"] == "underloaded"]
    targets = host_state[host_state["host_state"] == "normal"]



    #print(f"Overloaded hosts: {len(overloaded)}", f"Underloaded hosts: {len(underloaded)}", f"Target hosts: {len(targets)}")

    return overloaded, underloaded, targets

    
def vm_selection(underloaded, overloaded, upper_threshold, policy):
    
    #print("in vm selection")
    underloaded_vms = select_underloaded_vms(underloaded=underloaded)
    overloaded_vms = policy(overloaded=overloaded, UPPER_THRESHOLD=upper_threshold)
    #print(f"VMs to migrate from overloaded hosts: {len(overloaded_vms)}", overloaded_vms)
    return underloaded_vms + overloaded_vms


def vm_placement(migration_list, hosts, policy):
    #print("VM Placement starts here:")

    placements, failed_placements = bfd_placement(vms_to_migrate=migration_list, hosts=hosts, policy=policy)

    return placements, failed_placements


def update_host_state_after_migration(hosts, placements):
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

def save_results(simulated_frames, all_placements, all_failed_placements, OUTPUT_DIR, experiment):
    
    # create output directory if it doesn't exist
    output_dir = Path(f"{OUTPUT_DIR}/{experiment}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # with this after I can check if hosts are still overloaded or not
    print("Frames saved")
    simulated_df = pd.concat(simulated_frames, ignore_index=True)
    simulated_df.to_parquet(f'{output_dir}/simulated_{experiment}.parquet', index=False)

    # Saving placements - with this after I can check the VM migration frequency
    print("Placements saved")
    placements_df = pd.DataFrame(all_placements)
    placements_df.to_parquet(f'{output_dir}/placements_{experiment}.parquet', index=False)

    # Saving failed placements
    print("Failed placements saved")
    failed_placements_df = pd.DataFrame(all_failed_placements)
    failed_placements_df.to_parquet(f'{output_dir}/failed_placements_{experiment}.parquet', index=False)


def run_consolidation(timestamps, selection_policy, placement_policy, upper_threshold, name, con):

    # what to save for analysis
    simulated_frames = []
    all_placements = []
    all_failed_placements = []
    
    # example checking for the first 3 timestamps
    #n = len(timestamps)
    #start_idx = n // 2 - 1  # 1 before middle
    #timestamps = timestamps[start_idx:start_idx+1]

    for t, in tqdm(timestamps, desc="Processing timestamps"):
        
        host_df = con.execute(f"SELECT * FROM node_snapshot WHERE timestamp = '{t}'").df()

        # Fetch VMs for that timestamp and group by host
        vm_df = con.execute(f"""
            SELECT 
                hypervisor_name,
                hypervisor_group,
                vm_id, vm_cpu, vm_memory_mb, vm_power
            FROM vm_final
            WHERE timestamp = '{t}'
            ORDER BY hypervisor_name, vm_power DESC
        """).df()

        vms_by_host = {}
        for host, group in vm_df.groupby('hypervisor_name'):
            vms_by_host[host] = group[['vm_id', 'hypervisor_group', 'vm_cpu', 'vm_memory_mb', 'vm_power']].to_dict('records')

        # Now populate the host_df with this data
        host_df['vm_ids'] = host_df['node_name'].map(lambda x: [v['vm_id'] for v in vms_by_host.get(x, [])])
        host_df['vm_hypervisor_groups'] = host_df['node_name'].map(lambda x: [v['hypervisor_group'] for v in vms_by_host.get(x, [])])
        host_df['vm_cpus'] = host_df['node_name'].map(lambda x: [v['vm_cpu'] for v in vms_by_host.get(x, [])])
        host_df['vm_memories_mb'] = host_df['node_name'].map(lambda x: [v['vm_memory_mb'] for v in vms_by_host.get(x, [])])
        host_df['vm_powers'] = host_df['node_name'].map(lambda x: [v['vm_power'] for v in vms_by_host.get(x, [])])

        #print(host_df['vm_hypervisor_groups'])
        # new version of the host_df that I will mutate after placements
        simulated_df_at_t = host_df.copy(deep=True)
        
        # host detection
        overutilised, underutilized, placement_targets = host_detection(host_state=host_df)

        # vm selection
        vms_to_migrate = vm_selection(underloaded=underutilized, overloaded=overutilised, upper_threshold=upper_threshold, policy=selection_policy)

        # vm placement
        placements, failed_placements = vm_placement(migration_list=vms_to_migrate, hosts=placement_targets, policy=placement_policy)

        # Update
        simulated_df_at_t= update_host_state_after_migration(simulated_df_at_t, placements)

        # Save placements
        all_placements.extend(placements)

        # Save failed placements
        all_failed_placements.extend(failed_placements)

        # Save simulated frame
        simulated_frames.append(simulated_df_at_t)
    
    # Logs
    save_results(simulated_frames=simulated_frames, 
                 all_placements=all_placements, 
                 all_failed_placements=all_failed_placements, 
                 OUTPUT_DIR="results", 
                 experiment=name)