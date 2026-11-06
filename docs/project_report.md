# Boolean Expression Simplification using the Tabulation Method

## 1. Objective
Minimise a Boolean function given as minterms (and don't cares) using the Quine-McCluskey
tabulation method, implemented in Python, and present each step in a web dashboard.

## 2. Algorithm
1. **Group** all minterms and don't cares as binary strings by their number of 1s.
2. **Merge** terms in adjacent groups that differ in exactly one bit, replacing that bit with `-`. Tick merged terms. Repeat on the new column until nothing merges.
3. **Prime implicants (PIs)** are the unticked terms from every column.
4. **PI chart**: rows = PIs, columns = minterms (don't cares excluded). A column with a single mark gives an **essential PI**.
5. **Petrick's method** for minterms left uncovered: write (sum of PIs covering m) for each m, multiply out, apply absorption (X + XY = X), and pick the product with the fewest terms, then fewest literals.
6. **Verify**: the final SOP is evaluated on every input row and compared with the specification.

## 3. Worked example
F(A,B,C,D) = Σm(0,1,2,5,6,7,8,9,10,14) + d(4,15)

| PI | Mask | Covers |
|----|------|--------|
| B'C' | -00- | 0,1,8,9 |
| B'D' | -0-0 | 0,2,8,10 |
| A'D' | 0--0 | 0,2,4,6 |
| A'B | 01-- | 4,5,6,7 |
| CD' | --10 | 2,6,10,14 |
| BC | -11- | 6,7,14,15 |

Essential PIs: B'C' (minterm 9) and A'B (minterm 5). Remaining {2,10,14} are covered by CD'.
**F = B'C' + A'B + CD'** - literals reduced from 40 to 6 (85%).

## 4. Results
`python backend/test_benchmarks.py` runs 5 benchmarks (including a cyclic-cover case needing Petrick) and 300 random functions; every result is verified against its truth table.
