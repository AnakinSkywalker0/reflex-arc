# Can do (later)

Small tidy-ups. Nice to have, not urgent. Don't do these before the demo.

- **Replace `stack.sh` / `rover` with a ROS launch file, and start it on boot.**
  Cleaner and more reliable than the long bash script. Nithin's `optimisations.md` in PI_5 says
  the same.
- **Switch ROS messaging to CycloneDDS.**
  Often more stable on a Raspberry Pi. Only try it if ROS freezing comes back (`no_shm.xml` is the
  current fix for that).
