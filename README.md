# Operation Ultron

Ultron has hidden his physical body in **one of 196 fictional water stations in Sonora, Mexico**. Investigate the network and identify its station ID.

## Start

Requirements: Python 3.10 or later. Loading the data requires only the standard library.

```bash
python starter.py
python -m unittest discover -s tests -v
```

Complete the unfinished functions in `starter.py`. The template loads and validates the datasets but **does not solve the mystery**.

## Data

| File | Network or information | Columns |
| --- | --- | --- |
| `data/stations.csv` | 196 candidate stations (`S000`–`S195`) | `id,row,column,region,facility_type` |
| `data/roads.csv` | 690 undirected roads | `source,target,travel_minutes,cable_cost` |
| `data/interference.csv` | 1,000 undirected pairs of interfering antennas | `node_a,node_b` |
| `data/pipes.csv` | 689 directed water pipes | `source,target,capacity_per_minute` |
| `data/checkpoints.csv` | 12 checkpoints, in arbitrary order | `file_order,station_id` |


## Investigation clues:

Apply the clues **in order**. After each clue, print the IDs of all remaining candidates. Do not assume a clue identifies a single station on its own.

1. **Dijkstra: Escape timing.** Compute minimum road-travel times from `S000`, using `travel_minutes`. Ultron's station is **72–96 minutes** away, inclusive.

2. **Floyd–Warshall: Two repeaters.** Compute the shortest travel time between **every pair** of stations. Ultron's station is **30–78 minutes from `S013`** and **83–107 minutes from `S182`**, inclusive. Retain only candidates satisfying both distances and the previous clue.

3. **Prim and Kruskal — Cable backbone.** Independently compute a minimum spanning tree of the roads using **`cable_cost`**, not travel time. Compare the total costs and resulting tree edges. The backbone must have **195 edges**. Ultron's station has **degree 1** in the selected minimum spanning tree. Use both algorithms to support your conclusion.

4. **Graph coloring: Radio interference.** Assign frequency groups so adjacent vertices of the interference graph never share a group, using the **minimum possible number of groups**. Stations `S000`, `S013`, `S182`, and `S195` form a mutually interfering group. Ultron uses **the same frequency as `S182`**. Frequency names are interchangeable: compare station groups rather than arbitrary color numbers.

5. **Traveling Salesperson Problem: Inspection tour.** Starting at `S000`, visit each of the **12 stations** in `checkpoints.csv` **exactly once**, then return to `S000`. Use shortest-path road travel times from Step 2 between tour stops. Find the **exact shortest tour** (not a heuristic). If several tours tie, choose the **lexicographically smallest checkpoint-ID sequence** after the fixed start. The **sixth checkpoint visited** is **27–47 minutes** from Ultron's station, inclusive. A dynamic-programming solution (Held–Karp) is acceptable.

6. **Maximum flow: Water signature.** For each remaining candidate, compute the maximum flow through `data/pipes.csv` **from that station to `OUTLET`**. Treat the candidate as an unlimited injection point; every directed pipe still has its given capacity. Ultron's station can deliver **exactly 60 units per minute**. You may implement Ford–Fulkerson or Edmonds–Karp; account for residual edges.
