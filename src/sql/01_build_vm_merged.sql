CREATE OR REPLACE TABLE vm_merged AS

SELECT
    d.timestamp,
    d.vm_id,
    d.hypervisor_name,
    d.hypervisor_group,
    d.scaphandre_vm_power_total_watts,

    h.user_id,
    h.project_id,
    h.vcpus,
    h.memory_MB,
    h.root_GB,
    h.ephemeral_GB

FROM vm_data d
LEFT JOIN vmhardware h
ON d.vm_id = h.vm_id;