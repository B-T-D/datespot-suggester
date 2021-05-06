#!/bin/bash

echo $"Running all pytests in Python env."

source env/bin/activate

python3 -m pytest
