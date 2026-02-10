# IFCA Cloud energy consumption metrics

This dataset contains a snapshot of the energy consumption metrics for the
IFCA Cloud, a scientific cloud computing infrastructure located in Cantabria,
Spain. The data was collected over a period of four months, from December 14,
2024 to April 13, 2025.

# General Information

1. Title of Dataset: IFCA Cloud energy consumption metrics
2. Authors: Jaime Iglesias Blanco ([iglesias@ifca.unican.es](mailto:iglesias@ifca.unican.es)), Álvaro López García ([aloga@ifca.unican.es](mailto:aloga@ifca.unican.es))
3. Date of data collection: 14 December 2024 - 13 April 2025
4. Date of data publication on repository: May 2025
5. Geographic location of data collection: 43.47160739353177, -3.8022087210355364
6. Information about funding sources that supported the collection of the data: Greener Future Digital Research Infrastructures - GreenDIGIT (101131207), funded by the European Union under the Horizon Europe programme.
7. Recommended citation for this dataset: Iglesias Blanco, J; López García, Á. IFCA Cloud energy consumption metrics dataset (2025).

# Sharing / Access / Context information

1. Usage Licenses/restrictions placed on the data: CC-BY
2. Links to publications/other research outputs that cite the data: N/A
3. Links to publications/other research outputs that use the data: N/A
4. Links to other publicly accessible locations of the data: N/A
5. Links/relationships to ancillary data sets: N/A
6. Was data derived from another source?: No

# Data & File overview

The dataset includes two different types of metric files:

1. **Physical nodes energy consumption metrics** (files under `nodes`): These metrics provide 3-minute readings on the energy consumption of the physical nodes in the IFCA Cloud infrastructure. The data is collected from IPMI, from RAPL (Running Average Power Limit) and from the Scaphandre energy consumption metrology agent.
2. **Virtual Machines energy consumption metrics** (files under `nodes-vms`): These metrics provide 3-minute readings on the energy consumption of the virtual machines running in the IFCA Cloud infrastructure, as seen from the hypervisor. The data is collected using the Scaphandre energy consumption metrology agent.

Additionally, the dataset includes two auxiliary files:

1. **Physical nodes group information** (files under `node-groups`): These files contain information about the physical nodes in the IFCA Cloud infrastructure, including their hardware characteristics.
2. **Virtual Machines information** (files under `vms`): These files contain information about the virtual machines running in the IFCA Cloud infrastructure, including their hardware characteristics, as long as the user and project associated with them.

For each of these files, data is stored as a snapshot for the given period of
time. This version of the dataset contains the following snapshots:

- 14 December 2024 to 13 April 2025: `2024-12-14T000000Z_2025-04-13T235959Z`.

The identifiers have been anonymized to protect the privacy of the users and
the projects in a manner that they can still be linked between the different
files. The following identifiers are used in a consistent manner on all the
files:

- `node_group`: The group of nodes to which the node belongs. This is a string identifier that is used to group the nodes in the IFCA Cloud infrastructure. The groups are defined by the IFCA Cloud administrators. Nodes in a given group are of similar hardware characteristics.
- `node_name`: The name of the node. This is a string identifier that is used to identify the node in the IFCA Cloud infrastructure. The names are defined by the IFCA Cloud administrators.
- `vm_id`: The ID of the virtual machine. This is a string identifier that is used to identify the virtual machine in the IFCA Cloud infrastructure. The IDs are defined by the IFCA Cloud administrators.
- `hypervisor_name`: The name of the hypervisor. This is a string identifier that is used to identify the hypervisor in the IFCA Cloud infrastructure. The names of the hypervisors are equivalent to the `node_name` of the physical nodes where they are running.
- `hypervisor_group`: The group of hypervisors to which the hypervisor belongs. This is a string identifier that is used to group the hypervisors in the IFCA Cloud infrastructure. The names of the hypervisor groups are equivalent to the `node_group` of the physical nodes where they are running.
- `project_id`: The ID of the project. This is a string identifier that is used to identify the project in the IFCA Cloud infrastructure. The IDs are defined by the IFCA Cloud administrators.
- `user_id`: The ID of the user. This is a string identifier that is used to identify the user in the IFCA Cloud infrastructure. The IDs are defined by the IFCA Cloud administrators. A user can belong to multiple projects.
- `image_ref`: The ID of the image. This is a string identifier that is used to identify the image in the IFCA Cloud infrastructure. The IDs are defined by the IFCA Cloud administrators. The images are used to create the virtual machines.

## Data & File overview - "Physical nodes energy consumption metrics"

1. File List: The `nodes/<snapshot>/` directory contains the energy consumption metrics for the physical nodes in the IFCA Cloud infrastructure. The files are named as follows `nodes/<snapshot>/<node_group>/<node_name>.csv`
2. Relationship between files: Physical nodes in this dataset are hosts for the Virtual Machines in the "Virtual Machines energy consumption metrics" dataset. The `node_name` of the physical nodes is equivalent to the `hypervisor_name` of the virtual machines running in them. The `node_group` of the physical nodes is equivalent to the `hypervisor_group` of the virtual machines running in them.
3. Additional related data collected that was not included in the current data package: N/A
4. Are there multiple versions of the dataset?: N/A

## Data & File overview - "Virtual Machines energy consumption metrics"

1. File List: The `nodes-vms/<snapshot>/` directory contains the energy consumption metrics for the virtual machines in the IFCA Cloud infrastructure. The files are named as follows `nodes-vms/<snapshot>/<node_group>/<node_name>/<vm_id>.csv`
2. Relationship between files: VMs in this dataset are running in the physical nodes in the "Physical nodes energy consumption metrics" dataset. The `hypervisor_name` of the virtual machines is equivalent to the `node_name` of the physical nodes where they are running. The `hypervisor_group` of the virtual machines is equivalent to the `node_group` of the physical nodes where they are running.
3. Additional related data collected that was not included in the current data package: N/A
4. Are there multiple versions of the dataset? If so, please indicate where they are located: N/A

## Data & File overview - "Physical nodes group information"

1. File List: The `node-groups/<snapshot>/groups.csv` file contains the hardware characteristics and information about the physical nodes in the IFCA Cloud infrastructure.
2. Relationship between files, if important: The groups defined in this dataset are used to group the physical nodes in the "Physical nodes energy consumption metrics" dataset. The `node_group` of the physical nodes is equivalent to the `hypervisor_group` of the virtual machines running in them.
3. Additional related data collected that was not included in the current data package: N/A
4. Are there multiple versions of the dataset? If so, please indicate where they are located: N/A

## Data & File overview - "Virtual Machines information"

1. File List: The `vms/<snapshot>/vms.csv` file contains the hardware characteristics and information about the virtual machines in the IFCA Cloud infrastructure, including their user and project information.
2. Relationship between files, if important: The `vm_id` of the virtual machines in this dataset is equivalent to the `vm_id` of the virtual machines in the "Virtual Machines energy consumption metrics" dataset. The `project_id` and `user_id` of the virtual machines in this dataset are used to identify the project and user associated with them.
3. Additional related data collected that was not included in the current data package: N/A
4. Are there multiple versions of the dataset? If so, please indicate where they are located: N/A

# Methodological Information

1. Description of methods used for collection/generation of data: Energy consumption metrics are gathered from the [Intelligent Platform Management Interface (IPMI)](https://www.intel.com/content/www/us/en/products/docs/servers/ipmi/ipmi-home.html), [Running Average Power Limit (RAPL)](https://docs.kernel.org/power/powercap/powercap.html) interface and from the [Scaphandre](https://github.com/hubblo-org/scaphandre) energy consumption metrology agent.
2. Methods for processing the data: The identifiers have been anonymized to protect the privacy of the users and the projects in a manner that they can still be linked between the different files. Cf. "Data & File overview" section for more details.
3. Instrument- or software-specific information needed to interpret/reproduce the data, please indicate their location: N/A
4. Standards and calibration information: N/A
5. Environmental/experimental conditions: N/A
6. Describe any quality-assurance procedures performed on the data: N/A
7. People involved with sample collection, processing, analysis and/or submission (CREDIT roles): Jaime Iglesias Blanco (Conceptualization, Data curation, Methodology, Software), Álvaro López García (Conceptualization, Data curation, Resources, Software, Supervision, Validation, Methodology, Investigation, Validation).
8. Author contact information: Jaime Iglesias Blanco ([iglesias@ifca.unican.es](mailto:iglesias@ifca.unican.es)), Álvaro López García ([aloga@ifca.unican.es](mailto:aloga@ifca.unican.es)), [IFCA Advanced Computing and e-Science group](https://advancedcomputing.ifca.es/).

# Data-specific Information

## Data-specific Information - "Physical nodes energy consumption metrics"

1. Number of variables: 51
2. Number of cases/rows: 7434114
3. Variable List:
   - **Identifiers:**
     - `timestamp`: Timestamp of the measurement in ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`). All timestamps are in UTC.
     - `node_name`: The name of the node. This is a string identifier that is used to identify the node in the IFCA Cloud infrastructure.
     - `node_group`: The group of nodes to which the node belongs. This is a string identifier that is used to group the nodes in the IFCA Cloud infrastructure. Nodes in a given group are of similar hardware characteristics.
   - **CPU Usage Metrics:**
     - `cpu_usage_percent`: CPU overall usage percentage of the node.
     - `cpu_idle_percent`: CPU idle state percentage of the node.
     - `cpu_nice_percent`: CPU nice state percentage of the node.
     - `cpu_interrupt_percent`: CPU interrupt state percentage of the node.
     - `cpu_softirq_percent`: CPU softirq state percentage of the node.
     - `cpu_steal_percent`: CPU steal state percentage of the node.
     - `cpu_system_percent`: CPU system state percentage of the node.
     - `cpu_user_percent`: CPU user state percentage of the node.
     - `cpu_wait_percent`: CPU wait state percentage of the node.
   - **System Load Metrics:**
     - `load_shortterm_percent`: Represents the system's load average over the last minute. It indicates how much the system has been under load recently, reflecting the immediate demand for CPU resources.
     - `load_midterm_percent`: Represents the system's load average over the last five minutes. This provides a more stable view of the system's load, smoothing out short-term fluctuations and showing the load over a more balanced period.
     - `load_longterm_percent`: Shows the system's load average over the last fifteen minutes. It provides insight into the system's load over a longer period, giving a clearer picture of sustained load trends and behavior.
   - **Process Metrics:**
     - `num_processes_total`: Total number of processes running on the node.
     - `num_processes_blocked`: Number of processes in the blocked state on the node.
     - `num_processes_paging`: Number of processes in the paging state on the node.
     - `num_processes_running`: Number of processes in the running state on the node.
     - `num_processes_sleeping`: Number of processes in the sleeping state on the node.
     - `num_processes_stopped`: Number of processes in the stopped state on the node.
     - `num_processes_zombie`: Number of processes in the zombie state on the node.
   - **Memory Metrics:**
     - `memory_total_bytes`: Total amount of DRAM memory in bytes on the node. This represents all the physical RAM available on the system.
     - `memory_free_bytes`: Total amount of free DRAM memory in bytes on the node. This is memory that is not currently being used by any process or system operation.
     - `memory_used_bytes`: Total amount of used DRAM memory in bytes on the node. This includes memory occupied by running processes and system operations.
     - `memory_buffered_bytes`: Total amount of buffered DRAM memory in bytes on the node. This is memory used to temporarily store data before writing it to disk.
     - `memory_cached_bytes`: Total amount of cached DRAM memory in bytes on the node. This represents memory used to store frequently accessed data to improve performance.
     - `memory_slab_recl_bytes`: Total amount of slab reclaimed DRAM memory in bytes on the node. This is memory freed after kernel objects were no longer in use.
     - `memory_slab_unrecl_bytes`: Total amount of unreclaimed slab DRAM memory in bytes on the node. This represents memory allocated by the kernel but not yet freed.
   - **Disk Metrics:**
     - `disk_total_bytes`: Total amount of disk space in bytes on the node. This includes all physical local storage devices attached to the system.
     - `disk_free_bytes`: Total amount of free disk space in bytes on the node. This is space that is not currently being used by any files or system operations.
     - `disk_used_bytes`: Total amount of used disk space in bytes on the node. This includes space occupied by files and system operations.
     - `disk_reserved_bytes`: Total amount of reserved disk space in bytes on the node. This is space set aside for system operations or specific applications.
   - **Network Metrics:**
     - `network_bw_rx_b/s`: Total network bandwidth received in bytes per second on the node. This indicates the rate at which data is being received over all network interfaces.
     - `network_bw_tx_b/s`: Total network bandwidth transmitted in bytes per second on the node. This indicates the rate at which data is being sent over all network interfaces.
   - **Power Consumption Metrics:**
     - **IPMI Power Consumption Metrics:**
       - `ipmi_system_power_watts`: Power consumption in watts of the node, as reported by the IPMI system.
       - `ipmi_cpu_power_watts`: Power consumption in watts of the CPU, as reported by the IPMI system.
       - `ipmi_memory_power_watts`: Power consumption in watts of the memory, as reported by the IPMI system.
       - `ipmi_fan_power_watts`: Power consumption in watts of the fans, as reported by the IPMI system.
       - `ipmi_psu1_ac_in_power_watts`: Power consumption in watts at the AC input of the first power supply unit, as reported by the IPMI system.
       - `ipmi_psu2_ac_in_power_watts`: Power consumption in watts at the AC input of the second power supply unit, as reported by the IPMI system.
       - `ipmi_psu1_dc_out_power_watts`: Power consumption in watts at the DC output of the first power supply unit, as reported by the IPMI system.
       - `ipmi_psu2_dc_out_power_watts`: Power consumption in watts at the DC output of the second power supply unit, as reported by the IPMI system.
     - **RAPL Power Consumption Metrics:**
       - `rapl_power_total_watts`: Power consumption in watts of the CPU + Memory subsystem, as reported by the RAPL system. It includes the sum of CPU Packages and DRAM.
       - `rapl_power_package_0_watts`: Power consumption in watts of the CPU Package 0, as reported by the RAPL system.
       - `rapl_power_package_1_watts`: Power consumption in watts of the CPU Package 1, as reported by the RAPL system.
       - `rapl_power_dram_0_watts`: Power consumption in watts of the DRAM 0, as reported by the RAPL system.
       - `rapl_power_dram_1_watts`: Power consumption in watts of the DRAM 1, as reported by the RAPL system.
       - `rapl_power_cores_0_watts`: Power consumption in watts of overall CPU cores at Package 0, as reported by the RAPL system.
       - `rapl_power_cores_1_watts`: Power consumption in watts of overall CPU cores at Package 1, as reported by the RAPL system.
     - **Scaphandre Power Consumption Metrics:**
       - `scaphandre_power_total_watts`: Power consumption in watts of the CPU + Memory subsystem, as reported by the Scaphandre energy consumption metrology agent. It includes the sum of CPU Packages and DRAM.
4. Missing data codes: Empty string
5. Specialized formats or other abbreviations used: N/A
6. Dictionaries/codebooks used: N/A
7. Controlled vocabularies/ontologies used: N/A

## Data-specific Information - "Virtual Machines energy consumption metrics"

1. Number of variables: 5
2. Number of cases/rows: 15942293
3. Variable List:
   - **Identifiers:**
     - `timestamp`: Timestamp of the measurement in ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`). All timestamps are in UTC.
     - `vm_id`: The ID of the virtual machine. This is a string identifier that is used to identify the virtual machine in the IFCA Cloud infrastructure.
     - `hypervisor_name`: The name of the hypervisor. This is a string identifier that is used to identify the hypervisor in the IFCA Cloud infrastructure. The names of the hypervisors are equivalent to the `node_name` of the physical nodes where they are running.
     - `hypervisor_group`: The group of hypervisors to which the hypervisor belongs. This is a string identifier that is used to group the hypervisors in the IFCA Cloud infrastructure. The names of the hypervisor groups are equivalent to the `node_group` of the physical nodes where they are running.
   - **Scaphandre Power Consumption Metrics:**
     - `scaphandre_vm_power_total_watts`: Power consumption in watts of the CPU + Memory subsystem of the virtual machine, as reported by the Scaphandre energy consumption metrology agent. It includes the sum of CPU Packages and DRAM.
4. Missing data codes: Empty string
5. Specialized formats or other abbreviations used: N/A
6. Dictionaries/codebooks used: N/A
7. Controlled vocabularies/ontologies used: N/A

## Data-specific Information - "Physical nodes group information"

1. Number of variables: 25
2. Number of cases/rows: 6
3. Variable List:
   - **Identifiers:**
     - `node_group`: The group of nodes to which the node belongs. This is a string identifier that is used to group the nodes in the IFCA Cloud infrastructure. The groups are defined by the IFCA Cloud administrators. Nodes in a given group are of similar hardware characteristics.
   - **Hardware Characteristics:**
     - `model`: Commercial name of the model of the node.
     - `form_factor`: Form factor of the node. Can be either *"Rack Server"*, *"Chassis Server"* or *"Blade Server"*.
     - `#sockets`: Number of CPU sockets in the node.
     - `cpu_model`: Commercial name of the CPU model in the node.
     - `#cores_per_socket`: Number of CPU cores per socket in the node.
     - `#threads_per_core`: Number of threads per core in the node.
     - `memory_type`: Type of memory in the node. Can be either *"DDR3"* or *"DDR4"*.
     - `memory_manufacturer`: Manufacturer of the memory in the node.
     - `memory_used_slots`: Number of used memory slots in the node.
     - `memory_total_size_GB`: Total size of the memory in GB in the node.
     - `#gpus`: Number of GPUs in the node.
     - `gpu_model`: Commercial name of the GPU model in the node, if applicable.
     - `#ethernet_nics`: Number of Ethernet NICs in the node.
     - `ethernet_nic_model`: Commercial name of the Ethernet NIC model in the node, if applicable.
     - `#infiniband_nics`: Number of Infiniband NICs in the node.
     - `infiniband_nic_model`: Commercial name of the Infiniband NIC model in the node, if applicable.
     - `#disks`: Number of disks in the node.
     - `disk_vendor`: Vendor of the disks in the node.
     - `disk_model`: Commercial name of the disk model in the node. Some are missing as they are only visible through the RAID controller.
     - `disk_type`: Type of the disks in the node. Can be either *"HDD"*, *"SSD"* or *"M.2 SATA SSD"*.
     - `disk_size_GB`: Capacity of the disks in GB in the node.
     - `#fans`: Number of fans in the node. Some explanations are added as they can be shared on the chassis and blade servers.
     - `#power_supplies`: Number of power supplies in the node. Some explanations are added as they can be shared on the chassis and blade servers.
     - `rated_power`: Rated power of the power supplies in watts in the node.
4. Missing data codes: Empty string
5. Specialized formats or other abbreviations used: N/A
6. Dictionaries/codebooks used: N/A
7. Controlled vocabularies/ontologies used: N/A

## Data-specific Information - "Virtual Machines information"

1. Number of variables: 8
2. Number of cases/rows: 612
3. Variable List:
   - **Identifiers:**
     - `vm_id`: The ID of the virtual machine. This is a string identifier that is used to identify the virtual machine in the IFCA Cloud infrastructure.
     - `project_id`: The ID of the project. This is a string identifier that is used to identify the project in the IFCA Cloud infrastructure. The IDs are defined by the IFCA Cloud administrators.
     - `user_id`: The ID of the user. This is a string identifier that is used to identify the user in the IFCA Cloud infrastructure. The IDs are defined by the IFCA Cloud administrators. A user can belong to multiple projects.
   - **Virtual Machines Characteristics:**
     - `image_ref`: The ID of the image. This is a string identifier that is used to identify the image in the IFCA Cloud infrastructure. The IDs are defined by the IFCA Cloud administrators. The images are used to create the virtual machines.
     - `vcpus`: Number of virtual CPUs in the virtual machine.
     - `memory_MB`: Amount of memory in MB in the virtual machine.
     - `root_GB`: Size of the root disk in GB in the virtual machine.
     - `ephemeral_GB`: Size of the ephemeral disk in GB in the virtual machine.
4. Missing data codes: Empty string
5. Specialized formats or other abbreviations used: N/A
6. Dictionaries/codebooks used: N/A
7. Controlled vocabularies/ontologies used: N/A