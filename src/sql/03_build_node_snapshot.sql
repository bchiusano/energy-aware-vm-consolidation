CREATE OR REPLACE TABLE node_snapshot AS

SELECT
    n.timestamp,
    n.node_name,
    n.node_group,

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
    --CASE
    --    WHEN n.cpu_usage_percent > ? THEN 'overloaded'
    --    WHEN n.cpu_usage_percent < ? THEN 'underloaded'
    --    ELSE 'normal'
    --END AS host_state,

    -- VM info
    COUNT(v.vm_id) AS vm_count,

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
    n.node_group,
    n.cpu_usage_percent,
    n.ipmi_system_power_watts,
    n.total_threads,
    n.rated_power_usable,
    n.memory_total_bytes,      
    n.memory_free_bytes;