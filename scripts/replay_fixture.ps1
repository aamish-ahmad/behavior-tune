$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$scenario = Join-Path $repository 'examples\replay_fixture\scenario.json'
$rawOutput = Join-Path $repository 'examples\replay_fixture\raw_output.txt'
$destination = Join-Path $repository 'artifacts\replay-local'
$env:PYTHONPATH = Join-Path $repository 'src'
python -m behaviortune.cli replay --scenario $scenario --condition BASE --raw-output $rawOutput --output-dir $destination
