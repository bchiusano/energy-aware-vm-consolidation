import random

def estimate_vm_demand(host_usage, vm_power, total_vm_power, vm_count):
    if total_vm_power <= 0:
        return host_usage / vm_count if vm_count > 0 else 0

    return host_usage * (vm_power/total_vm_power)


def estimate_vm_demands(host_usage, vm_powers):
    total_vm_power = sum(vm_powers)
    vm_count = len(vm_powers)

    return [
        estimate_vm_demand(host_usage, power, total_vm_power, vm_count)
        for power in vm_powers
    ]


def estimate_vm_cpu_shares(cpu_util, vm_powers):
    total_vm_power = sum(vm_powers)

    if total_vm_power <= 0:
        return [cpu_util / len(vm_powers) for _ in vm_powers] if vm_powers else []

    return [cpu_util * power / total_vm_power for power in vm_powers]


# For Underloaded nodes, select all VMs for migration
def select_underloaded_vms(underloaded):
    #print("Selecting VMs from underloaded hosts")
    vms_to_migrate = []

    for _, row in underloaded.iterrows():
        if row["vm_count"] == 0:
            continue

        vm_ids = list(row["vm_ids"])
        hypervisor_groups = list(row["vm_hypervisor_groups"])
        vm_cpus = list(row["vm_cpus"])
        vm_memories_mb = list(row["vm_memories_mb"])
        vm_powers = list(row["vm_powers"])

        host_cpu_usage = row["cpu_capacity"] * row["cpu_usage_percent"] / 100
        host_memory_usage = row["memory_capacity_mb"] - row["memory_available_mb"]

        vm_cpu_demands = estimate_vm_demands(host_cpu_usage, vm_powers)
        vm_memory_demands = estimate_vm_demands(host_memory_usage, vm_powers)
        
        for i, vm_id in enumerate(vm_ids):
            vms_to_migrate.append({
            "vm_id": vm_id,
            "source_node": row["node_name"],
            "hypervisor_group": hypervisor_groups[i],
            "vm_cpu": vm_cpus[i],
            "vm_memory_mb": vm_memories_mb[i],
            "vm_power": vm_powers[i],
            "vm_cpu_demand": vm_cpu_demands[i],
            "vm_memory_demand": vm_memory_demands[i]
            })
    
    return vms_to_migrate

# For overloaded nodes, select Random VMs until we are under the threshold
# Randomly select VMs until CPU utilization drops below UPPER_THRESHOLD
def random_choice_policy(overloaded, UPPER_THRESHOLD, seed=None):

    #print("Random Choice Policy")

    if seed is not None:
        random.seed(seed)

    vms_to_migrate = []

    for _, row in overloaded.iterrows():

        cpu_util = row["cpu_usage_percent"]
        host_cpu_usage = row["cpu_capacity"] * row["cpu_usage_percent"] / 100
        host_memory_usage = row["memory_capacity_mb"] - row["memory_available_mb"]

        if cpu_util <= UPPER_THRESHOLD:
            continue

        vm_ids = list(row["vm_ids"])
        hypervisor_groups = list(row["vm_hypervisor_groups"])
        vm_cpus = list(row["vm_cpus"])
        vm_memories_mb = list(row["vm_memories_mb"])
        vm_powers = list(row["vm_powers"])

        vm_cpu_demands = estimate_vm_demands(host_cpu_usage, vm_powers)
        vm_memory_demands = estimate_vm_demands(host_memory_usage, vm_powers)

        # estimate each VM contribution to host utilization
        vm_cpu_shares = estimate_vm_cpu_shares(cpu_util, vm_powers)

        while cpu_util > UPPER_THRESHOLD and vm_ids:

            idx = random.randrange(len(vm_ids))
            vms_to_migrate.append({
                "vm_id": vm_ids[idx],
                "source_node": row["node_name"],
                "hypervisor_group": hypervisor_groups[idx],
                "vm_cpu": vm_cpus[idx],
                "vm_memory_mb": vm_memories_mb[idx],
                "vm_power": vm_powers[idx],
                "vm_cpu_demand": vm_cpu_demands[idx],
                "vm_memory_demand": vm_memory_demands[idx]
            })

            # reduce estimated utilization
            cpu_util -= vm_cpu_shares[idx]

            # remove migrated VM
            vm_ids.pop(idx)
            hypervisor_groups.pop(idx)
            vm_cpus.pop(idx)
            vm_memories_mb.pop(idx)
            vm_powers.pop(idx)
            vm_cpu_demands.pop(idx)
            vm_memory_demands.pop(idx)
            vm_cpu_shares.pop(idx)

    return vms_to_migrate


# For overloaded nodes
def minimization_of_migrations(overloaded, UPPER_THRESHOLD):

    #print("Minimization of Migrations Policy")
    vms_to_migrate = []

    for _, row in overloaded.iterrows():

        if row["vm_count"] == 0:
            continue

        vm_ids = list(row["vm_ids"])
        hypervisor_groups = list(row["vm_hypervisor_groups"])
        vm_cpus = list(row["vm_cpus"])
        vm_memories_mb = list(row["vm_memories_mb"])
        vm_powers = list(row["vm_powers"])
        
        cpu_util = row["cpu_usage_percent"]
        host_cpu_usage = row["cpu_capacity"] * row["cpu_usage_percent"] / 100
        host_memory_usage = row["memory_capacity_mb"] - row["memory_available_mb"]

        vm_cpu_demands = estimate_vm_demands(host_cpu_usage, vm_powers)
        vm_memory_demands = estimate_vm_demands(host_memory_usage, vm_powers)

        # Estimate VM CPU shares proportionally
        vm_cpu_shares = estimate_vm_cpu_shares(cpu_util, vm_powers)

        while cpu_util > UPPER_THRESHOLD and vm_ids:
            
            vm_cpu_shares = estimate_vm_cpu_shares(cpu_util, vm_powers)
            
            overload = cpu_util - UPPER_THRESHOLD

            # new search
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
                "hypervisor_group": hypervisor_groups[best_idx],
                "vm_cpu": vm_cpus[best_idx],
                "vm_memory_mb": vm_memories_mb[best_idx],
                "vm_power": vm_powers[best_idx],
                "vm_cpu_demand": vm_cpu_demands[best_idx],
                "vm_memory_demand": vm_memory_demands[best_idx]
            })

            # Reduce estimated CPU utilization
            cpu_util -= best_share

            # Remove migrated VM
            vm_ids.pop(best_idx)
            hypervisor_groups.pop(best_idx)
            vm_powers.pop(best_idx)
            vm_cpus.pop(best_idx)
            vm_memories_mb.pop(best_idx)
            vm_cpu_demands.pop(best_idx)
            vm_memory_demands.pop(best_idx)
            vm_cpu_shares.pop(best_idx)

    return vms_to_migrate
