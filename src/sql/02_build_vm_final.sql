CREATE OR REPLACE TABLE vm_filled AS

SELECT *,
    LAST_VALUE(scaphandre_vm_power_total_watts IGNORE NULLS)
    OVER (
        PARTITION BY vm_id
        ORDER BY timestamp
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS power_filled

FROM vm_merged;

CREATE OR REPLACE TABLE vm_final AS
    SELECT *,
        COALESCE(power_filled, 0) AS power_clean
    FROM vm_filled;