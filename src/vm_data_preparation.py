import pandas as pd
import duckdb as ddb
from config import DATAPATH


def preprocess_missing_data(data, power_metric="scaphandre_vm_power_total_watts", group_col="vm_id"):

    # Forward filling involves replacing a missing value with the last observed value
    # if  power is NaN for a timestamp, forward fill per VM/NODE
    # instead of using backwards filling, we fill na with 0
    # could be that measurements are delayed or not recorded yet

    df = data.sort_values([group_col, "timestamp"])

    df["power_filled"] = (df.groupby(group_col)[power_metric].ffill())
    
    df["power_filled"] = df["power_filled"].fillna(0)

    return df


def construct_vm_list(vm_df):
    # at timestamp t, what VMs exist and where are they?
    # if a VM is not active at time t it does not appear in that group

    VMs_per_t = {}

    for t, group in vm_df.groupby("timestamp"):
        VMs_t = []

        for _, row in group.iterrows():
            vm = {
                "vm_id": row["vm_id"],
                "node_name": row["hypervisor_name"],
                "user_id": row["user_id"],
                "project_id": row["project_id"],
                "power": row["power_filled"],
                "vcpus": row["vcpus"],
                "memory": row["memory_MB"],
            }
            VMs_t.append(vm)

        VMs_per_t[t] = VMs_t

    return VMs_per_t


# TODO: not sure what to include for the node hardware
def construct_host_list(nodes_df):
    host_per_t = {}

    # a dicitonary with lists
    for t, group in nodes_df.groupby("timestamp"):
        host_t = []

        for _, row in group.iterrows():
            node = {
                "node_name": row["node_name"],
                "node_group": row["node_group"],
                "cpu_usage": row["cpu_usage_percent"],
                "memory_usage": row["memory_util_ratio"],
                "disk_usage": row["disk_util_ratio"],
                "power": row["impi_power_total_watts"],
            }
            host_t.append(node)

        host_per_t[t] = host_t
    
    return host_per_t



con = ddb.connect(':memory:')

VM_HARDWARE = "/Users/biancachiusano/Desktop/uva/thesis/Thesis/datasets/cloud_energy_consumption/vms/2024-12-14T000000Z_2025-04-13T235959Z/vms.csv"
VM_DATA = "/Users/biancachiusano/Desktop/uva/thesis/Thesis/datasets/cloud_energy_consumption/nodes-vms/2024-12-14T000000Z_2025-04-13T235959Z/**/*.csv"

NODE_HARDWARE = "../datasets/cloud_energy_consumption/node-groups/2024-12-14T000000Z_2025-04-13T235959Z/cleaned_node_groups.csv"

# VM HARDWARE 
con.query(f"""CREATE OR REPLACE TABLE vmhardware AS SELECT * FROM '{VM_HARDWARE}'""")

# VMs DATA
con.execute(f"""
                CREATE OR REPLACE VIEW vm_data AS
                SELECT *
                FROM read_csv_auto('{VM_DATA}',
                                filename=false,
                                union_by_name=true)
            """)

# merging vm hardware and vm data
con.execute("""
    CREATE OR REPLACE TABLE vm_merged AS
    SELECT 
        d.*, 
        h.*
    FROM vm_data d
    LEFT JOIN vmhardware h
    ON d.vm_id = h.vm_id
""")

vm_merged = con.execute("SELECT * FROM vm_merged").df()

# NODES HARDWARE
node_groups = pd.read_csv(f'{NODE_HARDWARE}')

# NODES DATA
nodes = pd.read_parquet(DATAPATH)

# preprocess missing data for power metric
vm_filled = preprocess_missing_data(vm_merged)
nodes_filled = preprocess_missing_data(nodes, power_metric="impi_power_total_watts", group_col="node_name")

# construct vm list and host list
vm_list = construct_vm_list(vm_filled)
host_list = construct_host_list(nodes_filled)