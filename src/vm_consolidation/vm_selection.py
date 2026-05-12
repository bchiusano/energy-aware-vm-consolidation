
def minimization_of_migrations(vms, loads, cpu_util, vms_to_migrate, row, UPPER_THRESHOLD):
    
    best_fit_util = float('inf')
   
    while cpu_util > UPPER_THRESHOLD and vms:
        for i in range(len(vms)):
            if loads[i] > cpu_util - UPPER_THRESHOLD:
                util = loads[i] - cpu_util + UPPER_THRESHOLD
                print("NEW UTL:", util)
                if util < best_fit_util:
                    best_fit_util = util
                    best_fit_vm = vms[i]
        cpu_util -= best_fit_util
        print("CPU UTIL:", cpu_util)

        vms_to_migrate.append({
            "vm_id": best_fit_vm,
            "source_node": row["node_name"]
        })
        # remove the migrated vm from the list of vms and loads
        vms.remove(best_fit_vm)
        loads.remove(index=i)

    return vms_to_migrate