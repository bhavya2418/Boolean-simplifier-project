import itertools, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qm_solver import simplify

BENCHMARKS = [
    ("Worked example (4-var, don't cares)", 4, [0, 1, 2, 5, 6, 7, 8, 9, 10, 14], [4, 15]),
    ("BCD to 7-segment 'a' decoder", 4, [0, 2, 3, 5, 6, 7, 8, 9], [10, 11, 12, 13, 14, 15]),
    ("4-bit prime detector", 4, [2, 3, 5, 7, 11, 13], []),
    ("Cyclic-cover example (Petrick needed)", 3, [0, 1, 2, 5, 6, 7], []),
    ("5-variable example", 5, [0, 1, 4, 5, 16, 17, 20, 21, 23, 29, 31], [2, 18]),
]

def run():
    print("=" * 70, "\n QUINE-McCLUSKEY TABULATION - BENCHMARK & VERIFICATION SUITE\n", "=" * 70, sep="")
    for name, n, m, d in BENCHMARKS:
        r = simplify(n, m, d); k = r["metrics"]
        print(f"\n{name}\n  F = {r['minimal_sop']}\n  PIs={k['prime_implicants']} EPIs={k['essential_pis']} "
              f"literals {k['canonical_literals']}->{k['minimized_literals']} ({k['reduction_pct']}%)  verified={r['verified']}")
        assert r["verified"]
    rnd = random.Random(1)
    for _ in range(300):                      # random functions must always verify
        n = rnd.randint(2, 5); idx = list(range(1 << n)); rnd.shuffle(idx)
        a = rnd.randint(0, len(idx)); b = rnd.randint(0, len(idx) - a)
        assert simplify(n, idx[:a], idx[a:a + b])["verified"]
    print("\nAll benchmarks + 300 random functions verified against the truth table.")

if __name__ == "__main__":
    run()
