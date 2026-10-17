#!/usr/bin/env bash
# Run from the source checkout after origin has been set. First-time setup only.
set -euo pipefail
remote_url=$(git remote get-url origin)
if git ls-remote --heads origin monitor-state | rg -q .; then
  echo 'monitor-state already exists; refusing to reset it' >&2
  exit 1
fi
state_dir=$(mktemp -d)
trap 'rm -rf "$state_dir"' EXIT
uv run python -m scripts.initialize_state "$state_dir/state.json"
git -C "$state_dir" init --initial-branch=monitor-state
git -C "$state_dir" config user.name 'Tennis Monitor Setup'
git -C "$state_dir" config user.email 'tennis-monitor@users.noreply.github.com'
git -C "$state_dir" remote add origin "$remote_url"
git -C "$state_dir" add state.json
git -C "$state_dir" commit -m 'Initialize durable state; first check establishes baseline'
git -C "$state_dir" push origin HEAD:refs/heads/monitor-state
