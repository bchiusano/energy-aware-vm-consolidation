CREATE OR REPLACE TABLE node_snapshot AS

SELECT
    n.timestamp,
    n.node_name,

    -- Telemetry
    n.cpu_usage_percent,
    n.ipmi_system_power_watts,

    -- Capacities
    n.total_threads AS cpu_capacity,
    n.rated_power_usable AS power_capacity,
    --n.memory_size_gb * 1024 AS memory_capacity_mb,
    (n.memory_total_bytes / (1024.0 * 1024.0)) AS memory_capacity_mb,
    (n.memory_free_bytes / (1024.0 * 1024.0)) AS memory_available_mb,

    -- Host state
    CASE
        WHEN n.cpu_usage_percent > ? THEN 'overloaded'
        WHEN n.cpu_usage_percent < ? THEN 'underloaded'
        ELSE 'normal'
    END AS host_state,

    -- VM info
    COUNT(v.vm_id) AS vm_count,

    --LIST(v.vm_id ORDER BY v.vm_power DESC) AS vm_ids,
    --LIST(v.vm_cpu ORDER BY v.vm_power DESC) AS vm_cpus,
    --LIST(v.vm_memory_mb ORDER BY v.vm_power DESC) AS vm_memories_mb,
    --LIST(v.vm_power ORDER BY v.vm_power DESC) AS vm_powers,

    -- Dynamic allocated resources
    COALESCE(SUM(v.vm_power), 0)
        AS vm_power_allocated,

    COALESCE(SUM(v.vm_cpu), 0)
        AS cpu_allocated,

    COALESCE(SUM(v.vm_memory_mb), 0)
        AS memory_allocated_mb,

    -- Baseline node power
    (
        n.ipmi_system_power_watts
        - COALESCE(SUM(v.vm_power), 0)
    ) AS baseline_power,

    -- Initial simulated power
    n.ipmi_system_power_watts
        AS simulated_power

FROM nodes_table n

LEFT JOIN vm_final v
    ON n.timestamp = v.timestamp
    AND n.node_name = v.hypervisor_name

GROUP BY
    n.timestamp,
    n.node_name,
    n.cpu_usage_percent,
    n.ipmi_system_power_watts,
    n.total_threads,
    n.rated_power_usable,
    --n.memory_size_gb;
    n.memory_total_bytes,      
    n.memory_free_bytes;