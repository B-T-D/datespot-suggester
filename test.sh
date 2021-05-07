#!/bin/bash

echo $"Running all pytests in Python env."

source env/bin/activate

python3 -m pytest --cov=python_backend # coverage report misses some files even though the corresponding tests ran
