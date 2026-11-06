"""Quine-McCluskey (tabulation) Boolean minimiser with Petrick's method."""
from typing import Dict, List, Set


class QuineMcCluskeySolver:
    MAX_VARS = 6

    def __init__(self, num_vars: int, minterms: List[int], dont_cares: List[int] = None):
        if not 2 <= num_vars <= self.MAX_VARS:
            raise ValueError(f"num_vars must be between 2 and {self.MAX_VARS}.")
        size = 1 << num_vars
        for t in list(minterms) + list(dont_cares or []):
            if not 0 <= t < size:
                raise ValueError(f"Term {t} is out of range 0..{size - 1} for {num_vars} variables.")
        self.n = num_vars
        self.vars = [chr(65 + i) for i in range(num_vars)]
        self.minterms = sorted(set(minterms))
        self.dont_cares = sorted(set(dont_cares or []) - set(self.minterms))
        self.all_terms = sorted(self.minterms + self.dont_cares)

    # ---------- helpers ----------
    def _bin(self, v: int) -> str:
        return format(v, f"0{self.n}b")

    def _lits(self, mask: str) -> int:
        return self.n - mask.count("-")

    def _expr(self, mask: str) -> str:
        s = "".join(v if b == "1" else v + "'" for v, b in zip(self.vars, mask) if b != "-")
        return s or "1"

    @staticmethod
    def _merge(a: str, b: str):
        diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(diff) != 1:
            return None
        return a[:diff[0]] + "-" + a[diff[0] + 1:]

    # ---------- Phase 1: tabulation ----------
    def find_prime_implicants(self):
        groups: Dict[int, Dict[str, Set[int]]] = {}
        for m in self.all_terms:
            b = self._bin(m)
            groups.setdefault(b.count("1"), {})[b] = {m}

        primes: Dict[str, Set[int]] = {}
        columns = []
        while groups:
            nxt: Dict[int, Dict[str, Set[int]]] = {}
            used: Set[str] = set()
            keys = sorted(groups)
            for g1, g2 in zip(keys, keys[1:]):
                if g2 - g1 != 1:
                    continue
                for t1, c1 in groups[g1].items():
                    for t2, c2 in groups[g2].items():
                        merged = self._merge(t1, t2)
                        if merged:
                            used.update((t1, t2))
                            nxt.setdefault(merged.count("1"), {}).setdefault(merged, set()).update(c1 | c2)
            columns.append([
                {"ones": k, "terms": [
                    {"mask": t, "covers": sorted(c), "combined": t in used} for t, c in sorted(groups[k].items())
                ]} for k in keys
            ])
            for g in groups.values():
                for t, c in g.items():
                    if t not in used:
                        primes[t] = c
            groups = nxt
        return primes, columns

    # ---------- Phase 2: essential PIs + Petrick ----------
    def _petrick(self, uncovered: Set[int], pis: Dict[str, Set[int]]):
        products = [frozenset()]
        for m in sorted(uncovered):
            clause = [p for p in pis if m in pis[p]]
            new = {p | {c} for p in products for c in clause}
            kept: List[frozenset] = []
            for p in sorted(new, key=len):          # absorption law: X + XY = X
                if not any(k <= p for k in kept):
                    kept.append(p)
            products = kept
        best = min(products, key=lambda p: (len(p), sum(self._lits(x) for x in p)))
        return best, products

    def solve(self) -> Dict:
        canon = len(self.minterms) * self.n
        if not self.minterms:
            return self._pack("0", {}, [], [], [], [], [], canon)
        pis, columns = self.find_prime_implicants()
        epis = []
        for m in self.minterms:
            cov = [p for p in pis if m in pis[p]]
            if len(cov) == 1 and cov[0] not in epis:
                epis.append(cov[0])
        uncovered = set(self.minterms)
        for e in epis:
            uncovered -= pis[e]
        selected = list(epis)
        petrick = []
        if uncovered:
            best, petrick = self._petrick(uncovered, pis)
            selected += sorted(best)
        sop = " + ".join(self._expr(p) for p in selected)
        return self._pack(sop, pis, columns, epis, selected, petrick, sorted(uncovered), canon)

    def _pack(self, sop, pis, columns, epis, selected, petrick, cyclic, canon):
        lits = sum(self._lits(p) for p in selected)
        truth = []
        for i in range(1 << self.n):
            truth.append({"dec": i, "bits": self._bin(i),
                          "f": "1" if i in self.minterms else "X" if i in self.dont_cares else "0"})
        return {
            "variables": self.vars, "minterms": self.minterms, "dont_cares": self.dont_cares,
            "minimal_sop": sop, "tabulation": columns,
            "prime_implicants": [
                {"mask": m, "expr": self._expr(m), "covers": sorted(c),
                 "essential": m in epis, "selected": m in selected}
                for m, c in sorted(pis.items(), key=lambda kv: (-kv[1].__len__(), kv[0]))],
            "essential": [self._expr(p) for p in epis],
            "cyclic_minterms": cyclic,
            "petrick_products": [sorted(self._expr(x) for x in p) for p in petrick],
            "selected": [self._expr(p) for p in selected],
            "truth_table": truth,
            "verified": self._verify(selected),
            "verilog": self._verilog(selected),
            "metrics": {
                "canonical_literals": canon, "minimized_literals": lits,
                "reduction_pct": round((1 - lits / canon) * 100, 1) if canon else 0.0,
                "terms": len(selected),
                "and_gates": sum(1 for p in selected if self._lits(p) > 1),
                "or_gates": 1 if len(selected) > 1 else 0,
                "prime_implicants": len(pis), "essential_pis": len(epis),
                "tabulation_rounds": len(columns),
            },
        }

    def _verify(self, selected) -> bool:
        """Re-evaluate the SOP on every input row; must match the specification."""
        for i in range(1 << self.n):
            b = self._bin(i)
            val = any(all(c == "-" or c == x for c, x in zip(p, b)) for p in selected)
            if i in self.minterms and not val:
                return False
            if i not in self.minterms and i not in self.dont_cares and val:
                return False
        return True

    def _verilog(self, selected) -> str:
        terms = []
        for p in selected:
            parts = [("" if b == "1" else "~") + v for v, b in zip(self.vars, p) if b != "-"]
            terms.append("(" + " & ".join(parts) + ")" if parts else "1'b1")
        body = " |\n             ".join(terms) if terms else "1'b0"
        return (f"module boolean_minimized (\n  input  wire {', '.join(self.vars)},\n  output wire F\n);\n"
                f"  assign F = {body};\nendmodule")


def simplify(num_vars, minterms, dont_cares=None):
    return QuineMcCluskeySolver(num_vars, minterms, dont_cares).solve()


if __name__ == "__main__":
    r = simplify(4, [0, 1, 2, 5, 6, 7, 8, 9, 10, 14], [4, 15])
    print("F =", r["minimal_sop"], "| verified:", r["verified"], "|", r["metrics"])
