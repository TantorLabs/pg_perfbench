#!/bin/bash
exclude_params='CPU(s) scaling MHz'
lscpu | grep -Ev '$exclude_params'