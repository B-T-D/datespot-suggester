#!/bin/bash

echo $"Running all pytests in Python env"

source env/bin/activate

python3 -m populate_mock_data && coverage run -m pytest -s && coverage report -m --omit=env/* # -s flag shows std out even when tests pass
