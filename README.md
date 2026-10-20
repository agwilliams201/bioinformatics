# bioinformatics

as per the problem statement:

1. make setup creates a virtual environment in .venv and installs the python dependencies from requirements.txt into it
2. make pipeline builds cell-count.db (load_data.py), then runs the analysis (analysis.py),
   which prints the results and writes them to outputs/
3. make dashboard starts the dashboard

## dashboard

http://localhost:8000 (after make dashboard)

## design decisions

pls see comments in code for design decisions, generally speaking i leaned towards making this expandable s.t. in theory it would be able to handle bigger/different data (with the exception of the FE filter, which was done purely for convenience)
