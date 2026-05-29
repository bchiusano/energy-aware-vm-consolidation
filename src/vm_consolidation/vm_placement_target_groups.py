def bfd_placement(vms_to_migrate, hosts, policy="power_bfd"):

    placements = []
    failed_placements = []
    
    # SORTING CHANGES BASED ON POLICY

    if policy == "power_bfd":
        vms = sorted(vms_to_migrate, key=lambda x: x["vm_power"], reverse=True)

    elif policy == "cpu_bfd":
        vms = sorted(vms_to_migrate, key=lambda x: x["vm_cpu"], reverse=True)

    else:
        vms = vms_to_migrate

    for vm in vms:

        #print("LEN HOSTS BEFORE: ", len(hosts))
        #print("vm hypervisor group: ", vm["hypervisor_group"])
        # only consider hosts in the same node/hypervisor group
        vm_hosts = hosts[hosts["node_group"] == vm["hypervisor_group"]]
        #print("HOSTS: ", vm_hosts)
        #print("LEN HOSTS AFTER: ", len(vm_hosts))

        vm_memory = vm["vm_memory_mb"]
        vm_cpu = vm["vm_cpu"]
        vm_power = vm["vm_power"]

        # Resource tracking
        insufficient_cpu = []
        insufficient_memory = []
        insufficient_power = []

        best_host = None
        best_remaining = float("inf")

        for idx, host in vm_hosts.iterrows():

            cpu_capacity = host["cpu_capacity"]
            cpu_allocated = host["cpu_allocated"]
            cpu_available = cpu_capacity - cpu_allocated
        

            memory_available = host["memory_available_mb"]

            power_capacity = host["power_capacity"]
            power_baseline = host["baseline_power"]
            power_allocated = host['vm_power_allocated']
            power_available = power_capacity - power_baseline - power_allocated

            # Check constraints
            cpu_ok = vm_cpu <= cpu_available
            mem_ok = vm_memory <= memory_available
            power_ok = vm_power <= power_available

            # TODO: this contraint may also change in the future
            if cpu_ok and mem_ok and power_ok:
                
                if policy == "power_bfd":
                    remaining_score = power_available - vm_power
                elif policy == "cpu_bfd":
                    remaining_score = cpu_available - vm_cpu

                if remaining_score < best_remaining:
                    #print("new best: ", idx)
                    best_remaining = remaining_score
                    best_host = idx
            else:
                # failed placement
                if not cpu_ok:
                    insufficient_cpu.append(host["node_name"])
                if not mem_ok:
                    insufficient_memory.append(host["node_name"])
                if not power_ok:
                    insufficient_power.append(host["node_name"])
    

        if best_host is not None:
            
            target_name = hosts.loc[best_host, "node_name"]

            
            placements.append({
                "vm_id": vm["vm_id"],
                "source_node": vm["source_node"],
                "target_node": target_name,
                "vm_power": vm_power,
                "vm_cpu": vm_cpu,
                "vm_memory_mb": vm_memory
            })

            # Update allocated resources 
            hosts.at[best_host, "cpu_allocated"] += vm["vm_cpu"]
            hosts.at[best_host, "memory_allocated_mb"] += vm["vm_memory_mb"]
            hosts.at[best_host, "vm_power_allocated"] += vm["vm_power"]
            hosts.at[best_host, "simulated_power"] = (
                hosts.loc[best_host, "baseline_power"]
                + hosts.loc[best_host, "vm_power_allocated"]
            )

        else:
            # no valid target found for this VM
            failed_placements.append({
                "vm_id": vm["vm_id"],
                "source_node": vm["source_node"],
                "vm_power": vm_power,
                "vm_cpu": vm_cpu,
                "vm_memory_mb": vm_memory,
                "insufficient_cpu_hosts": len(insufficient_cpu),
                "insufficient_memory_hosts": len(insufficient_memory),
                "insufficient_power_hosts": len(insufficient_power)
            })

    return placements, failed_placements