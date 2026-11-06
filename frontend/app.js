const $ = id => document.getElementById(id);
const PRESETS = {
  "Worked example: Σm(0,1,2,5,6,7,8,9,10,14)+d(4,15)": [4, "0,1,2,5,6,7,8,9,10,14", "4,15"],
  "BCD to 7-segment 'a' decoder": [4, "0,2,3,5,6,7,8,9", "10,11,12,13,14,15"],
  "4-bit prime number detector": [4, "2,3,5,7,11,13", ""],
  "Cyclic cover (Petrick) 3-var": [3, "0,1,2,5,6,7", ""],
  "5-variable example": [5, "0,1,4,5,16,17,20,21,23,29,31", "2,18"],
};
const history = [];
let last = null;

$("preset").innerHTML = Object.keys(PRESETS).map(k => `<option>${k}</option>`).join("");
$("preset").onchange = () => {
  const [n, m, d] = PRESETS[$("preset").value];
  $("nvars").value = n; $("mt").value = m; $("dc").value = d; run();
};

const parse = s => s.split(/[\s,]+/).filter(Boolean).map(Number);

async function run() {
  $("err").textContent = "";
  const body = { num_vars: +$("nvars").value, minterms: parse($("mt").value), dont_cares: parse($("dc").value) };
  if ([...body.minterms, ...body.dont_cares].some(x => !Number.isInteger(x)))
    return ($("err").textContent = "Enter whole numbers separated by commas.");
  try {
    const res = await fetch("/api/simplify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Server error");
    last = data; render(data, body);
  } catch (e) { $("err").textContent = e.message; }
}

function render(r, body) {
  const m = r.metrics, n = r.variables.length;
  $("sop").textContent = `F(${r.variables.join(",")}) = ${r.minimal_sop}`;
  $("ver").textContent = r.verified ? "✓ verified vs truth table" : "✗ mismatch";
  $("ver").className = "chip " + (r.verified ? "ok" : "bad");
  $("kLit").textContent = m.minimized_literals; $("kCanon").textContent = ` of ${m.canonical_literals} canonical`;
  $("kRed").textContent = m.reduction_pct + "%";
  $("kPi").textContent = m.prime_implicants; $("kEpi").textContent = ` ${m.essential_pis} essential`;
  $("kGate").textContent = m.and_gates + m.or_gates; 

  // Tabulation columns
  $("tab").innerHTML = r.tabulation.length ? r.tabulation.map((col, i) => `
    <div class="col"><h3>Column ${i + 1}${i === 0 ? " (minterms + d)" : ` (size-${2 ** i} groups)`}</h3>
    ${col.map(g => `<div class="grp">${g.terms.map(t => `
      <div class="t ${t.combined ? "" : "pi"}"><span>${t.mask}</span><i>${t.covers.join(",")}</i>
      <span class="ck">${t.combined ? "✓" : "PI"}</span></div>`).join("")}</div>`).join("")}</div>`).join("")
    : "<p class='hint'>No minterms: F = 0.</p>";

  // PI chart
  const mts = r.minterms;
  const owners = Object.fromEntries(mts.map(x => [x, r.prime_implicants.filter(p => p.covers.includes(x)).length]));
  $("chart").innerHTML = `<tr><th>Prime implicant</th><th>Mask</th>${mts.map(x => `<th>${x}</th>`).join("")}<th>Role</th></tr>` +
    r.prime_implicants.map(p => `<tr class="${p.selected ? "sel" : ""}"><td>${p.expr}</td><td>${p.mask}</td>
      ${mts.map(x => p.covers.includes(x) ? `<td class="${owners[x] === 1 ? "star" : "dot"}">${owners[x] === 1 ? "★" : "×"}</td>` : "<td></td>").join("")}
      <td><span class="tag ${p.essential ? "e" : p.selected ? "s" : "r"}">${p.essential ? "Essential" : p.selected ? "Selected (Petrick)" : "Redundant"}</span></td></tr>`).join("");
  $("petrick").innerHTML = r.cyclic_minterms.length
    ? `<b>Petrick's method</b> resolves cyclic minterms {${r.cyclic_minterms.join(", ")}}. Candidate covers after absorption: ` +
      r.petrick_products.map(p => `<code>${p.join(" + ")}</code>`).join(" &nbsp;|&nbsp; ") + ". The cheapest (fewest terms, then literals) is chosen."
    : "All minterms are covered by essential prime implicants, so Petrick's method is not needed.";

  // Truth table (click to toggle)
  $("tt").innerHTML = `<tr><th>Dec</th>${r.variables.map(v => `<th>${v}</th>`).join("")}<th>F</th></tr>` +
    r.truth_table.map(t => `<tr data-i="${t.dec}"><td>${t.dec}</td>${[...t.bits].map(b => `<td>${b}</td>`).join("")}
      <td class="${t.f === "1" ? "f1" : t.f === "X" ? "fx" : ""}">${t.f}</td></tr>`).join("");
  document.querySelectorAll("#tt tr[data-i]").forEach(tr => tr.onclick = () => toggle(+tr.dataset.i));

  $("v").textContent = r.verilog;

  // History chart
  const label = `${n}v #${history.length + 1}`;
  if (!history.length || history[history.length - 1].key !== JSON.stringify(body))
    history.push({ key: JSON.stringify(body), label, canon: m.canonical_literals, min: m.minimized_literals });
  drawBars();
}

function toggle(i) {
  const mt = new Set(parse($("mt").value)), dc = new Set(parse($("dc").value));
  if (mt.has(i)) { mt.delete(i); dc.add(i); } else if (dc.has(i)) dc.delete(i); else mt.add(i);
  const f = s => [...s].sort((a, b) => a - b).join(",");
  $("mt").value = f(mt); $("dc").value = f(dc); run();
}

function drawBars() {
  const c = $("bar"), g = c.getContext("2d"), css = getComputedStyle(document.body);
  const runs = history.slice(-6), max = Math.max(1, ...runs.map(r => r.canon));
  g.clearRect(0, 0, c.width, c.height); g.font = "11px system-ui";
  const bw = 20, gap = (c.width - 20) / runs.length;
  runs.forEach((r, i) => {
    const x = 16 + i * gap, h = v => (v / max) * 150;
    g.fillStyle = css.getPropertyValue("--bd"); g.fillRect(x, 180 - h(r.canon), bw, h(r.canon));
    g.fillStyle = css.getPropertyValue("--ac"); g.fillRect(x + bw + 3, 180 - h(r.min), bw, h(r.min));
    g.fillStyle = css.getPropertyValue("--tx"); g.fillText(r.canon, x, 176 - h(r.canon)); g.fillText(r.min, x + bw + 3, 176 - h(r.min));
    g.fillStyle = css.getPropertyValue("--mu"); g.fillText(r.label, x, 198);
  });
  $("hist").textContent = "Grey = canonical literals, blue = minimized literals (your last runs).";
}

$("go").onclick = run;
$("copy").onclick = () => navigator.clipboard.writeText($("v").textContent).then(() => { $("copy").textContent = "Copied ✓"; setTimeout(() => $("copy").textContent = "Copy", 1500); });
run();
