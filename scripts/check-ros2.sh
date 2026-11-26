#!/usr/bin/env bash
# Run upstream demos only. No robot drivers or hardware commands.
set -eo pipefail
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=87
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
unset ROS_STATIC_PEERS
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
logs=$(mktemp -d)
pids=()
cleanup() {
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
  rm -rf "$logs"
}
trap cleanup EXIT
# timeout bounds the demos even if a client disconnects.
timeout --signal=INT 25s ros2 run demo_nodes_cpp talker >"$logs/talker" 2>&1 &
pids+=("$!")
timeout --signal=INT 25s ros2 run demo_nodes_py listener >"$logs/listener" 2>&1 &
pids+=("$!")
if ! timeout 20s ros2 topic echo /chatter std_msgs/msg/String --once --no-daemon >"$logs/echo" 2>&1; then
  cat "$logs"/*
  exit 1
fi
for attempt in {1..10}; do
  if grep -q 'I heard' "$logs/listener"; then break; fi
  sleep 1
done
grep -q 'Publishing' "$logs/talker"
grep -q 'I heard' "$logs/listener"
grep -q 'Hello World' "$logs/echo"
head -n 2 "$logs/talker" "$logs/listener" "$logs/echo"
printf '\nPASS: C++ publisher, Python subscriber, and topic echo (domain 87, localhost).\n'
