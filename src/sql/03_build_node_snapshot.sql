CREATE OR REPLACE TABLE node_snapshot AS

SELECT
    n.timestamp,
    n.node_name,
    n.cpu_usage_percent,
    n.ipmi_system_power_watts,

    COUNT(v.vm_id) AS vm_count,

    LIST(v.vm_id) AS vm_ids,
    LIST(v.power_clean) AS vm_powers,

    SUM(v.power_clean) AS total_vm_power

FROM nodes_table n

LEFT JOIN vm_final v
    ON n.timestamp = v.timestamp
    AND n.node_name = v.hypervisor_name

GROUP BY
    n.timestamp,
    n.node_name,
    n.cpu_usage_percent,
    n.ipmi_system_power_watts;