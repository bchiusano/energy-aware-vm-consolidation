import duckdb as ddb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "src/sql"
DATA_DIR = ROOT / "datasets/cloud_energy_consumption"

UPPER_THRESHOLD = 90
LOWER_THRESHOLD = 10

# DUCKDB IN-MEMORY DATABASE
# TODO: check if con is being passed properly 
con = ddb.connect(':memory:')

if not Path(f'{DATA_DIR}/processed/vm_final.parquet').exists():
    
    print("Preprocessing VM data...")

    VM_HARDWARE = DATA_DIR / "vms/2024-12-14T000000Z_2025-04-13T235959Z/vms.csv"
    VM_DATA = DATA_DIR / "nodes-vms/2024-12-14T000000Z_2025-04-13T235959Z/**/*.csv"

    # Import data into DuckDB
    con.execute(f"""CREATE OR REPLACE TABLE vmhardware AS SELECT * FROM '{VM_HARDWARE}'""")
    con.execute(f"""
                    CREATE OR REPLACE VIEW vm_data AS
                    SELECT *
                    FROM read_csv_auto('{VM_DATA}',
                                    filename=false,
                                    union_by_name=true)
                """)

    con.execute(open(SQL_DIR / "01_build_vm_merged.sql").read())
    con.execute(open(SQL_DIR / "02_build_vm_final.sql").read())
    
    # persist 
    con.execute(f"""
        COPY vm_final TO
        '{DATA_DIR}/processed/vm_final.parquet'
        (FORMAT PARQUET)
    """)

else:
    # import vm_final.parquet into duckdb
    #con.execute(f"""CREATE TABLE vm_final AS SELECT * FROM read_parquet('{DATA_DIR}/processed/vm_final.parquet')""")
    print("VM FINAL exists, creating view")
    con.execute(f"""CREATE OR REPLACE VIEW vm_final AS SELECT * FROM read_parquet('{DATA_DIR}/processed/vm_final.parquet')""")

if not Path(f'{DATA_DIR}/processed/node_snapshot.parquet').exists():

    print("Preprocessing Node Snapshot data...")

    NODES_FEATURES = DATA_DIR / "full_nodes_featurestwo.parquet"
    con.execute(f"""CREATE TABLE nodes_table AS SELECT * FROM read_parquet('{NODES_FEATURES}')""")

    # compute node_snapshot
    # Also calculates over/under utilised nodes
    con.execute(open(SQL_DIR / "03_build_node_snapshot.sql").read(), [UPPER_THRESHOLD, LOWER_THRESHOLD])

    # persist

    con.execute(f"""
        COPY (
            SELECT *
            FROM node_snapshot
            ORDER BY timestamp, node_name
        )
        TO '{DATA_DIR}/processed/node_snapshot.parquet'
        (FORMAT PARQUET)
    """)
else: 
    # import node_snapshot.parquet into duckdb
    #con.execute(f"""CREATE TABLE node_snapshot AS SELECT * FROM read_parquet('{DATA_DIR}/processed/node_snapshot.parquet')""")
    print("NODE SNAPSHOT exists, creating view")
    con.execute(f"""CREATE OR REPLACE VIEW node_snapshot AS SELECT * FROM read_parquet('{DATA_DIR}/processed/node_snapshot.parquet')""")
