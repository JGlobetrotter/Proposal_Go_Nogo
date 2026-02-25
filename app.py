pip install streamlit reportlab
streamlit run app.py

# ─── Palette ───────────────────────────────────────────────────────────────
const C = {
  bg:          "#1a1a1a",   // near-black page background
  panel:       "#222222",   // panel / header background
  card:        "#2a2a2a",   // card & input background
  cardBorder:  "#333333",   // subtle border
  divider:     "#2f2f2f",   // divider lines
  yellow:      "#f5c518",   // primary accent
  yellowDim:   "#f5c51820", // yellow low-opacity fill
  yellowMid:   "#f5c51855", // yellow mid-opacity border
  white:       "#ffffff",
  offWhite:    "#e8e8e8",
  grey1:       "#aaaaaa",   // muted text
  grey2:       "#666666",   // very muted / labels
  grey3:       "#3a3a3a",   // inactive borders
};

# ─── Sections config ───────────────────────────────────────────────────────
const SECTIONS = [
  {
    key: "strategic_fit", label: "Strategic Fit", icon: "◎",
    questions: [
      "Aligns with our organizational mission?",
      "Builds on existing programs or expertise?",
      "Strengthens key donor relationships?",
      "Advances long-term strategic goals?",
    ],
  },
  {
    key: "organizational_capacity", label: "Organizational Capacity", icon: "⬡",
    questions: [
      "Sufficient staff expertise available?",
      "Adequate time to prepare a quality proposal?",
      "Established relationships in target geography?",
      "Past performance on similar grants?",
    ],
  },
  {
    key: "financial_viability", label: "Financial Viability", icon: "◈",
    questions: [
      "Budget covers full cost of delivery?",
      "Acceptable overhead and indirect rate?",
      "Cash-flow manageable during project?",
      "Reporting requirements are feasible?",
    ],
  },
  {
    key: "risk_assessment", label: "Risk Assessment", icon: "△",
    questions: [
      "Political / security environment is stable?",
      "Low risk of scope creep or mission drift?",
      "Manageable compliance requirements?",
      "Reputational risk is acceptable?",
    ],
  },
];

const SCORE_LABELS = ["", "Very Low", "Low", "Moderate", "High", "Very High"];

function initScores() {
  const s = {};
  SECTIONS.forEach(sec => { s[sec.key] = sec.questions.map(() => 0); });
  return s;
}

function computeVerdict(scores) {
  let total = 0, maxTotal = 0;
  const sectionResults = SECTIONS.map(sec => {
    const score = scores[sec.key].reduce((a, b) => a + b, 0);
    const max = sec.questions.length * 5;
    total += score; maxTotal += max;
    return { ...sec, score, max, pct: score / max };
  });
  const pct = total / maxTotal;
  let verdict, verdictColor, emoji;
  if (pct >= 0.7)      { verdict = "GO";                   verdictColor = C.yellow;   emoji = "●"; }
  else if (pct >= 0.5) { verdict = "PROCEED WITH CAUTION"; verdictColor = C.offWhite; emoji = "◐"; }
  else                 { verdict = "NO-GO";                verdictColor = C.grey1;    emoji = "○"; }
  return { verdict, verdictColor, emoji, total, maxTotal, pct, sectionResults };
}

function strength(pct) {
  if (pct >= 0.7) return { label: "Strong",   color: C.yellow };
  if (pct >= 0.5) return { label: "Moderate", color: C.offWhite };
  return              { label: "Weak",     color: C.grey1 };
}

function buildCLI(meta, scores) {
  const sum = key => scores[key].reduce((a, b) => a + b, 0);
  const qs  = key => SECTIONS.find(s => s.key === key).questions
    .map((q, i) => `"${q}:${scores[key][i]},5"`).join(" \\\n    ");
  return `python generate_report.py \\
  --org "${meta.org}" \\
  --title "${meta.title}" \\
  --donor "${meta.donor}" \\
  --deadline "${meta.deadline}" \\
  --evaluator "${meta.evaluator}" \\
  --sf ${sum("strategic_fit")} --sf-q \\
    ${qs("strategic_fit")} \\
  --oc ${sum("organizational_capacity")} --oc-q \\
    ${qs("organizational_capacity")} \\
  --fv ${sum("financial_viability")} --fv-q \\
    ${qs("financial_viability")} \\
  --ra ${sum("risk_assessment")} --ra-q \\
    ${qs("risk_assessment")} \\
  --notes "${meta.notes}" \\
  --output "${(meta.title || "report").replace(/\s+/g, "_").toLowerCase()}_report.pdf"`;
}

# ─── Sub-components ────────────────────────────────────────────────────────
function ScoreBar({ pct, height = 4 }) {
  const fill = pct >= 0.7 ? C.yellow : pct >= 0.5 ? `${C.yellow}99` : C.grey2;
  return (
    <div style={{ background: C.grey3, borderRadius: 99, overflow: "hidden", height }}>
      <div style={{ width: `${Math.max(0, pct) * 100}%`, height: "100%", background: fill, borderRadius: 99, transition: "width 0.35s ease" }} />
    </div>
  );
}

function ScorePicker({ value, onChange }) {
  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      {[1,2,3,4,5].map(n => (
        <button key={n} onClick={() => onChange(n === value ? 0 : n)} title={SCORE_LABELS[n]}
          style={{
            width: 26, height: 26, borderRadius: "50%", flexShrink: 0,
            border: `2px solid ${n <= value ? C.yellow : C.grey3}`,
            background: n <= value ? C.yellow : "transparent",
            cursor: "pointer", fontSize: 10, fontWeight: 700,
            color: n <= value ? C.bg : C.grey2,
            transition: "all 0.12s",
          }}>
          {n}
        </button>
      ))}
      <span style={{ fontSize: 10.5, fontFamily: "monospace", color: value ? C.yellow : C.grey2, fontWeight: 600, minWidth: 58 }}>
        {value ? SCORE_LABELS[value] : "—"}
      </span>
    </div>
  );
}

function InputField({ label, value, onChange, placeholder, type, span2 }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ gridColumn: span2 ? "span 2" : "span 1" }}>
      <label style={{ display: "block", fontSize: 9.5, letterSpacing: "0.12em", color: C.grey2, fontFamily: "monospace", marginBottom: 5, textTransform: "uppercase" }}>
        {label}
      </label>
      <input type={type || "text"} placeholder={placeholder} value={value}
        onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
        style={{
          width: "100%", boxSizing: "border-box", padding: "8px 11px", borderRadius: 5,
          border: `1px solid ${focused ? C.yellow : C.cardBorder}`,
          background: C.card, color: C.offWhite,
          fontSize: 12.5, fontFamily: "'Helvetica Neue', Helvetica, sans-serif", outline: "none",
          transition: "border-color 0.15s",
        }}
      />
    </div>
  );
}

function Label({ children, extra }) {
  return (
    <div style={{ fontSize: 9.5, letterSpacing: "0.16em", color: C.grey2, fontFamily: "monospace", textTransform: "uppercase", marginBottom: 10, ...extra }}>
      {children}
    </div>
  );
}

# ─── App ───────────────────────────────────────────────────────────────────
export default function GoNoGoIntake() {
  const [meta, setMeta]           = useState({ org:"", title:"", donor:"", deadline:"", evaluator:"", notes:"" });
  const [scores, setScores]       = useState(initScores);
  const [activeKey, setActiveKey] = useState(SECTIONS[0].key);
  const [showCLI, setShowCLI]     = useState(false);
  const [copied, setCopied]       = useState(false);

  const results   = computeVerdict(scores);
  const answered  = Object.values(scores).flat().filter(v => v > 0).length;
  const totalQ    = SECTIONS.reduce((a, s) => a + s.questions.length, 0);
  const activeSec = SECTIONS.find(s => s.key === activeKey);

  const setM  = key => val => setMeta(p => ({ ...p, [key]: val }));
  const setQ  = (secKey, qi, val) => setScores(p => ({ ...p, [secKey]: p[secKey].map((v,i) => i===qi ? val : v) }));
  const copy  = () => { navigator.clipboard.writeText(buildCLI(meta, scores)).then(() => { setCopied(true); setTimeout(()=>setCopied(false),2000); }); };

  const panelHead = { padding: "22px 26px 18px", background: C.panel, borderBottom: `1px solid ${C.divider}`, flexShrink: 0 };
  const mono      = { fontFamily: "monospace" };
  const sans      = { fontFamily: "'Helvetica Neue', Helvetica, sans-serif" };

  return (
    <div style={{ display:"flex", height:"100vh", background:C.bg, color:C.white, fontFamily:"'Georgia','Times New Roman',serif", overflow:"hidden" }}>

      {/* ══ LEFT PANEL ══════════════════════════════════════════════════════ */}
      <div style={{ width:"52%", display:"flex", flexDirection:"column", borderRight:`1px solid ${C.divider}`, overflow:"hidden" }}>

        {/* Header */}
        <div style={panelHead}>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:3 }}>
            <div style={{ width:7, height:7, borderRadius:"50%", background:C.yellow, boxShadow:`0 0 8px ${C.yellow}88` }} />
            <span style={{ ...mono, fontSize:9.5, letterSpacing:"0.2em", color:C.yellow, textTransform:"uppercase" }}>Proposal Assessment Tool</span>
          </div>
          <h1 style={{ margin:"2px 0 2px", fontSize:21, fontWeight:400, color:C.white, letterSpacing:"-0.01em" }}>
            Go / No-Go Diagnostic
          </h1>
          <p style={{ ...sans, margin:0, fontSize:11.5, color:C.grey1 }}>
            Evaluate proposal readiness across four dimensions
          </p>
          <div style={{ marginTop:14 }}>
            <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
              <span style={{ ...mono, fontSize:9.5, color:C.grey2 }}>COMPLETION</span>
              <span style={{ ...mono, fontSize:9.5, color:C.yellow }}>{answered} / {totalQ}</span>
            </div>
            <ScoreBar pct={answered/totalQ} height={3} />
          </div>
        </div>

        {/* Body */}
        <div style={{ overflowY:"auto", flex:1, padding:"20px 26px" }}>

          <Label>Proposal Details</Label>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:24 }}>
            <InputField label="Organisation"        value={meta.org}       onChange={setM("org")}       placeholder="Hope Bridge Foundation"          span2 />
            <InputField label="Proposal Title"      value={meta.title}     onChange={setM("title")}     placeholder="Clean Water Access – Rural Kenya" span2 />
            <InputField label="Donor / Funder"      value={meta.donor}     onChange={setM("donor")}     placeholder="USAID" />
            <InputField label="Submission Deadline" value={meta.deadline}  onChange={setM("deadline")}  placeholder="2025-06-30" type="date" />
            <InputField label="Evaluator Name"      value={meta.evaluator} onChange={setM("evaluator")} placeholder="Your name" span2 />
          </div>

          <Label>Scoring Sections</Label>
          <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginBottom:14 }}>
            {SECTIONS.map(sec => {
              const s = scores[sec.key].reduce((a,b)=>a+b,0);
              const m = sec.questions.length * 5;
              const on = activeKey === sec.key;
              return (
                <button key={sec.key} onClick={() => setActiveKey(sec.key)}
                  style={{
                    ...mono, padding:"6px 12px", borderRadius:5, cursor:"pointer", fontSize:11,
                    border:`1px solid ${on ? C.yellow : C.grey3}`,
                    background: on ? C.yellowDim : "transparent",
                    color: on ? C.yellow : C.grey1,
                    display:"flex", alignItems:"center", gap:6, transition:"all 0.12s",
                  }}>
                  <span style={{ fontSize:13 }}>{sec.icon}</span>
                  <span>{sec.label}</span>
                  <span style={{ background: on ? C.yellowMid : C.cardBorder, color: on ? C.yellow : C.grey2, borderRadius:3, padding:"1px 5px", fontSize:9.5 }}>
                    {s}/{m}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Questions */}
          {activeSec && (
            <div style={{ background:C.card, borderRadius:8, border:`1px solid ${C.yellowMid}`, overflow:"hidden", marginBottom:20 }}>
              <div style={{ padding:"11px 15px", background:C.yellowDim, borderBottom:`1px solid ${C.yellowMid}`, display:"flex", alignItems:"center", gap:8 }}>
                <span style={{ color:C.yellow, fontSize:14 }}>{activeSec.icon}</span>
                <span style={{ ...sans, fontSize:12.5, color:C.yellow, fontWeight:600 }}>{activeSec.label}</span>
              </div>
              {activeSec.questions.map((q, qi) => (
                <div key={qi} style={{ padding:"13px 15px", borderBottom: qi < activeSec.questions.length-1 ? `1px solid ${C.divider}` : "none" }}>
                  <div style={{ ...sans, fontSize:12.5, color:C.offWhite, marginBottom:9, lineHeight:1.4 }}>
                    {qi+1}. {q}
                  </div>
                  <ScorePicker value={scores[activeSec.key][qi]} onChange={val => setQ(activeSec.key, qi, val)} />
                </div>
              ))}
            </div>
          )}

          <Label>Evaluator Notes (optional)</Label>
          <textarea rows={3}
            placeholder="Any context, caveats, or observations about this proposal..."
            value={meta.notes}
            onChange={e => setMeta(p => ({ ...p, notes:e.target.value }))}
            style={{
              ...sans, width:"100%", boxSizing:"border-box",
              padding:"9px 11px", borderRadius:5,
              border:`1px solid ${C.cardBorder}`,
              background:C.card, color:C.offWhite,
              fontSize:12.5, resize:"vertical", outline:"none",
            }}
            onFocus={e => e.target.style.borderColor = C.yellow}
            onBlur={e  => e.target.style.borderColor = C.cardBorder}
          />
          <div style={{ height:24 }} />
        </div>
      </div>

      {/* ══ RIGHT PANEL ═════════════════════════════════════════════════════ */}
      <div style={{ width:"48%", display:"flex", flexDirection:"column", overflow:"hidden" }}>

        {/* Verdict header */}
        <div style={panelHead}>
          <div style={{ ...mono, fontSize:9.5, letterSpacing:"0.16em", color:C.grey2, textTransform:"uppercase", marginBottom:10 }}>Live Results</div>
          <div style={{ display:"inline-flex", alignItems:"center", gap:12, padding:"10px 18px", borderRadius:7, background:C.yellowDim, border:`1.5px solid ${C.yellowMid}` }}>
            <span style={{ fontSize:20, color:results.verdictColor, lineHeight:1 }}>{results.emoji}</span>
            <div>
              <div style={{ ...sans, fontSize:15, fontWeight:700, color:results.verdictColor, letterSpacing:"0.05em" }}>{results.verdict}</div>
              <div style={{ ...mono, fontSize:10.5, color:C.grey1 }}>{results.total} / {results.maxTotal} pts · {(results.pct*100).toFixed(0)}%</div>
            </div>
          </div>
          <div style={{ marginTop:12 }}><ScoreBar pct={results.pct} height={4} /></div>
        </div>

        <div style={{ overflowY:"auto", flex:1, padding:"20px 26px" }}>

          <Label>Section Breakdown</Label>
          <div style={{ display:"flex", flexDirection:"column", gap:8, marginBottom:22 }}>
            {results.sectionResults.map(sec => {
              const s = strength(sec.pct);
              return (
                <div key={sec.key} style={{ background:C.card, borderRadius:7, border:`1px solid ${C.cardBorder}`, padding:"10px 13px" }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:7 }}>
                    <div style={{ display:"flex", alignItems:"center", gap:7 }}>
                      <span style={{ color:C.grey2, fontSize:12 }}>{sec.icon}</span>
                      <span style={{ ...sans, fontSize:12, color:C.offWhite }}>{sec.label}</span>
                    </div>
                    <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                      <span style={{ ...mono, fontSize:10.5, color:s.color, fontWeight:600 }}>{s.label}</span>
                      <span style={{ ...mono, fontSize:10.5, color:C.grey2 }}>{sec.score}/{sec.max}</span>
                    </div>
                  </div>
                  <ScoreBar pct={sec.pct} height={4} />
                </div>
              );
            })}
          </div>

          <Label>Recommendation</Label>
          <div style={{ background:C.card, borderRadius:7, border:`1px solid ${C.cardBorder}`, padding:"13px 15px", marginBottom:22 }}>
            {results.pct >= 0.7 && (
              <p style={{ ...sans, margin:0, fontSize:12.5, color:C.grey1, lineHeight:1.65 }}>
                This proposal demonstrates <strong style={{ color:C.yellow }}>strong readiness</strong> across all dimensions. Proceed with full team commitment. Assign a lead writer and schedule kick-off within 5 working days.
              </p>
            )}
            {results.pct >= 0.5 && results.pct < 0.7 && (
              <p style={{ ...sans, margin:0, fontSize:12.5, color:C.grey1, lineHeight:1.65 }}>
                This proposal shows <strong style={{ color:C.offWhite }}>moderate readiness</strong>. Proceed conditionally — address weak areas before committing full resources. Obtain senior sign-off and develop a risk mitigation plan.
              </p>
            )}
            {results.pct < 0.5 && (
              <p style={{ ...sans, margin:0, fontSize:12.5, color:C.grey1, lineHeight:1.65 }}>
                This proposal has <strong style={{ color:C.grey1 }}>critical gaps</strong> across multiple dimensions. Declining preserves capacity for stronger opportunities. Document lessons learned and consider a sub-grantee role if still viable.
              </p>
            )}
          </div>

          {/* CLI */}
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:10 }}>
            <Label extra={{ marginBottom:0 }}>Generate PDF Report</Label>
            <button onClick={() => setShowCLI(p=>!p)}
              style={{ ...mono, fontSize:9.5, padding:"4px 10px", borderRadius:4, border:`1px solid ${C.grey3}`, background:"transparent", color:C.grey2, cursor:"pointer" }}
              onMouseEnter={e=>{e.currentTarget.style.borderColor=C.yellow;e.currentTarget.style.color=C.yellow;}}
              onMouseLeave={e=>{e.currentTarget.style.borderColor=C.grey3;e.currentTarget.style.color=C.grey2;}}
            >
              {showCLI ? "Hide" : "Show"} command
            </button>
          </div>

          {showCLI && (
            <div style={{ background:"#111", borderRadius:7, border:`1px solid ${C.cardBorder}`, overflow:"hidden", marginBottom:16 }}>
              <div style={{ padding:"7px 13px", borderBottom:`1px solid ${C.divider}`, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                <span style={{ ...mono, fontSize:9.5, color:C.grey2 }}>$ terminal</span>
                <button onClick={copy} style={{ ...mono, fontSize:9.5, padding:"3px 10px", borderRadius:4, border:`1px solid ${copied?C.yellow+"66":C.grey3}`, background:copied?C.yellowDim:"transparent", color:copied?C.yellow:C.grey2, cursor:"pointer", transition:"all 0.15s" }}>
                  {copied ? "✓ Copied!" : "Copy"}
                </button>
              </div>
              <pre style={{ ...mono, margin:0, padding:"13px", fontSize:10, lineHeight:1.7, color:C.offWhite, whiteSpace:"pre-wrap", wordBreak:"break-all", maxHeight:280, overflowY:"auto" }}>
                {buildCLI(meta, scores)}
              </pre>
            </div>
          )}

          {/* Score table */}
          <Label>Score Summary</Label>
          <div style={{ background:C.card, borderRadius:7, border:`1px solid ${C.cardBorder}`, overflow:"hidden" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", ...mono, fontSize:11.5 }}>
              <thead>
                <tr style={{ borderBottom:`1px solid ${C.divider}` }}>
                  {["Section","Score","Max","%"].map(h=>(
                    <td key={h} style={{ padding:"7px 10px", color:C.grey2, fontSize:9.5 }}>{h}</td>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.sectionResults.map(sec=>(
                  <tr key={sec.key} style={{ borderBottom:`1px solid ${C.divider}` }}>
                    <td style={{ padding:"7px 10px", color:C.grey1 }}>{sec.icon} {sec.label}</td>
                    <td style={{ padding:"7px 10px", color:C.offWhite, textAlign:"center" }}>{sec.score}</td>
                    <td style={{ padding:"7px 10px", color:C.grey2, textAlign:"center" }}>{sec.max}</td>
                    <td style={{ padding:"7px 10px", color:strength(sec.pct).color, textAlign:"center" }}>{(sec.pct*100).toFixed(0)}%</td>
                  </tr>
                ))}
                <tr style={{ borderTop:`1px solid ${C.grey3}`, background:C.yellowDim }}>
                  <td style={{ padding:"8px 10px", color:C.white, fontWeight:700 }}>TOTAL</td>
                  <td style={{ padding:"8px 10px", color:C.yellow, textAlign:"center", fontWeight:700 }}>{results.total}</td>
                  <td style={{ padding:"8px 10px", color:C.grey2, textAlign:"center" }}>{results.maxTotal}</td>
                  <td style={{ padding:"8px 10px", color:C.yellow, textAlign:"center", fontWeight:700 }}>{(results.pct*100).toFixed(0)}%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div style={{ height:24 }} />
        </div>
      </div>
    </div>
  );
}
    st.stop()
