# Boolean Expression Simplification using the Tabulation (Quine-McCluskey) Method

Digital Circuit Design project. A Python engine minimises Boolean functions with the
**tabulation method** + **Petrick's method**, and a web dashboard shows every step.

## Structure
- `backend/qm_solver.py` - Quine-McCluskey tabulation, essential PIs, Petrick's method, verification, Verilog.
- `backend/test_benchmarks.py` - benchmarks + 300 random functions checked against the truth table.
- `api/simplify.py` - serverless endpoint (`POST /api/simplify`) that calls the solver.
- `server.py` - local server (no dependencies) serving the dashboard and the API.
- `frontend/` - dashboard (tabulation columns, PI chart, Petrick, KPIs, truth table, Verilog).
- `docs/project_report.md` - report with algorithm and worked example.

## Run locally
```bash
python backend/test_benchmarks.py     # verify the algorithm
python server.py                      # open http://localhost:3000
```

## Deploy (Vercel)
1. Push this folder to a new GitHub repo.
2. vercel.com -> Add New Project -> import the repo -> Deploy (no settings needed;
   `vercel.json` serves `frontend/` and runs `api/simplify.py` as a Python function).
Or from a terminal: `npm i -g vercel && vercel --prod`.

Supports 2-6 variables, with don't-care terms.
