SELECT *,
    CASE
        WHEN cpu_usage_percent > ? THEN 'overloaded'
        WHEN cpu_usage_percent < ? THEN 'underloaded'
        ELSE 'normal'
    END AS host_state

FROM node_snapshot
WHERE timestamp = ?;