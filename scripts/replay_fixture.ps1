$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$scenario = Join-Path $repository 'examples\reviewer_repro\scenario.json'
$rawOutput = Join-Path $repository 'examples\reviewer_repro\raw_output.txt'
$destination = Join-Path $repository 'artifacts\reviewer-repro-local'
$env:PYTHONPATH = Join-Path $repository 'src'
python -m behaviortune.cli replay --scenario $scenario --condition BASE --raw-output $rawOutput --output-dir $destination
