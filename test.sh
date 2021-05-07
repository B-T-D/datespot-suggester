#!/bin/bash

echo $"Running all pytests in Python env."

source env/bin/activate

coverage run -m pytest && coverage report -m --omit=env/*

#python3 -m pytest --cov=python_backend # old
