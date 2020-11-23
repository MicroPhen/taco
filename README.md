# TACO
TACO (Tool for Automated Cloning) is a simple tool to keep track about your progress in an automated cloning workflow. It has been developed to aid the authors of the study "Automated rational strain construction based on high-throughput conjugation" (Link). Its focus is to keep track of the different constructs and provide template files for certain unit operations in the workflow. Additionally, add-ons can be used, e.g., for analyzing data from capillary gel electrophoresis devices. TACO comes with an MIT licence. Anyone who is interested in using or contribution to TACO is invited to do so. For a quick start, a real-world application can be found in the example folder.

## Requirements 
* python 3.8
* pandas
* xlrd
* openpyxl
* numpy

If you want to create directed acyclic graphs (DAGs), you will need:
* graphviz

## Installation
* In a shell, navigate to the folder where you want the repository to be located.
* Open a terminal and clone the repository via git clone
* Change directory to the newly cloned repository
* Install via `python setup.py install`
