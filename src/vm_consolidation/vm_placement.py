def best_fit_placement(vms_to_migrate, hosts, UPPER_THRESHOLD):

    placements = []
    # TODO: check load vs power
    # for each vm that has to be migrated (sorted by vm load)
    for vm in sorted(vms_to_migrate,
                     key=lambda x: x["vm_load"],
                     reverse=True):

        best_host = None
        best_remaining = float("inf")

        for idx, host in hosts.iterrows():

            current_util = host["cpu_usage_percent"]
            # TODO: check this
            new_util = current_util + vm["vm_load"]

            if new_util <= UPPER_THRESHOLD:

                remaining = UPPER_THRESHOLD - new_util

                if remaining < best_remaining:
                    best_remaining = remaining
                    best_host = idx

        if best_host is not None:
            
            placements.append({
                "vm_id": vm["vm_id"],
                "source_node": vm["source_node"],
                "target_node": hosts.loc[best_host, "node_name"]
            })

            print("There is a best host: ", hosts.loc[best_host, "node_name"], "for vm: ", vm)

            # update host utilization
            hosts.at[best_host, "cpu_usage_percent"] += vm["vm_load"]

        else:
            print(f"No valid target found for VM {vm['vm_id']}")

    return placements