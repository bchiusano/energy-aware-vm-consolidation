def best_fit_placement(vms_to_migrate, hosts):

    # This is power-aware BFD

    placements = []
    
    for vm in sorted(vms_to_migrate,
                     key=lambda x: x["vm_power"],
                     reverse=True):

        # TODO: make sure that vm and node memory use the same units (normalise everything to mb)
        vm_memory = vm["vm_memory"] # Memory_MB
        vm_cpu = vm["vm_cpu"]  # vCPUs to allocate
        vm_power = vm["vm_power"]

        best_host = None
        best_remaining = float("inf")

        for idx, host in hosts.iterrows():
            ######## CPU ########
            cpu_capacity = host["cpu_capacity"]  # total threads (from node groups)
            cpu_allocated = host["cpu_allocated"]  # sum of vCPUs from VMs on this host
            cpu_available = cpu_capacity - cpu_allocated # cpu is not based on allocated vCPUs instead of runtime utilization
            
            ######## Memory ########
            memory_available = host["memory_free_bytes"] # free memory in bytes during that timestamp

            ######## Power ########
            power_capacity = host["rated_power"]
            power_baseline = host["baseline_power"] # power_ipmi - power_allocated
            power_allocated = host['vm_total_power']
            power_available = power_capacity - power_baseline - power_allocated

            # Check all three constraints
            if (vm_cpu <= cpu_available and 
                vm_memory <= memory_available and 
                vm_power <= power_available):

                # This is what makes it power-aware: we want to minimize the remaining power capacity after placing the VM
                remaining_score = power_available - vm_power

                if remaining_score < best_remaining:
                    best_remaining = remaining_score
                    best_host = idx

        if best_host is not None:
            placements.append({
                "vm_id": vm["vm_id"],
                "source_node": vm["source_node"],
                "target_node": hosts.loc[best_host, "node_name"]
            })

            print("Placed VM", vm["vm_id"], "on", hosts.loc[best_host, "node_name"])

            # Update allocated resources 
            hosts.at[best_host, "cpu_allocated"] += vm["vm_cpu"]
            hosts.at[best_host, "memory_free_bytes"] -= vm["vm_memory"]
            hosts.at[best_host, "memory_allocated_bytes"] += vm["vm_memory"] # sum of memory from VMs on this host
            hosts.at[best_host, "power_allocated"] += vm["vm_power"]
            
            # Updating power
            hosts.at[best_host, "total_vm_power"] += vm["vm_power"]

            # TODO: add simulated power
            hosts.at[best_host, "simulated_power"] = (
                hosts.loc[best_host, "baseline_power"]
                + hosts.loc[best_host, "total_vm_power"]
            )

        else:
            print(f"No valid target found for VM {vm['vm_id']}")

    return placements