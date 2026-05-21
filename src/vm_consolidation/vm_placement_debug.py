def best_fit_placement(vms_to_migrate, hosts):

    placements = []
    
    for vm in sorted(vms_to_migrate,
                     key=lambda x: x["vm_power"],
                     reverse=True):

        vm_memory = vm["vm_memory_mb"]
        vm_cpu = vm["vm_cpu"]
        vm_power = vm["vm_power"]
        
        #print(f"\n{'='*80}")
        #print(f"Placing VM {vm['vm_id']} (CPU: {vm_cpu}, Mem: {vm_memory}MB, Power: {vm_power}W)")
        #print(f"  Source: {vm['source_node']}")

        best_host = None
        best_remaining = float("inf")
        candidates = []

        for idx, host in hosts.iterrows():

            #print(f"  Evaluating host {host['node_name']}...")
            cpu_capacity = host["cpu_capacity"]
            cpu_allocated = host["cpu_allocated"]
            #print(f"CPU capacity: {cpu_capacity}, allocated: {cpu_allocated}")
            cpu_available = cpu_capacity - cpu_allocated
            # TODO: CHECK - for some reason cpu available is often zero
            
            memory_capacity = host["memory_capacity_mb"]
            memory_allocated = host["memory_allocated_mb"]
            memory_available = host["memory_available_mb"]
            #print(f"Memory capacity: {memory_capacity}MB, allocated: {memory_allocated}MB, available: {memory_available}MB")

            power_capacity = host["power_capacity"]
            power_baseline = host["baseline_power"]
            power_allocated = host['vm_power_allocated']
            power_available = power_capacity - power_baseline - power_allocated

            # Check constraints
            cpu_ok = vm_cpu <= cpu_available
            mem_ok = vm_memory <= memory_available
            power_ok = vm_power <= power_available

            if cpu_ok and mem_ok and power_ok:
                remaining_score = power_available - vm_power
                candidates.append((idx, host["node_name"], remaining_score))

                if remaining_score < best_remaining:
                    best_remaining = remaining_score
                    best_host = idx
            '''
            else:
                # Show why this host was rejected
                failures = []
                if not cpu_ok:
                    failures.append(f"CPU (need {vm_cpu}, have {cpu_available})")
                if not mem_ok:
                    failures.append(f"Memory (need {vm_memory}MB, have {memory_available}MB)")
                if not power_ok:
                    failures.append(f"Power (need {vm_power}W, have {power_available}W)")
                print(f"  ✗ {host['node_name']}: {', '.join(failures)}")
            '''

        if best_host is not None:
            target_name = hosts.loc[best_host, "node_name"]
            #print(f"\n  VALID target found for VM {vm['vm_id']} (CPU: {vm_cpu}, Mem: {vm_memory}MB, Power: {vm_power}W)")
            #print(f"\n  ✓ Selected: {target_name} (remaining power score: {best_remaining}W)")
            
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

        #else:
            #print(f"\n  ✗ No valid target found for VM {vm['vm_id']} (CPU: {vm_cpu}, Mem: {vm_memory}MB, Power: {vm_power}W)")

    return placements