# GPU FinOps Submission Note

NimbusAI should optimize against $/1M-token instead of raw $/GPU-hour. The baseline monthly spend is $27,133 and the optimized plan is $14,626, for projected savings of $12,507 (46%).

The largest lever is purchasing strategy: interruptible jobs move to spot with checkpointing, while steady inference moves to reserved capacity. Inference serving also improves through cascade routing, prompt caching, and batch API usage.

I implemented two "Your Turn" extensions:

- Cache economics: `cache_is_worth_it()` gates cache usage by comparing cache-write premium against expected read savings. In this dataset, 2,400/2,400 cache candidates pass the break-even gate, with ~0.28 reads needed per cached prompt.
- Reasoning budget: M2/M5 now report reasoning traffic separately. The dataset has 201 reasoning requests, costing $1.40/day and consuming 29,788 Wh/day, so reasoning should be routed only for eval, complex planning, and escalation cases.

Verification:

- `verify.py`: 11/11 checks passed.
- `pytest`: 17 tests passed.
