# NariShield AI • Inter-Thread Specification
# Thread 3 (ML/DL/XAI) → Thread 4 (DSA & Intelligent Route Optimization)
# Mathematical Risk Contract & Normalization Specification

**Document Version**: `1.0.0`  
**Status**: `FINAL_APPROVED`  
**Author**: Thread 3 (Machine Learning, Deep Learning & Explainable AI)  
**Consumer**: Thread 4 (Data Structures, Algorithms & Safe Routing Engine)  
**Mathematical Objective**: Guarantee bounded, monotonic, non-negative risk edge weights for Dijkstra / A* / Contraction Hierarchies.

---

## 1. Context & Architectural Separation

In the NariShield AI single-process architecture:
- **Thread 4's Exclusive Mandate**: Graph construction, spatial indexing (R-Tree / KD-Tree), Dijkstra's algorithm, A* heuristic pathfinding, and Pareto multi-objective route optimization (Safety vs. Distance vs. Time).
- **Thread 3's Mandate**: Statistical modeling, contextual risk inference, crowdsource temporal decay, and risk score normalization. **Thread 3 NEVER implements Dijkstra or A*.**

Thread 3 provides Thread 4 with:
1. The **Formal Cost Equation** for graph edge evaluation.
2. The **Mathematical Proofs of Normalization & Boundedness**.
3. The **Batch Waypoint Scoring API & Schema**.

---

## 2. Mathematical Formulations

### 2.1 Graph Edge Definition
Let the road network be represented as a directed graph $G = (V, E)$, where:
- $V = \{v_1, v_2, \dots, v_n\}$ is the set of intersections / waypoints.
- $E = \{(u, v) \mid u, v \in V\}$ is the set of road segments.
- Each edge $e = (u, v) \in E$ possesses physical length $L(e) > 0$ (in meters).

---

### 2.2 Risk Score Normalization Guarantee
Thread 3 computes a raw dynamic risk score $R_{\text{raw}}(e) \in [0.0, 100.0]$.

To preserve algorithmic stability in Thread 4, Thread 3 guarantees that the normalized risk $r(e)$ satisfies:
$$r(e) = \text{clip}\left(\frac{R_{\text{raw}}(e)}{100.0}, 0.0, 1.0\right) \in [0.0, 1.0]$$

#### Theorem 1 (Non-Negativity & Boundedness):
$$\forall e \in E, \quad 0.0 \le r(e) \le 1.0$$
*Proof*: Since $R_{\text{raw}}(e) \ge 0.0$ by non-negative feature activations and the clipping operator restricts outputs to $[0.0, 1.0]$, $r(e)$ is strictly non-negative and finite. $\blacksquare$

---

### 2.3 Edge Cost Traversal Function
Thread 4 evaluates the traversal cost of edge $e$ under penalty parameter $\beta \ge 0$:

$$C(e) = L(e) \cdot \left(1 + \beta \cdot r(e)\right) \cdot \Phi_{\text{corridor}}(e)$$

Where:
- $L(e)$: Physical edge length (meters).
- $\beta$: Safety sensitivity factor (configured default: $\beta = 2.5$).
  - When $\beta = 0$: $C(e) = L(e)$ (pure shortest distance path).
  - When $\beta = 2.5$: An edge with maximum danger ($r(e) = 1.0$) incurs a **$3.5\times$ distance penalty**, causing Dijkstra/A* to detour through safer avenues.
- $\Phi_{\text{corridor}}(e)$: Safe corridor infrastructure modifier:
  $$\Phi_{\text{corridor}}(e) = \begin{cases} 
  0.85 & \text{if } \text{StreetLighting}(e) \ge 0.80 \text{ and } \text{DistPolice}(e) \le 1.0\text{ km} \\
  1.00 & \text{otherwise}
  \end{cases}$$

#### Theorem 2 (Dijkstra Non-Negative Edge Weight Invariant):
$$\forall e \in E, \quad C(e) > 0$$
*Proof*: Since $L(e) > 0$, $\beta \ge 0$, $r(e) \ge 0$, and $\Phi_{\text{corridor}}(e) \ge 0.85$:
$$C(e) \ge L(e) \cdot (1 + 0) \cdot 0.85 = 0.85 \cdot L(e) > 0$$
Therefore, no zero or negative-weight cycles can exist in $G$, ensuring Dijkstra's algorithm and A* always terminate with globally optimal solutions. $\blacksquare$

#### Theorem 3 (A* Admissible Heuristic Compatibility):
For A* search with Euclidean distance heuristic $h(u, \text{target}) = \|\mathbf{x}_u - \mathbf{x}_{\text{target}}\|_2$:
To guarantee admissibility ($h(u) \le C^*(u, \text{target})$), Thread 4 must scale the Euclidean distance by the minimum possible edge multiplier:
$$h_{\text{safe}}(u) = 0.85 \cdot \|\mathbf{x}_u - \mathbf{x}_{\text{target}}\|_2$$
Because $\forall e, C(e) \ge 0.85 \cdot L(e)$, $h_{\text{safe}}(u)$ is strictly admissible (never overestimates the true traversal cost). $\blacksquare$

---

## 3. High-Throughput Batch Scoring Protocol

Thread 4 needs to evaluate hundreds of road segments without incurring per-request HTTP overhead. Thread 3 provides the **Batch Waypoint / Edge Risk Interface**:

### Python In-Process Function:
```python
from narishield_ml.thread4_route_contract import Thread4RiskContract

# edges: List of road segment descriptors
evaluated_edges = Thread4RiskContract.evaluate_edge_batch(
    edges=road_network_edges,
    dynamic_risk_engine=engine,
    beta=2.5
)
```

### JSON Input Payload Format:
```json
{
  "route_id": "QUERY_PATH_901",
  "day_of_week": 5,
  "month": 10,
  "waypoints": [
    {
      "waypoint_id": "WP_101",
      "latitude": 28.6140,
      "longitude": 77.2095,
      "hour": 23,
      "dist_police_km": 3.5,
      "dist_hospital_km": 4.0,
      "street_lighting_score": 0.20,
      "weather_condition": "Clear",
      "zone_type": "Isolated"
    },
    {
      "waypoint_id": "WP_102",
      "latitude": 28.6120,
      "longitude": 77.2080,
      "hour": 23,
      "dist_police_km": 0.6,
      "dist_hospital_km": 2.0,
      "street_lighting_score": 0.88,
      "weather_condition": "Clear",
      "zone_type": "Commercial"
    }
  ]
}
```

### JSON Output Format Consumed by Thread 4:
```json
{
  "route_id": "QUERY_PATH_901",
  "total_waypoints_evaluated": 2,
  "beta_risk_penalty": 2.5,
  "results": [
    {
      "waypoint_id": "WP_101",
      "risk_score": 78.40,
      "normalized_risk": 0.784,
      "risk_category": "HIGH",
      "edge_cost_multiplier": 2.960
    },
    {
      "waypoint_id": "WP_102",
      "risk_score": 21.50,
      "normalized_risk": 0.215,
      "risk_category": "LOW",
      "edge_cost_multiplier": 1.306
    }
  ]
}
```

---

## 4. Multi-Objective Routing Integration (Pareto Frontiers)

Thread 4 may compute three alternative routes for the user:
1. **Safest Route ($\beta = 4.0$)**: Minimizes total risk $R_{\text{path}} = \sum_{e \in \text{path}} r(e)$, accepting up to 30% longer physical distance.
2. **Balanced Safe Route ($\beta = 2.0$)**: Balances distance and illumination corridors.
3. **Fastest Route ($\beta = 0.0$)**: Standard shortest distance / time path.

Thread 3 outputs `normalized_risk_thread4` continuously so Thread 4 can dynamically adjust $\beta$ on the fly based on user preferences in Thread 1's UI slider.
