def best_fit_placement(vms_to_migrate, hosts):

    # This is power-aware BFD

    placements = []
    
    for vm in sorted(vms_to_migrate,
                     key=lambda x: x["vm_power"],
                     reverse=True):

        vm_memory = vm["vm_memory_mb"] # Memory_MB to allocate
        vm_cpu = vm["vm_cpu"]  # vCPUs to allocate
        vm_power = vm["vm_power"] # Power to allocate

        # DEBUGGGGGG    
        print(f"\n{'='*80}")
        print(f"Placing VM {vm['vm_id']} (CPU: {vm_cpu}, Mem: {vm_memory}MB, Power: {vm_power}W)")
        print(f"  Source: {vm['source_node']}")

        best_host = None
        best_remaining = float("inf")

        for idx, host in hosts.iterrows():
            ######## CPU ########
            cpu_capacity = host["cpu_capacity"]  # total threads (from node groups)
            cpu_allocated = host["cpu_allocated"]  # sum of vCPUs from VMs on this host
            cpu_available = cpu_capacity - cpu_allocated # cpu is not based on allocated vCPUs instead of runtime utilization
            
            ######## Memory ########
            memory_capacity = host["memory_capacity_mb"] # free memory in bytes during that timestamp
            memory_allocated = host["memory_allocated_mb"] # sum of memory from VMs on this host
            memory_available = memory_capacity - memory_allocated

            ######## Power ########
            power_capacity = host["power_capacity"]
            power_baseline = host["baseline_power"] # power_ipmi - power_allocated
            power_allocated = host['vm_power_allocated'] # sum of power from VMs on this host
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
            hosts.at[best_host, "memory_allocated_mb"] += vm["vm_memory_mb"] # sum of memory from VMs on this host
            hosts.at[best_host, "vm_power_allocated"] += vm["vm_power"]

            hosts.at[best_host, "simulated_power"] = (
                hosts.loc[best_host, "baseline_power"]
                + hosts.loc[best_host, "vm_power_allocated"]
            )

        else:
            print(f"No valid target found for VM {vm['vm_id']}")

    return placements