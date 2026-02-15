"""Test complet du système Alpha AI Trading — 100 cycles de simulation."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alpha_system.orchestrator import AlphaOrchestrator


def run_test(cycles=100):

    print("=" * 60)
    print("  ALPHA AI TRADING — TEST SIMULATION")
    print(f"  Cycles: {cycles}")
    print("=" * 60)

    system = AlphaOrchestrator()

    results = {}
    errors = 0

    for i in range(1, cycles + 1):

        try:
            print(f"\n{'='*40} Cycle {i}/{cycles} {'='*40}")

            result = system.cycle()
            results[result] = results.get(result, 0) + 1

            print(f"  -> {result}")

        except Exception as e:
            errors += 1
            print(f"  ERROR cycle {i}: {e}")

    # Rapport final
    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)

    print(f"\n  Cycles: {cycles}")
    print(f"  Errors: {errors}")

    print("\n  Results:")
    for k, v in sorted(results.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    system.report()

    print("\n  Simulation complete")


if __name__ == "__main__":
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_test(cycles)
