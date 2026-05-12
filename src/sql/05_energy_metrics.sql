-- =========================================
-- REAL SYSTEM ENERGY
-- =========================================

CREATE OR REPLACE VIEW real_energy AS

SELECT
    timestamp,
    node_name,
    ipmi_system_power_watts AS real_power

FROM node_snapshot;

-- =========================================
-- NODE BASELINE / OVERHEAD POWER
-- =========================================

CREATE OR REPLACE VIEW node_baseline_power AS

SELECT
    timestamp,
    node_name,

    ipmi_system_power_watts,
    total_vm_power,

    GREATEST(
        ipmi_system_power_watts - total_vm_power,
        0
    ) AS baseline_power

FROM node_snapshot;

-- =========================================
-- SIMULATED VM POWER PER NODE
-- =========================================

CREATE OR REPLACE VIEW simulated_node_power AS

SELECT
    p.timestamp,
    p.target_node AS node_name,

    SUM(v.power_clean) AS simulated_vm_power,
    COUNT(*) AS simulated_vm_count

FROM simulated_placements p

JOIN vm_final v
    ON p.timestamp = v.timestamp
    AND p.vm_id = v.vm_id

GROUP BY
    p.timestamp,
    p.target_node;


-- =========================================
-- ESTIMATED SIMULATED NODE POWER
-- =========================================

CREATE OR REPLACE VIEW simulated_total_power AS

SELECT
    s.timestamp,
    s.node_name,

    s.simulated_vm_power,

    b.baseline_power,

    CASE
        WHEN s.simulated_vm_count > 0
        THEN b.baseline_power + s.simulated_vm_power
        ELSE 0
    END AS estimated_power

FROM simulated_node_power s

LEFT JOIN node_baseline_power b
    ON s.timestamp = b.timestamp
    AND s.node_name = b.node_name;


-- =========================================
-- TOTAL ENERGY CONSUMPTION
-- =========================================

-- REAL ENERGY

CREATE OR REPLACE VIEW total_real_energy AS

SELECT
    SUM(real_power) AS total_real_power

FROM real_energy;


-- SIMULATED ENERGY

CREATE OR REPLACE VIEW total_simulated_energy AS

SELECT
    SUM(estimated_power) AS total_simulated_power

FROM simulated_total_power;

-- =========================================
-- ENERGY SAVINGS
-- =========================================

CREATE OR REPLACE VIEW energy_savings AS

SELECT
    r.total_real_power,
    s.total_simulated_power,

    r.total_real_power - s.total_simulated_power
        AS absolute_savings,

    100 * (
        r.total_real_power - s.total_simulated_power
    ) / r.total_real_power
        AS percent_savings

FROM total_real_energy r
CROSS JOIN total_simulated_energy s;


-- =========================================
-- ACTIVE NODES
-- =========================================
CREATE OR REPLACE VIEW active_nodes AS

SELECT
    timestamp,
    COUNT(*) AS active_node_count

FROM simulated_total_power
WHERE estimated_power > 0

GROUP BY timestamp;