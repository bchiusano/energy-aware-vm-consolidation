def select_underloaded_vms(underloaded):
    vms_to_migrate = []

    # Underloaded nodes
    for _, row in underloaded.iterrows():
        if row["vm_count"] == 0:
            continue

        #print("ROW: VMS", row["vm_ids"])
        # this should already be lists
        vm_ids = list(row["vm_ids"])
        vm_cpus = list(row["vm_cpus"])
        vm_memories_mb = list(row["vm_memories_mb"])
        vm_powers = list(row["vm_powers"])
        
        for i, vm_id in enumerate(vm_ids):
            vms_to_migrate.append({
            "vm_id": vm_id,
            "source_node": row["node_name"],
            "vm_cpu": vm_cpus[i],
            "vm_memory_mb": vm_memories_mb[i],
            "vm_power": vm_powers[i]
            })
    
    #print("VMS TO MIGRATE (UNDERLOADED): ", vms_to_migrate)
    #print("LENGTH: ", len(vms_to_migrate))
    return vms_to_migrate


def minimization_of_migrations(overloaded, UPPER_THRESHOLD):

    vms_to_migrate = []

    for _, row in overloaded.iterrows():

        if row["vm_count"] == 0:
            continue

        vm_ids = list(row["vm_ids"])
        vm_cpus = list(row["vm_cpus"])
        vm_memories_mb = list(row["vm_memories_mb"])
        vm_powers = list(row["vm_powers"])
        
        cpu_util = row["cpu_usage_percent"]

        total_vm_power = sum(vm_powers)

        # Estimate VM CPU shares proportionally
        vm_cpu_shares = []

        for power in vm_powers:

            if total_vm_power > 0:
                estimated_share = (
                    cpu_util * power / total_vm_power
                )
            else:
                estimated_share = 0

            vm_cpu_shares.append(estimated_share)

        while cpu_util > UPPER_THRESHOLD and vm_ids:

            overload = cpu_util - UPPER_THRESHOLD

            best_idx = None
            best_share = None

            # Smallest VM that resolves overload
            for i, share in enumerate(vm_cpu_shares):

                if share >= overload:

                    if best_share is None or share < best_share:
                        best_share = share
                        best_idx = i

            # Otherwise remove largest estimated share
            if best_idx is None:
                best_idx = vm_cpu_shares.index(
                    max(vm_cpu_shares)
                )
                best_share = vm_cpu_shares[best_idx]

            vms_to_migrate.append({
                "vm_id": vm_ids[best_idx],
                "source_node": row["node_name"],
                "vm_cpu": vm_cpus[best_idx],
                "vm_memory_mb": vm_memories_mb[best_idx],
                "vm_power": vm_powers[best_idx]
            })

            # Reduce estimated CPU utilization
            cpu_util -= best_share

            # Remove migrated VM
            vm_ids.pop(best_idx)
            vm_powers.pop(best_idx)
            vm_cpus.pop(best_idx)
            vm_memories_mb.pop(best_idx)
            vm_cpu_shares.pop(best_idx)

    #print("VMS TO MIGRATE (OVERLOADED): ", vms_to_migrate)
    #print("LENGTH: ", len(vms_to_migrate))
    return vms_to_migrate