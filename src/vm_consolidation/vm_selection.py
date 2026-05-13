def select_underloaded_vms(underloaded):
    vms_to_migrate = []

    # Underloaded nodes
    for _, row in underloaded.iterrows():
        if row["vm_count"] == 0:
            continue

        vm_ids = list(row["vm_ids"])
        vm_loads = list(row["vm_loads"])
        
        # TODO: check if vms and loads are corresponding to the same ids
        for i, vm_id in enumerate(vm_ids):
            vms_to_migrate.append({
            "vm_id": vm_id,
            "vm_load": vm_loads[i],
            "source_node": row["node_name"]
            })
    
    print("VMS TO MIGRATE (UNDERLOADED): ", vms_to_migrate)
    return vms_to_migrate


def minimization_of_migrations(overloaded, UPPER_THRESHOLD):

    vms_to_migrate = []

    print("UPPER_THRESH: ", UPPER_THRESHOLD)

    for _, row in overloaded.iterrows():

        if row["vm_count"] == 0:
            continue
        
        vm_ids = list(row["vm_ids"])
        print("VM_IDs: ", vm_ids)
        vm_loads = list(row["vm_loads"])
        print("VM_LOADs: ", vm_loads)

        cpu_util = row["cpu_usage_percent"]
        print("CPU UTIL START: ", cpu_util)

        while cpu_util > UPPER_THRESHOLD and vm_ids:

            overload = cpu_util - UPPER_THRESHOLD

            best_idx = None
            best_load = None

            # smallest VM that fixes overload
            for i, load in enumerate(vm_loads):

                if load >= overload:
                    print("load >= overload: ", load, " >= ", overload)
                    if best_load is None or load < best_load:
                        best_load = load
                        print("Best load: ", best_load)
                        best_idx = i

            # if none can fix overload alone,
            # migrate largest VM
            if best_idx is None:
                best_idx = vm_loads.index(max(vm_loads))
                print("BEST IDX IS NONE")
                best_load = vm_loads[best_idx]
                print("BEST LOAD; ", best_load)

            vm_id = vm_ids[best_idx]

            vms_to_migrate.append({
                "vm_id": vm_id,
                "vm_load": best_load,
                "source_node": row["node_name"]
            })

            cpu_util -= best_load

            vm_ids.pop(best_idx)
            vm_loads.pop(best_idx)

    print("VMS to migrate (FROM MM): ", vms_to_migrate)
    return vms_to_migrate