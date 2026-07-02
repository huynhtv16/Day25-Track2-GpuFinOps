"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing, sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    reasoning_cost = reasoning_wh = 0.0
    reasoning_requests = 0
    cache_candidates = cache_enabled = 0
    total_tokens = 0
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        is_reasoning = bool(int(num(r["is_reasoning"])))
        total_tokens += inp + out
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        cache_decision = pricing.cache_is_worth_it(cached, expected_reads=1, price_in_per_m=pin)
        billable_cached = cached if cache_decision["worth_it"] else 0
        if cached > 0:
            cache_candidates += 1
        if billable_cached > 0:
            cache_enabled += 1
        row_cost = pricing.request_cost(inp, out, pin, pout, cached_in=billable_cached, batch=is_batch)
        opt_cost += row_cost
        if is_reasoning:
            reasoning_requests += 1
            reasoning_cost += row_cost
            reasoning_wh += sustainability.wh_per_query(inp + out, is_reasoning=True)

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"cache gate: {cache_enabled}/{cache_candidates} cached prompts pass break-even")
        print(f"reasoning : {reasoning_requests} requests, ${reasoning_cost:.2f}/day, {reasoning_wh:.0f} Wh/day")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "cache_candidates": cache_candidates, "cache_enabled": cache_enabled,
        "reasoning_requests": reasoning_requests,
        "reasoning_daily": round(reasoning_cost, 2),
        "reasoning_wh_daily": round(reasoning_wh, 2),
    }


if __name__ == "__main__":
    run()
