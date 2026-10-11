# SIH26226 — what went into the portal

Submitted 30 September 2026. The portal allows no changes after submission, so anything said
about Angaraka in a later round has to agree with this page and the PDF.

- **Title:** Project Angaraka: A Mars Rover That Chooses Its Own Next Goal, Without Waiting for Earth
- **Technology bucket:** IoT and Electronics
- **Idea template:** [`SIH26226_Maneki_Neko_Project_Angaraka.pdf`](SIH26226_Maneki_Neko_Project_Angaraka.pdf), the final export
- **YouTube link:** as entered in the portal. The `[PASTE THE DRIVE LINK…]` line below stood for
  the deck's Drive link, to be pasted in at submission.

The text is idea-first. The ideal system runs the model on board; the demonstration section says
it runs in the cloud because a Raspberry Pi 5 cannot hold a capable model.

## Abstract

```text
A Mars rover can drive itself, but it cannot decide what is worth doing. Perseverance steers around hazards on its own and can pick which nearby rock to measure with its laser. Where it goes and what it does each sol (Martian day) are still decided on Earth.

Every plan crosses a light delay of 3 to 22 minutes each way. A team on Earth reads the images the rover sent back, writes out the next sol's commands and uplinks them. The rover runs them, and the team finds out how it went on the next downlink. When the rover meets unexpected terrain or something interesting that nobody planned for, it cannot ask and wait. It carries on with a plan written before the situation was known, or it stops. For about two weeks every two years, during solar conjunction, the Sun sits between Earth and Mars, no commands are sent, and the rovers stop driving. A rover has a limited life, and much of it is spent waiting for Earth. The farther the mission, the longer the wait.

Our inspiration is the reflex arc in the human body. Touch a hot stove and your hand pulls back before your brain knows: the spinal cord handles the reflex, and the brain decides what to do next. A rover today has the reflexes, but its brain is on Earth, minutes away.

Project Angaraka (Angaraka is a Sanskrit name for Mars) puts the deciding on board. A small language model on the rover reads what the rover knows: its map, its position, its remaining energy, the objectives it has found and the intent the mission team set for the sol. It then chooses the next goal. It never drives. It calls a skill such as "go to this place". A proven path planner (A*) plans the route, and a driving policy trained with reinforcement learning carries it out. LiDAR measures where the rover actually ended up, so the model replans from the rover's real position. The model has knowledge and no hands; the driving policy has hands and no knowledge. We call this split the Reflex Arc.

Onboard software computes the facts, such as distances, positions and unexplored ground, so the model only has to weigh them. Every decision is logged with its reason in plain English. Only a short note is carried from one sol to the next, so the model's memory stays small over a long mission.

Mission teams would set intent instead of scripting every move. Targets would be chosen from what the rover saw today rather than yesterday's images. Hours spent waiting for Earth would become driving hours, and work would continue through conjunction. The benefit grows with distance, and the same approach fits places on Earth with poor communication.

We demonstrate the idea with a six-wheel Raspberry Pi rover carrying a 360° camera and a LiDAR, and a fogged Martian simulation with dust storms and a daily energy budget. The ideal system runs the language model on board. The demonstration runs it in the cloud, because a Raspberry Pi cannot run a model of that size.
```

## Idea description

```text
PROJECT ANGARAKA: A MARS ROVER THAT CHOOSES ITS OWN NEXT GOAL

1. THE PROBLEM

A sol, one Martian day, lasts about 24 hours and 39 minutes, and on a rover today each one begins on Earth. A team reads the images the rover sent back and decides where it should go and what it should do there. They write the day out as a sequence of commands and send it across a light delay of 3 to 22 minutes each way. The rover runs the plan, and the team finds out how it went on the next downlink.

Nothing on Mars can be driven live, and the rover cannot ask. When it meets unexpected terrain, or something scientifically interesting that nobody planned for, it has two choices. It can carry on with a plan written before anyone knew, or it can stop and wait for Earth. Either way time is lost, and time is what a rover has least of: a limited life, limited power, and a science team waiting on every sol.

For about two weeks every two years, during solar conjunction, the Sun sits between Earth and Mars and can corrupt radio commands, so engineers stop sending them. The rovers stop driving and run only what was uploaded beforehand.

The farther the mission, the worse this gets. Mars is minutes away; the moons of Jupiter and Saturn are hours away.

2. EXISTING SOLUTIONS

Rovers already do a great deal on their own.
- Driving. Perseverance's AutoNav makes 3D maps of the terrain ahead, identifies hazards and plans a route around them without waiting for Earth.
- Choosing what to measure. AEGIS lets Curiosity and Perseverance pick rocks for their laser spectrometers from their own images, using criteria set by scientists on Earth.
- Onboard computing. Ingenuity, the Mars helicopter, flew on a commercial smartphone processor (a Qualcomm Snapdragon). A JPL study (Didier et al., 2022) proposes using the high-performance processors already on Perseverance to analyse data on board, to reduce operations cost and do more science.
- Research. JPL's MLNav places a learned route proposer inside a deterministic safety check. Work such as SayCan shows a language model choosing among the skills a robot can physically perform.

3. THE GAP

In JPL's own description, rover drivers on Earth plan routes with specific stops, and AutoNav lets the rover choose how it gets to those stops. The destination is still chosen on Earth. Every onboard system above answers a "how" question: how to cross the next stretch of ground, or which rock in view to measure. None of them decides where the rover goes next, which objective it pursues, or when to stop exploring and head back. That judgment sits on Earth, a sol behind the rover.

Research on language models choosing robot skills works in short episodes that can be reset, in labs and games, with a person close by. A rover has to keep going sol after sol with no reset, on ground nobody has seen, with the nearest person minutes away.

4. INSPIRATION

Touch a hot stove and your hand pulls back before you feel the pain. The signal runs to the spinal cord and straight back to the muscle; that loop is the reflex arc. The brain is not asked. It catches up a moment later and decides what to do next.

A rover already has reflexes: it steers around a rock by itself. What it lacks is the brain, which today is a room of experts on Earth, minutes away. Angaraka moves the judgment on board and leaves the reflexes where they are.

The second inspiration came from trying the two technologies on their own. A language model knows a great deal: what a crater might hide, why a layered rock matters, when to turn back. But it is slow, and poor at exact geometry and motor control. A reinforcement learning policy reacts in milliseconds and handles terrain well, but it knows only the one skill it was trained for. Each is good at what the other lacks.

5. THE IDEA

An onboard small language model chooses the rover's goals and hands each one to a learned driving policy to carry out. The model has knowledge and no hands; the policy has hands and no knowledge. We call the architecture the Reflex Arc, and the rover that carries it Angaraka, a Sanskrit name for Mars.

Earth stops scripting the day and starts setting intent, for example: "survey the rim of this crater; the layered outcrop is the priority; be back in range of the orbiter pass by evening". The rover works out the rest on Mars, in seconds, and reports what it did and why.

6. METHODOLOGY

How a decision reaches the wheels:

1. Intent from Earth. Once a sol, the mission team uploads goals, priorities and limits in plain language.
2. Perception. A 360° camera looks all around the rover for objectives and unexplored ground. LiDAR measures the surroundings and the rover's own position and heading. Together they keep a map of what is open ground, what is rock and what has not been seen yet.
3. Facts are computed, not guessed. Onboard software turns the map into facts: distances, reachable places, what each objective costs and how much energy is left. It gives these to the model as text. Language models are poor at measuring geometry from a picture and good at weighing facts, so the software measures and the model weighs.
4. Deciding. The model reads the facts and the intent, and calls one skill at a time:
   - go to a place
   - price a route without moving
   - carry out a science task where it is
   - note something for tomorrow
   - hand control back to Earth
   Each skill checks its preconditions and refuses an invalid call with a reason.
5. Planning. A proven path planner (A*) turns a destination into a route.
6. Driving. A policy trained with reinforcement learning in simulation drives the route and reacts to the ground in real time. The rover's existing hazard avoidance stays underneath as a backstop.
7. Feedback. After every leg, LiDAR measures where the rover actually ended up. If a drive was blocked or fell short, the model is told where the rover really is and replans from there.
8. Memory and record. The model keeps a short list for the sol and writes one compact note that survives into the next sol. Its view of the world is rebuilt from scratch before every decision, so its context does not grow over a long mission. Every call is logged with the reason the model gave, and the log goes to Earth on the next downlink.

Thinking takes seconds, planning takes milliseconds, and driving happens in real time. The model is consulted a few times a sol, between drives.

7. THE IDEAL SOLUTION

On a flight rover, Angaraka runs entirely on board:
- a small language model on a radiation-tolerant, high-performance processor such as NASA and Microchip's HPSC, which is being built to give at least 100 times the computing of today's spaceflight computers
- a 360° camera and LiDAR for perception
- a driving policy trained in simulation on Martian terrain and refined on the real vehicle
- the rover's existing hazard avoidance and fault protection underneath everything

Earth uplinks intent once a sol. The rover spends the whole sol working and downlinks what it did and why. During conjunction it carries on with a restricted set of skills and budgets that Earth fixed in advance, and parks safely if anything falls outside them.

8. FEASIBILITY

- Self-driving on Mars is proven. AutoNav already steers Perseverance around hazards, and Angaraka adds the layer above it.
- Onboard choice is already trusted. AEGIS has been choosing laser targets on Mars for years. Angaraka widens that choice from which rock to measure to where to go next.
- Speed is not a constraint. Decisions are needed a few times a sol, not every second, so a modest onboard processor is fast enough.
- The compute is on its way. Today's rover computer, a RAD750 running at up to 200 MHz with 256 MB of memory, is far too small for a language model. HPSC is being built for onboard AI, Ingenuity has already flown a commercial phone processor on Mars, and JPL's own study argues for more onboard processing.
- Safety comes from the design. The model never touches the motors. Every goal passes through the planner, the driving policy and hazard avoidance, so a bad decision costs a detour rather than the rover.

9. IMPACT AND BENEFITS

Target audience: mission teams at ISRO, NASA and ESA, and the scientists who depend on them.
- Scientific. More science from every sol of a rover's limited life. Targets are chosen from what the rover saw today, and an unexpected find can be followed up the same sol.
- Operational. Teams set intent instead of scripting every move, and conjunction stops being lost time.
- Economic. More return from a fixed-cost mission and lighter daily operations.
- Scales with distance. The longer the link, the more onboard judgment is worth: Mars is minutes away, the outer planets hours.
- On Earth. The same architecture fits places where communication is poor or slow, such as disaster sites, mines, and polar or deep-sea surveys.
- Education. It is open source and runs on student hardware, so other teams can build on it.

10. PROS AND CONS

Pros
- Decisions are made on Mars in seconds, from current information.
- The language model cannot directly harm the rover.
- Every decision comes with a reason in plain English, so it can be audited.
- It is modular: the model, the planner and the driving policy can each be upgraded or replaced separately.
- It builds on parts that are already proven, such as path planning and hazard avoidance.
- Memory stays the same size however long the mission runs.

Cons
- It needs more computing and power than today's rovers carry.
- A language model's choices are harder to verify than deterministic flight software.
- Language models reason poorly about space, so the layer that computes facts must be built carefully and trusted.
- The driving policy is only as good as the terrain simulation it was trained in.
- The reasons in the log cost some downlink.

11. POTENTIAL ISSUES AND HOW WE WOULD ADDRESS THEM

- Wrong or inconsistent decisions. Skills are bounded and check their preconditions. The planner, the policy and hazard avoidance sit below them, Earth sets energy and distance budgets, and Earth can review and override. The worst case is a wasted drive.
- Trust. Roll it out in stages. First the model proposes and Earth approves. Then it acts inside limits Earth sets. Only then does it run unattended through stretches such as conjunction.
- Model size. How small the onboard model can be while still deciding well is an open question. Our demonstration uses a larger model in the cloud, and finding the smallest model that works is part of the work ahead.
- Compute, power and radiation. The model runs only between drives, a few times a sol, on a flight-qualified processor, and the skill checks catch malformed calls.
- Spatial mistakes. Geometry is computed in code, and the model is never asked to measure.
- Simulation to reality. The policy is trained in simulation and refined on the vehicle, with hazard avoidance as a backstop.
- Long missions. The view is rebuilt before every decision, and only one compact note is carried per sol.

12. HOW WE ARE DEMONSTRATING IT

A flight processor is out of reach for a student team, so the demonstration keeps the architecture and moves the heavy computing off the rover.
- The rover. A six-wheel chassis with a Raspberry Pi 5 (8 GB), a 360° camera, a LiDAR, a SmartElex 15D motor driver and an 11.1 V LiPo battery. The LiDAR maps the surroundings and tracks the rover's own movement, and planned routes drive the real motors.
- The language model. A Raspberry Pi 5 has 8 GB of memory, too little for a capable model, so the demonstration runs Gemma 4 (31B) in the cloud and the rover calls it over the network. It uses the same skill interface an onboard model would.
- The simulation. A fogged Martian area with rock formations, a daily dust storm, objectives of three priorities that cost time to complete, and a daily energy budget, all behind the same skills.
- The driving policy is being trained with reinforcement learning in Unity. Until it is ready, the planned route drives the motors directly.

In a recorded sol, the model explored under fog, found all three objectives, noted their coordinates and returned to base. Told to finish only the nearest one, it priced all three routes and chose correctly. It also misread the shape of a C-shaped rock, which is why the design computes geometry in code instead of asking the model to measure.

Code: https://github.com/IshuIsAwake/reflex-arc
Videos (simulation run and LiDAR on the rover): [PASTE THE DRIVE LINK FROM THE DECK]

13. REFERENCES

- NASA's Self-Driving Perseverance Mars Rover "Takes the Wheel" (JPL, 2021)
- NASA's Mars Fleet Lies Low With Sun Between Earth and Red Planet (JPL, 2021)
- Results From the First Four Years of AEGIS Autonomous Targeting for ChemCam on Mars Science Laboratory and New Capability Planned for SuperCam on Mars 2020 Rover (NASA NTRS 20220001538)
- Perseverance rover components: the RAD750 computer (NASA)
- High Performance Spaceflight Computing, HPSC (NASA)
- Benchmarking and Testing of Qualcomm Snapdragon System-on-Chip for JPL Space Applications and Missions (IEEE, 2022)
- Didier et al., New Rover Conops with High-Performance Onboard Computing: Give Up Raw Data to Reduce Ops Cost and Do More Science (NASA NTRS, 2022)
- SayCan: Do As I Can, Not As I Say (arXiv:2204.01691)
- MLNav: learned proposer, safe verifier (JPL, arXiv:2203.04563)
- Hösch et al.: language model choosing among RL skills (arXiv:2606.20014)
- LARAP: language model over robot action primitives (Scientific Reports, 2025)
- SCALAR: skills with preconditions (arXiv:2603.09036)
```
