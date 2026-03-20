import { useState, useRef, useEffect, createContext, useContext } from "react";

// ─── Theme Definitions ────────────────────────────────────────────────────────
const DARK = {
  mode:"dark",
  bg:"#07111f", surface:"#0c1825", surfaceHi:"#111f30",
  border:"#152030", borderHi:"#1e3248",
  text:"#ddeaf7", muted:"#517898", dim:"#2a4361",
  accent:"#4b7dff", accentDim:"rgba(75,125,255,0.12)",
  green:"#1fd49e", greenDim:"rgba(31,212,158,0.10)",
  amber:"#f2a020", amberDim:"rgba(242,160,32,0.10)",
  red:"#ef5060",   redDim:"rgba(239,80,96,0.10)",
  purple:"#a78bfa",
  inputBg:"#060e1a", codeBg:"#060e1a",
  navBg:"rgba(7,17,31,0.92)",
  cardShadow:"0 8px 32px rgba(0,0,0,0.5)",
  scrollThumb:"#1e3248",
};
const LIGHT = {
  mode:"light",
  bg:"#f0f4f9", surface:"#ffffff", surfaceHi:"#f5f8fc",
  border:"#dde5ef", borderHi:"#c8d5e6",
  text:"#0e1d30", muted:"#5a7a99", dim:"#9aaec4",
  accent:"#2a5de8", accentDim:"rgba(42,93,232,0.09)",
  green:"#0fa878", greenDim:"rgba(15,168,120,0.09)",
  amber:"#c07800", amberDim:"rgba(192,120,0,0.09)",
  red:"#d63040",   redDim:"rgba(214,48,64,0.09)",
  purple:"#6d4fd4",
  inputBg:"#f0f4f9", codeBg:"#e8edf5",
  navBg:"rgba(240,244,249,0.94)",
  cardShadow:"0 4px 20px rgba(0,0,0,0.08)",
  scrollThumb:"#c8d5e6",
};

// ─── Theme Context ────────────────────────────────────────────────────────────
const ThemeCtx = createContext(DARK);
const useT = () => useContext(ThemeCtx);

// ─── Static Data ─────────────────────────────────────────────────────────────
const INSTALL_LABEL = { "claude-code":"Claude Code", mcp:"MCP Server", manual:"Manual" };
const INSTALL_COLOR = { "claude-code":"#4b7dff", mcp:"#1fd49e", manual:"#f2a020" };
const CATS  = ["All","Engineering","Product","Data","Security","Finance","General","HR","Research"];
const DIVS  = ["Engineering Org","Product Org","Finance & Legal","People & HR","Operations","Executive Office","Sales & Marketing","Customer Success"];
const SORTS = ["Trending","Most Installed","Highest Rated","Newest","Recently Updated"];
const DIV_COLOR = {
  "Engineering Org":"#4b7dff","Product Org":"#a78bfa","Finance & Legal":"#1fd49e",
  "People & HR":"#f2a020","Operations":"#22d3ee","Executive Office":"#ef5060",
  "Sales & Marketing":"#fb923c","Customer Success":"#84cc16",
};
const OAUTH_PROVIDERS = [
  { id:"microsoft", label:"Microsoft / Azure AD", icon:"🪟", color:"#0078d4", hint:"Most common for enterprise orgs" },
  { id:"google",    label:"Google Workspace",     icon:"🔵", color:"#4285f4", hint:"G Suite / Google Cloud identity" },
  { id:"okta",      label:"Okta",                 icon:"🔷", color:"#007dc1", hint:"Okta Universal Directory" },
  { id:"github",    label:"GitHub Enterprise",    icon:"⬛", color:"#555",    hint:"Org-level GitHub SSO" },
  { id:"oidc",      label:"Generic OIDC / SAML",  icon:"🔑", color:"#a78bfa", hint:"Any standards-compliant provider" },
];
const USERS = {
  "chase.oneill":{ name:"Chase O'Neill", initials:"CO", role:"Senior Engineer",  division:"Engineering Org",  email:"chase@acme.com" },
  "sarah.malik": { name:"Sarah Malik",   initials:"SM", role:"Product Manager",  division:"Product Org",      email:"sarah@acme.com" },
  "dev.huang":   { name:"Dev Huang",     initials:"DH", role:"Data Engineer",    division:"Engineering Org",  email:"dev@acme.com"   },
  "nina.cross":  { name:"Nina Cross",    initials:"NC", role:"VP Finance",       division:"Finance & Legal",  email:"nina@acme.com"  },
  "tom.reyes":   { name:"Tom Reyes",     initials:"TR", role:"Head of People",   division:"People & HR",      email:"tom@acme.com"   },
};
const SKILLS = [
  { id:1, slug:"pr-review-assistant", name:"PR Review Assistant",
    shortDesc:"Surgical code reviews with security, perf & style analysis",
    category:"Engineering", divisions:["Engineering Org"], accent:"#4b7dff",
    author:"Platform Team", authorType:"official", version:"2.3.1",
    rating:4.9, ratingCount:218, installs:1842, forks:34, favorites:156,
    tags:["code-review","git","security","typescript"], verified:true, featured:true, daysAgo:2, installMethod:"claude-code",
    triggers:["review this PR","review my changes","check this diff"],
    whenToUse:"Before merging any PR, especially for cross-team reviews or when the reviewer is unfamiliar with the codebase domain.",
    howToUse:"Paste the diff or describe the changes. Optionally specify a focus: security, performance, or style.",
    bestPrompts:["Review this PR with focus on security vulnerabilities","Check this diff for performance regressions and N+1 patterns","Review my changes aligned with SOLID principles"],
    notes:"Works best with TypeScript/JavaScript. Output for Rust/Go is still useful but less idiomatic." },
  { id:2, slug:"executive-summary-generator", name:"Executive Summary Generator",
    shortDesc:"Turn dense technical docs into crisp leadership narratives",
    category:"General", divisions:["Executive Office","Product Org","Engineering Org","Finance & Legal"], accent:"#a78bfa",
    author:"Comms Team", authorType:"official", version:"1.4.0",
    rating:4.7, ratingCount:304, installs:3210, forks:67, favorites:289,
    tags:["writing","leadership","summarization","reports"], verified:true, featured:true, daysAgo:5, installMethod:"manual",
    triggers:["summarize this for leadership","executive summary","write exec summary"],
    whenToUse:"When presenting technical findings to non-technical stakeholders or preparing materials for C-suite.",
    howToUse:"Paste your document. Specify the audience level (Director, VP, C-Suite).",
    bestPrompts:["Executive summary for CTO, focus on security risks and timeline","Summarize this incident report for VP-level — 3 bullets max"],
    notes:"Language and technical depth auto-calibrate based on audience level specified." },
  { id:3, slug:"hipaa-audit-analyzer", name:"HIPAA Audit Analyzer",
    shortDesc:"Scan audit logs for PHI exposure and HIPAA violations",
    category:"Security", divisions:["Engineering Org","Finance & Legal","Operations"], accent:"#ef5060",
    author:"Security Team", authorType:"official", version:"3.0.0",
    rating:4.8, ratingCount:89, installs:412, forks:8, favorites:71,
    tags:["hipaa","compliance","security","audit","phi"], verified:true, featured:false, daysAgo:1, installMethod:"mcp",
    triggers:["analyze this audit log","check hipaa compliance","review access logs"],
    whenToUse:"During quarterly compliance reviews, incident investigations, or after infrastructure changes.",
    howToUse:"Paste sanitized audit log data. Skill flags anomalies by HIPAA rule section with risk severity scores.",
    bestPrompts:["Analyze these access logs for HIPAA violations, rank by severity","Generate an OCR-ready audit report from this log export"],
    notes:"Never paste raw PHI. Sanitize all patient identifiers." },
  { id:4, slug:"sprint-planning-coach", name:"Sprint Planning Coach",
    shortDesc:"Velocity-aware sprint planning with dependency & risk mapping",
    category:"Product", divisions:["Product Org","Engineering Org"], accent:"#f2a020",
    author:"eng-productivity", authorType:"community", version:"1.1.2",
    rating:4.5, ratingCount:143, installs:987, forks:28, favorites:112,
    tags:["agile","sprint","planning","jira","product"], verified:false, featured:false, daysAgo:12, installMethod:"claude-code",
    triggers:["plan this sprint","help me plan sprint","sprint planning"],
    whenToUse:"Before sprint kickoff. Most effective when Jira backlog data is exported alongside team velocity history.",
    howToUse:"Paste your backlog items with story points and team velocity.",
    bestPrompts:["Plan our 2-week sprint with these backlog items — team at 80% capacity"],
    notes:"Works best with structured CSV/JSON backlog exports." },
  { id:5, slug:"sql-query-optimizer", name:"SQL Query Optimizer",
    shortDesc:"Diagnose slow queries and rewrite for maximum performance",
    category:"Data", divisions:["Engineering Org","Operations"], accent:"#22d3ee",
    author:"data-guild", authorType:"community", version:"2.0.1",
    rating:4.6, ratingCount:178, installs:1560, forks:42, favorites:134,
    tags:["sql","postgres","performance","database","bigquery"], verified:true, featured:false, daysAgo:7, installMethod:"manual",
    triggers:["optimize this query","why is this query slow","rewrite this sql"],
    whenToUse:"When a query exceeds latency thresholds or when auditing data pipelines before production.",
    howToUse:"Paste the query and optionally the EXPLAIN output. Specify dialect.",
    bestPrompts:["Optimize this PostgreSQL query and explain why it's slow"],
    notes:"BigQuery mode includes cost optimization alongside performance." },
  { id:6, slug:"architecture-decision-record", name:"Architecture Decision Record",
    shortDesc:"Structured ADR creation with full tradeoff analysis",
    category:"Engineering", divisions:["Engineering Org"], accent:"#1fd49e",
    author:"Platform Team", authorType:"official", version:"1.2.0",
    rating:4.8, ratingCount:96, installs:743, forks:19, favorites:88,
    tags:["architecture","adr","documentation","decisions"], verified:true, featured:true, daysAgo:14, installMethod:"claude-code",
    triggers:["create an ADR","write architecture decision","document this decision"],
    whenToUse:"When making significant technical decisions that will be difficult or costly to reverse.",
    howToUse:"Describe the decision context and options considered. Skill guides through MADR format.",
    bestPrompts:["Create an ADR for our decision to use Kafka over SQS","Write an ADR for switching from REST to GraphQL with tradeoffs"],
    notes:"Outputs MADR format by default. Nygard or Y-Statements format available via prompt flag." },
  { id:7, slug:"financial-report-narrator", name:"Financial Report Narrator",
    shortDesc:"Translate P&L and budget data into plain-language narratives",
    category:"Finance", divisions:["Finance & Legal","Executive Office"], accent:"#84cc16",
    author:"finance-ops", authorType:"community", version:"1.3.0",
    rating:4.6, ratingCount:112, installs:678, forks:15, favorites:98,
    tags:["finance","reporting","narrative","p&l","budget"], verified:false, featured:false, daysAgo:9, installMethod:"manual",
    triggers:["narrate this financial report","explain this P&L","summarize financials"],
    whenToUse:"When presenting financial data to non-finance teams or preparing monthly business reviews.",
    howToUse:"Paste the financial data. Specify audience and key variances to highlight.",
    bestPrompts:["Narrate this Q3 P&L for a product team","Board-ready narrative from this monthly financial summary"],
    notes:"Remove sensitive compensation data before input." },
  { id:8, slug:"onboarding-guide-builder", name:"Onboarding Guide Builder",
    shortDesc:"Generate role-specific onboarding plans and first-week checklists",
    category:"HR", divisions:["People & HR","Operations"], accent:"#fb923c",
    author:"people-ops", authorType:"official", version:"1.0.3",
    rating:4.4, ratingCount:67, installs:534, forks:11, favorites:79,
    tags:["onboarding","hr","checklist","new-hire"], verified:true, featured:false, daysAgo:21, installMethod:"manual",
    triggers:["build onboarding plan","create new hire checklist","onboarding guide for"],
    whenToUse:"Before a new hire's first day. Provide role, team, and tech stack for a tailored plan.",
    howToUse:"Specify the role, team, reporting manager, and key tools.",
    bestPrompts:["Onboarding plan for a senior backend engineer joining platform team"],
    notes:"Best when combined with the org's existing documentation links." },
];
const MOCK_REVIEWS = [
  { id:1, skillId:1, user:"sarah.malik",  rating:5, time:"2 days ago",  text:"Saved our team hours on every PR. The security focus mode is especially useful.", helpful:14, unhelpful:0 },
  { id:2, skillId:1, user:"dev.huang",    rating:5, time:"1 week ago",  text:"Found a subtle race condition in our auth flow that three human reviewers missed.", helpful:9,  unhelpful:1 },
  { id:3, skillId:1, user:"chase.oneill", rating:4, time:"2 weeks ago", text:"Works great for TS. Slightly less useful for our Python services but still catches the critical stuff.", helpful:6, unhelpful:0 },
];
const MOCK_COMMENTS = [
  { id:1, skillId:1, user:"dev.huang",   time:"3 days ago", text:"Quick tip — prepend 'Focus on auth flows:' before pasting your diff for much more targeted output.", replies:[], helpful:8 },
  { id:2, skillId:1, user:"sarah.malik", time:"1 week ago", text:"Does this work with GitHub Actions output or just raw diffs?",
    replies:[{ id:3, user:"chase.oneill", time:"6 days ago", text:"Yes — paste the step output directly. Works cleanly." }], helpful:5 },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
function useDivMultiSelect(initial=[]) {
  const [selected, setSelected] = useState(initial);
  const toggle  = d => setSelected(s => s.includes(d)?s.filter(x=>x!==d):[...s,d]);
  const clear   = () => setSelected([]);
  const matches = skill => selected.length===0 || selected.some(d=>skill.divisions.includes(d));
  return { selected, toggle, clear, matches };
}

// ─── Theme Toggle Button ──────────────────────────────────────────────────────
function ThemeToggle({ isDark, onToggle }) {
  const C = useT();
  const [hov, setHov] = useState(false);
  return (
    <button
      onClick={onToggle}
      onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      style={{
        width:"38px", height:"22px", borderRadius:"11px", border:"none", cursor:"pointer",
        position:"relative", flexShrink:0, transition:"background 0.3s",
        background: isDark
          ? (hov?"#1e3248":"#152030")
          : (hov?"#bfd0e8":"#c8d5e6"),
        boxShadow:`inset 0 1px 3px rgba(0,0,0,${isDark?0.4:0.15})`,
      }}>
      {/* Track icons */}
      <span style={{ position:"absolute", left:"5px", top:"50%", transform:"translateY(-50%)",
        fontSize:"10px", opacity: isDark?0.4:0, transition:"opacity 0.3s" }}>🌙</span>
      <span style={{ position:"absolute", right:"5px", top:"50%", transform:"translateY(-50%)",
        fontSize:"10px", opacity: isDark?0:0.5, transition:"opacity 0.3s" }}>☀️</span>
      {/* Thumb */}
      <div style={{
        position:"absolute", top:"3px",
        left: isDark?"3px":"19px",
        width:"16px", height:"16px", borderRadius:"50%",
        background: isDark?"#4b7dff":"#ffffff",
        boxShadow:`0 1px 4px rgba(0,0,0,${isDark?0.5:0.25})`,
        transition:"left 0.25s cubic-bezier(.4,0,.2,1), background 0.3s",
        display:"flex", alignItems:"center", justifyContent:"center",
        fontSize:"9px",
      }}>
        {isDark ? "🌙" : "☀️"}
      </div>
    </button>
  );
}

// ─── Micro Components ────────────────────────────────────────────────────────
function Avatar({ username, size=28 }) {
  const u = USERS[username];
  if (!u) return null;
  const hue = username.split("").reduce((a,c)=>a+c.charCodeAt(0),0)%360;
  return (
    <div style={{ width:size, height:size, borderRadius:"50%", flexShrink:0,
      background:`hsl(${hue},45%,${useT().mode==="dark"?"30%":"65%"})`,
      border:`2px solid hsl(${hue},45%,${useT().mode==="dark"?"42%":"55%"})`,
      display:"flex", alignItems:"center", justifyContent:"center",
      fontSize:size<32?"10px":"13px", fontWeight:700,
      color:`hsl(${hue},60%,${useT().mode==="dark"?"85%":"15%"})` }}>
      {u.initials}
    </div>
  );
}

function UserChip({ username, showRole=false }) {
  const C = useT();
  const u = USERS[username];
  if (!u) return <span style={{ fontSize:"12px", color:C.muted }}>@{username}</span>;
  return (
    <div style={{ display:"flex", alignItems:"center", gap:"7px" }}>
      <Avatar username={username} size={24} />
      <div>
        <span style={{ fontSize:"13px", fontWeight:600, color:C.text }}>{u.name}</span>
        {showRole && <div style={{ fontSize:"10px", color:C.dim }}>{u.role} · {u.division}</div>}
      </div>
    </div>
  );
}

function Tag({ children }) {
  const C = useT();
  return <span style={{ fontSize:"10px", padding:"2px 7px", borderRadius:"4px",
    background:C.border, color:C.muted, fontFamily:"'JetBrains Mono',monospace" }}>#{children}</span>;
}

function Badge({ color, children }) {
  const C = useT();
  const col = color || C.accent;
  return <span style={{ fontSize:"10px", padding:"2px 9px", borderRadius:"99px",
    background:`${col}18`, color:col, border:`1px solid ${col}28`, fontWeight:500, whiteSpace:"nowrap" }}>{children}</span>;
}

function DivisionChip({ division, active=false, onClick, small=false }) {
  const color = DIV_COLOR[division] || "#888";
  return (
    <span onClick={onClick} style={{ fontSize:small?"9px":"10px", padding:small?"2px 6px":"3px 9px",
      borderRadius:"99px", fontWeight:600, fontFamily:"'JetBrains Mono',monospace",
      background:active?`${color}25`:`${color}14`, color,
      border:`1px solid ${active?color+"66":color+"22"}`,
      whiteSpace:"nowrap", cursor:onClick?"pointer":"default",
      transition:"all 0.12s", boxShadow:active?`0 0 0 2px ${color}22`:"none" }}>
      {division}
    </span>
  );
}

function Btn({ onClick, primary, small, danger, disabled, style:sx={}, children }) {
  const C = useT();
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}
      style={{ cursor:disabled?"not-allowed":"pointer", border:"none", outline:"none",
        fontFamily:"'Outfit',sans-serif", fontWeight:600, opacity:disabled?0.45:1,
        padding:small?"5px 12px":"9px 18px", fontSize:small?"12px":"13px", borderRadius:"8px",
        background: primary?(hov?"#1f4fd4":C.accent)
          : danger?(hov?`${C.red}28`:`${C.red}14`)
          : (hov?C.surfaceHi:C.surface),
        color: primary?"#fff": danger?C.red: C.muted,
        border: primary?"none": danger?`1px solid ${C.red}44`: `1px solid ${C.border}`,
        transition:"all 0.15s", ...sx }}>
      {children}
    </button>
  );
}

// ─── OAuth Modal ──────────────────────────────────────────────────────────────
function AuthModal({ onLogin, onClose }) {
  const C = useT();
  const [step, setStep]         = useState("provider");
  const [provider, setProvider] = useState(null);
  const [simulating, setSimulating] = useState(false);

  const handleProvider = p => {
    setProvider(p); setSimulating(true); setStep("callback");
    setTimeout(()=>{ setSimulating(false); setStep("demo"); }, 1600);
  };

  const overlayStyle = { position:"fixed", inset:0, background:"rgba(4,8,16,0.85)",
    backdropFilter:"blur(10px)", zIndex:999, display:"flex", alignItems:"center", justifyContent:"center" };
  const boxStyle = { background:C.surface, border:`1px solid ${C.borderHi}`, borderRadius:"18px",
    width:"420px", maxHeight:"90vh", overflow:"auto", boxShadow:C.cardShadow };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div onClick={e=>e.stopPropagation()} style={boxStyle}>
        <div style={{ height:"3px", background:`linear-gradient(90deg,${C.accent},${C.purple},${C.green})` }} />
        <div style={{ padding:"28px" }}>
          <div style={{ display:"flex", alignItems:"center", gap:"12px", marginBottom:"22px" }}>
            <div style={{ width:"40px", height:"40px", borderRadius:"10px", background:C.accent,
              display:"flex", alignItems:"center", justifyContent:"center", fontSize:"20px" }}>⚡</div>
            <div>
              <div style={{ fontWeight:700, fontSize:"17px", color:C.text }}>Sign in to SkillHub</div>
              <div style={{ fontSize:"12px", color:C.muted }}>Use your organization's identity provider</div>
            </div>
          </div>

          {step==="provider" && (
            <div>
              <div style={{ fontSize:"11px", color:C.dim, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.9px", marginBottom:"10px" }}>Choose your provider</div>
              {OAUTH_PROVIDERS.map(p=>(
                <button key={p.id} onClick={()=>handleProvider(p)}
                  style={{ display:"flex", alignItems:"center", gap:"12px", padding:"11px 14px", width:"100%",
                    background:C.bg, border:`1px solid ${C.border}`, borderRadius:"10px",
                    cursor:"pointer", textAlign:"left", fontFamily:"'Outfit',sans-serif", marginBottom:"8px",
                    transition:"all 0.12s" }}
                  onMouseEnter={e=>{ e.currentTarget.style.borderColor=p.color+"66"; e.currentTarget.style.background=`${p.color}09`; }}
                  onMouseLeave={e=>{ e.currentTarget.style.borderColor=C.border; e.currentTarget.style.background=C.bg; }}>
                  <span style={{ fontSize:"20px", width:"28px", textAlign:"center" }}>{p.icon}</span>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:"13px", fontWeight:600, color:C.text }}>{p.label}</div>
                    <div style={{ fontSize:"11px", color:C.dim }}>{p.hint}</div>
                  </div>
                  <span style={{ fontSize:"16px", color:C.dim }}>→</span>
                </button>
              ))}
              <div style={{ fontSize:"11px", color:C.dim, textAlign:"center", marginTop:"12px", lineHeight:"1.5" }}>
                SkillHub never stores your password · Session expires after 8h
              </div>
            </div>
          )}

          {step==="callback" && (
            <div style={{ textAlign:"center", padding:"20px 0" }}>
              <div style={{ fontSize:"32px", marginBottom:"16px" }}>{provider?.icon}</div>
              <div style={{ fontSize:"14px", fontWeight:600, color:C.text, marginBottom:"8px" }}>Redirecting to {provider?.label}…</div>
              <div style={{ fontSize:"12px", color:C.muted, marginBottom:"20px" }}>Complete sign-in in the popup window</div>
              <div style={{ display:"flex", justifyContent:"center", gap:"6px" }}>
                {[0,1,2].map(i=>(
                  <div key={i} style={{ width:"8px", height:"8px", borderRadius:"50%",
                    background:C.accent, animation:`pulse 1.2s ease-in-out ${i*0.3}s infinite` }} />
                ))}
              </div>
              <style>{`@keyframes pulse{0%,100%{opacity:.2}50%{opacity:1}}`}</style>
            </div>
          )}

          {step==="demo" && (
            <div>
              <div style={{ display:"flex", alignItems:"center", gap:"8px", padding:"10px 12px",
                background:C.greenDim, border:`1px solid ${C.green}30`, borderRadius:"8px", marginBottom:"16px" }}>
                <span style={{ color:C.green }}>✓</span>
                <span style={{ fontSize:"12px", color:C.green }}>OAuth handshake complete via {provider?.label}</span>
              </div>
              <div style={{ fontSize:"11px", color:C.dim, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.9px", marginBottom:"10px" }}>Select your identity (demo)</div>
              {Object.entries(USERS).map(([k,v])=>(
                <button key={k} onClick={()=>onLogin(k)}
                  style={{ display:"flex", alignItems:"center", gap:"12px", padding:"10px 12px", width:"100%",
                    background:C.bg, border:`1px solid ${C.border}`, borderRadius:"10px",
                    cursor:"pointer", textAlign:"left", fontFamily:"'Outfit',sans-serif", marginBottom:"6px",
                    transition:"all 0.12s" }}
                  onMouseEnter={e=>{ e.currentTarget.style.borderColor=C.accent+"55"; e.currentTarget.style.background=C.accentDim; }}
                  onMouseLeave={e=>{ e.currentTarget.style.borderColor=C.border; e.currentTarget.style.background=C.bg; }}>
                  <Avatar username={k} size={34} />
                  <div>
                    <div style={{ fontSize:"13px", fontWeight:600, color:C.text }}>{v.name}</div>
                    <div style={{ fontSize:"11px", color:C.dim }}>{v.role} · {v.division}</div>
                  </div>
                  <DivisionChip division={v.division} small />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Submit Skill Modal ───────────────────────────────────────────────────────
function SubmitModal({ authUser, onClose }) {
  const C = useT();
  const [step, setStep]         = useState(1);
  const [name, setName]         = useState("");
  const [shortDesc, setShortDesc] = useState("");
  const [category, setCategory] = useState("");
  const [selDivs, setSelDivs]   = useState([]);
  const [justification, setJustification] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors]     = useState({});

  const toggleDiv = d => setSelDivs(s=>s.includes(d)?s.filter(x=>x!==d):[...s,d]);

  const validate1 = () => {
    const e={};
    if(!name.trim())      e.name="Required";
    if(!shortDesc.trim()) e.shortDesc="Required";
    if(!category)         e.category="Required";
    setErrors(e); return Object.keys(e).length===0;
  };
  const validate2 = () => {
    const e={};
    if(selDivs.length===0)    e.divs="At least one division required.";
    if(!justification.trim()) e.justification="Justification required.";
    setErrors(e); return Object.keys(e).length===0;
  };

  const inp = (err) => ({
    width:"100%", background:C.inputBg, border:`1px solid ${err?C.red+"66":C.border}`,
    borderRadius:"8px", padding:"9px 12px", fontSize:"13px", color:C.text,
    outline:"none", fontFamily:"'Outfit',sans-serif", transition:"border 0.2s",
  });
  const errMsg = k => errors[k] && <div style={{ fontSize:"11px", color:C.red, marginTop:"4px" }}>⚠ {errors[k]}</div>;
  const STEP_LABELS = ["Basic Info","Division Scope","Review & Submit"];

  return (
    <div style={{ position:"fixed", inset:0, background:"rgba(4,8,16,0.85)", backdropFilter:"blur(10px)",
      zIndex:999, display:"flex", alignItems:"center", justifyContent:"center" }} onClick={onClose}>
      <div onClick={e=>e.stopPropagation()}
        style={{ background:C.surface, border:`1px solid ${C.borderHi}`, borderRadius:"18px",
          width:"520px", maxHeight:"90vh", overflow:"auto", boxShadow:C.cardShadow }}>
        <div style={{ height:"3px", background:`linear-gradient(90deg,${C.accent},${C.purple})` }} />
        <div style={{ padding:"28px" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
            <div>
              <div style={{ fontWeight:700, fontSize:"17px", color:C.text }}>Submit a Skill</div>
              <div style={{ fontSize:"12px", color:C.muted }}>As <span style={{ color:C.text }}>{USERS[authUser]?.name}</span></div>
            </div>
            <button onClick={onClose} style={{ background:"none", border:"none", color:C.muted, cursor:"pointer", fontSize:"20px" }}>✕</button>
          </div>

          {!submitted && (
            <div style={{ display:"flex", gap:"0", marginBottom:"24px" }}>
              {STEP_LABELS.map((l,i)=>{
                const n=i+1, done=step>n, active=step===n;
                return (
                  <div key={n} style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center" }}>
                    <div style={{ display:"flex", alignItems:"center", width:"100%" }}>
                      {i>0 && <div style={{ flex:1, height:"2px", background:done||active?C.accent:C.border, transition:"background 0.3s" }} />}
                      <div style={{ width:"26px", height:"26px", borderRadius:"50%", flexShrink:0,
                        background:done?C.green:active?C.accent:C.surface,
                        border:`2px solid ${done?C.green:active?C.accent:C.border}`,
                        display:"flex", alignItems:"center", justifyContent:"center",
                        fontSize:"11px", fontWeight:700, color:done||active?"#fff":C.dim, transition:"all 0.3s" }}>
                        {done?"✓":n}
                      </div>
                      {i<2 && <div style={{ flex:1, height:"2px", background:done?C.accent:C.border, transition:"background 0.3s" }} />}
                    </div>
                    <div style={{ fontSize:"10px", color:active?C.text:C.dim, marginTop:"5px", textAlign:"center", fontWeight:active?600:400 }}>{l}</div>
                  </div>
                );
              })}
            </div>
          )}

          {!submitted && step===1 && (
            <div>
              <div style={{ marginBottom:"14px" }}>
                <label style={{ fontSize:"11px", color:C.muted, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.8px", display:"block", marginBottom:"5px" }}>Skill Name *</label>
                <input value={name} onChange={e=>setName(e.target.value)} style={inp(errors.name)} placeholder="e.g. PR Review Assistant" />
                {errMsg("name")}
              </div>
              <div style={{ marginBottom:"14px" }}>
                <label style={{ fontSize:"11px", color:C.muted, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.8px", display:"block", marginBottom:"5px" }}>Short Description * <span style={{ color:C.dim, fontWeight:400 }}>(max 80 chars)</span></label>
                <input value={shortDesc} onChange={e=>setShortDesc(e.target.value.slice(0,80))} style={inp(errors.shortDesc)} placeholder="What does this skill do in one line?" />
                <div style={{ fontSize:"10px", color:shortDesc.length>70?C.amber:C.dim, textAlign:"right", marginTop:"3px" }}>{shortDesc.length}/80</div>
                {errMsg("shortDesc")}
              </div>
              <div style={{ marginBottom:"14px" }}>
                <label style={{ fontSize:"11px", color:C.muted, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.8px", display:"block", marginBottom:"8px" }}>Category *</label>
                <div style={{ display:"flex", flexWrap:"wrap", gap:"6px" }}>
                  {CATS.filter(c=>c!=="All").map(c=>(
                    <button key={c} onClick={()=>{setCategory(c);setErrors(e=>({...e,category:undefined}));}}
                      style={{ padding:"5px 12px", borderRadius:"6px", fontSize:"12px", cursor:"pointer",
                        fontFamily:"'Outfit',sans-serif", transition:"all 0.1s",
                        border:`1px solid ${category===c?C.accent:C.border}`,
                        background:category===c?C.accentDim:"transparent",
                        color:category===c?C.accent:C.muted }}>
                      {c}
                    </button>
                  ))}
                </div>
                {errMsg("category")}
              </div>
              <div style={{ display:"flex", justifyContent:"flex-end" }}>
                <Btn primary onClick={()=>{if(validate1())setStep(2);}}>Next: Division Scope →</Btn>
              </div>
            </div>
          )}

          {!submitted && step===2 && (
            <div>
              <div style={{ padding:"12px 14px", background:C.amberDim, border:`1px solid ${C.amber}30`,
                borderRadius:"8px", marginBottom:"18px", fontSize:"12px", color:C.amber, lineHeight:"1.6" }}>
                <strong>⚠ Required:</strong> Declare which divisions are authorized to install this skill. Undeclared divisions will be blocked at install time.
              </div>
              <div style={{ marginBottom:"16px" }}>
                <label style={{ fontSize:"11px", color:C.muted, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.8px", display:"block", marginBottom:"10px" }}>
                  Target Divisions * <span style={{ color:C.dim, fontWeight:400 }}>({selDivs.length} selected)</span>
                </label>
                <div style={{ display:"flex", flexDirection:"column", gap:"6px" }}>
                  {DIVS.map(d=>{
                    const active=selDivs.includes(d); const color=DIV_COLOR[d]||C.accent;
                    return (
                      <button key={d} onClick={()=>{toggleDiv(d);setErrors(e=>({...e,divs:undefined}));}}
                        style={{ display:"flex", alignItems:"center", gap:"10px", padding:"9px 13px",
                          background:active?`${color}10`:C.bg, border:`1px solid ${active?color+"44":C.border}`,
                          borderRadius:"8px", cursor:"pointer", textAlign:"left", fontFamily:"'Outfit',sans-serif", transition:"all 0.12s" }}>
                        <div style={{ width:"17px", height:"17px", borderRadius:"4px", flexShrink:0,
                          border:`2px solid ${active?color:C.border}`, background:active?color:"transparent",
                          display:"flex", alignItems:"center", justifyContent:"center",
                          fontSize:"10px", color:"#fff", transition:"all 0.12s" }}>{active?"✓":""}</div>
                        <span style={{ fontSize:"13px", fontWeight:active?600:400, color:active?color:C.muted }}>{d}</span>
                      </button>
                    );
                  })}
                </div>
                {errMsg("divs")}
              </div>
              <div style={{ marginBottom:"16px" }}>
                <label style={{ fontSize:"11px", color:C.muted, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.8px", display:"block", marginBottom:"5px" }}>Division Justification *</label>
                <textarea value={justification} onChange={e=>setJustification(e.target.value)} rows={3}
                  placeholder="Explain why the selected divisions need this skill…"
                  style={{ width:"100%", background:C.inputBg, border:`1px solid ${errors.justification?C.red+"66":C.border}`,
                    borderRadius:"8px", padding:"9px 12px", fontSize:"13px", color:C.text, outline:"none",
                    resize:"vertical", fontFamily:"'Outfit',sans-serif", lineHeight:"1.6" }} />
                {errMsg("justification")}
              </div>
              <div style={{ display:"flex", justifyContent:"space-between" }}>
                <Btn onClick={()=>setStep(1)}>← Back</Btn>
                <Btn primary onClick={()=>{if(validate2())setStep(3);}}>Next: Review →</Btn>
              </div>
            </div>
          )}

          {!submitted && step===3 && (
            <div>
              <div style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:"10px", padding:"16px", marginBottom:"16px" }}>
                <div style={{ fontSize:"11px", color:C.dim, textTransform:"uppercase", letterSpacing:"0.8px", fontWeight:600, marginBottom:"12px" }}>Summary</div>
                {[["Name",name],["Category",category],["Short Desc",shortDesc]].map(([k,v])=>(
                  <div key={k} style={{ display:"flex", gap:"10px", marginBottom:"8px" }}>
                    <span style={{ fontSize:"12px", color:C.dim, width:"90px", flexShrink:0 }}>{k}</span>
                    <span style={{ fontSize:"12px", color:C.text }}>{v}</span>
                  </div>
                ))}
                <div style={{ display:"flex", gap:"10px", marginBottom:"8px" }}>
                  <span style={{ fontSize:"12px", color:C.dim, width:"90px", flexShrink:0 }}>Divisions</span>
                  <div style={{ display:"flex", flexWrap:"wrap", gap:"4px" }}>{selDivs.map(d=><DivisionChip key={d} division={d} small />)}</div>
                </div>
                <div style={{ display:"flex", gap:"10px", marginBottom:"8px" }}>
                  <span style={{ fontSize:"12px", color:C.dim, width:"90px", flexShrink:0 }}>Justification</span>
                  <span style={{ fontSize:"12px", color:C.muted, lineHeight:"1.5" }}>{justification}</span>
                </div>
              </div>
              <div style={{ padding:"10px 14px", background:C.accentDim, border:`1px solid ${C.accent}22`,
                borderRadius:"8px", marginBottom:"16px", fontSize:"12px", color:C.accent, lineHeight:"1.6" }}>
                Enters review queue. Gate 1 runs immediately. Gates 2 & 3 follow. Expect 3–5 business days.
              </div>
              <div style={{ display:"flex", justifyContent:"space-between" }}>
                <Btn onClick={()=>setStep(2)}>← Back</Btn>
                <Btn primary onClick={()=>setSubmitted(true)}>Submit for Review →</Btn>
              </div>
            </div>
          )}

          {submitted && (
            <div style={{ textAlign:"center", padding:"10px 0 20px" }}>
              <div style={{ fontSize:"48px", marginBottom:"12px" }}>🎉</div>
              <div style={{ fontSize:"18px", fontWeight:700, color:C.text, marginBottom:"8px" }}>Skill submitted!</div>
              <div style={{ fontSize:"13px", color:C.muted, maxWidth:"320px", margin:"0 auto 20px", lineHeight:"1.65" }}>
                <strong style={{ color:C.text }}>{name}</strong> is now in the review queue. Gate 1 validation is running.
              </div>
              <div style={{ display:"inline-block", padding:"8px 16px", background:C.bg,
                border:`1px solid ${C.border}`, borderRadius:"8px", marginBottom:"20px" }}>
                <div style={{ fontSize:"10px", color:C.dim }}>Submission ID</div>
                <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:"13px", color:C.accent }}>
                  #SKL-{Math.random().toString(36).slice(2,8).toUpperCase()}
                </div>
              </div>
              <br/>
              <Btn primary onClick={onClose}>Done</Btn>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── User Menu ────────────────────────────────────────────────────────────────
function UserMenu({ user, onLogout }) {
  const C = useT();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const u = USERS[user];
  useEffect(()=>{
    const h=e=>{if(ref.current&&!ref.current.contains(e.target))setOpen(false);};
    document.addEventListener("mousedown",h);
    return()=>document.removeEventListener("mousedown",h);
  },[]);
  return (
    <div ref={ref} style={{ position:"relative" }}>
      <div onClick={()=>setOpen(!open)}
        style={{ display:"flex", alignItems:"center", gap:"8px", cursor:"pointer",
          padding:"4px 10px 4px 4px", borderRadius:"99px",
          border:`1px solid ${open?C.borderHi:C.border}`,
          background:open?C.surfaceHi:C.surface, transition:"all 0.15s" }}>
        <Avatar username={user} size={28} />
        <div style={{ lineHeight:1.2 }}>
          <div style={{ fontSize:"12px", fontWeight:600, color:C.text }}>{u.name.split(" ")[0]}</div>
          <div style={{ fontSize:"9px", color:C.dim, fontFamily:"'JetBrains Mono',monospace" }}>{u.division}</div>
        </div>
        <span style={{ fontSize:"10px", color:C.dim }}>{open?"▲":"▼"}</span>
      </div>
      {open && (
        <div style={{ position:"absolute", right:0, top:"calc(100% + 8px)", width:"220px", zIndex:200,
          background:C.surface, border:`1px solid ${C.borderHi}`, borderRadius:"12px",
          boxShadow:C.cardShadow, overflow:"hidden" }}>
          <div style={{ padding:"14px 16px", borderBottom:`1px solid ${C.border}` }}>
            <UserChip username={user} showRole />
            <div style={{ fontSize:"11px", color:C.dim, marginTop:"4px", fontFamily:"'JetBrains Mono',monospace" }}>{u.email}</div>
          </div>
          {[["📦","My Installed Skills"],["★","My Favorites"],["↗","My Forks"],["📝","My Submissions"]].map(([icon,label])=>(
            <button key={label} onClick={()=>setOpen(false)}
              style={{ display:"flex", gap:"10px", width:"100%", padding:"10px 16px",
                background:"none", border:"none", cursor:"pointer", fontFamily:"'Outfit',sans-serif",
                fontSize:"13px", color:C.muted, textAlign:"left" }}
              onMouseEnter={e=>e.currentTarget.style.background=C.surfaceHi}
              onMouseLeave={e=>e.currentTarget.style.background="none"}>
              {icon} {label}
            </button>
          ))}
          <div style={{ borderTop:`1px solid ${C.border}`, padding:"6px 0" }}>
            <button onClick={()=>{setOpen(false);onLogout();}}
              style={{ display:"flex", gap:"10px", width:"100%", padding:"10px 16px",
                background:"none", border:"none", cursor:"pointer", fontFamily:"'Outfit',sans-serif",
                fontSize:"13px", color:C.red, textAlign:"left" }}
              onMouseEnter={e=>e.currentTarget.style.background=C.redDim}
              onMouseLeave={e=>e.currentTarget.style.background="none"}>
              ⎋ Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Nav ──────────────────────────────────────────────────────────────────────
function Nav({ view, setView, searchQuery, setSearchQuery, onSearch, authUser, onAuthOpen, onLogout, onSubmitOpen, isDark, onThemeToggle }) {
  const C = useT();
  const [focused, setFocused] = useState(false);
  const navItem = (label,v) => (
    <button key={v} onClick={()=>setView(v)}
      style={{ background:view===v?C.border:"transparent", border:"none", cursor:"pointer",
        fontFamily:"'Outfit',sans-serif", fontSize:"13px", fontWeight:view===v?600:400,
        color:view===v?C.text:C.muted, padding:"4px 10px", borderRadius:"6px", transition:"all 0.15s" }}>
      {label}
    </button>
  );
  return (
    <div style={{ position:"fixed", top:0, left:0, right:0, height:"60px",
      background:C.navBg, backdropFilter:"blur(14px)",
      borderBottom:`1px solid ${C.border}`, zIndex:100,
      display:"flex", alignItems:"center", padding:"0 24px", gap:"14px" }}>
      <div style={{ display:"flex", alignItems:"center", gap:"8px", marginRight:"6px" }}>
        <div style={{ width:"28px",height:"28px",borderRadius:"6px",background:C.accent,
          display:"flex",alignItems:"center",justifyContent:"center",fontSize:"14px" }}>⚡</div>
        <span style={{ fontWeight:700, fontSize:"15px", color:C.text }}>SkillHub</span>
        <span style={{ fontSize:"10px", padding:"1px 6px", borderRadius:"4px", background:C.accentDim,
          color:C.accent, fontFamily:"'JetBrains Mono',monospace" }}>INTERNAL</span>
      </div>
      <div style={{ display:"flex", gap:"2px" }}>
        {navItem("Discover","home")}
        {navItem("Browse","browse")}
        {navItem("Filtered","filtered")}
      </div>
      <div style={{ flex:1, maxWidth:"380px", marginLeft:"auto", marginRight:"auto", position:"relative" }}>
        <input value={searchQuery} onChange={e=>setSearchQuery(e.target.value)}
          onKeyDown={e=>e.key==="Enter"&&onSearch()} onFocus={()=>setFocused(true)} onBlur={()=>setFocused(false)}
          placeholder="⌕  Search skills with AI..."
          style={{ width:"100%", background:focused?C.surfaceHi:C.surface,
            border:`1px solid ${focused?C.accent+"66":C.border}`, borderRadius:"8px",
            padding:"8px 14px", fontSize:"13px", color:C.text, outline:"none",
            fontFamily:"'Outfit',sans-serif", transition:"all 0.15s",
            boxShadow:focused?`0 0 0 3px ${C.accentDim}`:"none" }} />
      </div>
      <div style={{ display:"flex", gap:"10px", marginLeft:"auto", alignItems:"center" }}>
        {/* Theme toggle */}
        <ThemeToggle isDark={isDark} onToggle={onThemeToggle} />
        {authUser
          ? <><Btn small onClick={onSubmitOpen}>+ Submit</Btn><UserMenu user={authUser} onLogout={onLogout} /></>
          : <Btn primary small onClick={onAuthOpen}>Sign In</Btn>}
      </div>
    </div>
  );
}

// ─── Skill Card ───────────────────────────────────────────────────────────────
function SkillCard({ skill, onSelect }) {
  const C = useT();
  const [hov, setHov] = useState(false);
  return (
    <div onClick={()=>onSelect(skill)} onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}
      style={{ background:hov?C.surfaceHi:C.surface, border:`1px solid ${hov?C.borderHi:C.border}`,
        borderRadius:"12px", overflow:"hidden", cursor:"pointer", transition:"all 0.18s",
        transform:hov?"translateY(-2px)":"none",
        boxShadow:hov?`${C.cardShadow},0 0 0 1px ${skill.accent}22`:C.mode==="light"?`0 1px 4px rgba(0,0,0,0.07)`:"none" }}>
      <div style={{ height:"3px", background:`linear-gradient(90deg,${skill.accent},${skill.accent}44)` }} />
      <div style={{ padding:"16px" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"10px" }}>
          <div style={{ display:"flex", alignItems:"center", gap:"10px" }}>
            <div style={{ width:"38px", height:"38px", borderRadius:"8px", background:`${skill.accent}18`,
              border:`1px solid ${skill.accent}30`, display:"flex", alignItems:"center", justifyContent:"center",
              fontSize:"17px", fontWeight:800, color:skill.accent, fontFamily:"'JetBrains Mono',monospace", flexShrink:0 }}>
              {skill.name[0]}
            </div>
            <div>
              <div style={{ display:"flex", alignItems:"center", gap:"5px" }}>
                <span style={{ fontWeight:600, fontSize:"14px", color:C.text }}>{skill.name}</span>
                {skill.verified&&<span style={{ color:C.amber, fontSize:"11px" }}>✓</span>}
              </div>
              <span style={{ fontSize:"10px", color:C.dim, fontFamily:"'JetBrains Mono',monospace" }}>v{skill.version}</span>
            </div>
          </div>
          <Badge color={skill.authorType==="official"?C.accent:C.green}>{skill.authorType}</Badge>
        </div>
        <p style={{ fontSize:"12px", color:C.muted, lineHeight:"1.55", margin:"0 0 8px", minHeight:"36px" }}>{skill.shortDesc}</p>
        <div style={{ display:"flex", flexWrap:"wrap", gap:"4px", marginBottom:"8px" }}>
          {skill.divisions.slice(0,2).map(d=><DivisionChip key={d} division={d} small />)}
          {skill.divisions.length>2&&<span style={{ fontSize:"9px", color:C.dim, fontFamily:"'JetBrains Mono',monospace", padding:"2px 6px" }}>+{skill.divisions.length-2}</span>}
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:"4px", marginBottom:"12px" }}>
          {skill.tags.slice(0,3).map(t=><Tag key={t}>{t}</Tag>)}
        </div>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", paddingTop:"10px", borderTop:`1px solid ${C.border}` }}>
          <div style={{ display:"flex", gap:"12px" }}>
            <span style={{ fontSize:"11px", color:C.muted }}><span style={{ color:C.amber }}>★</span> {skill.rating} <span style={{ color:C.dim }}>({skill.ratingCount})</span></span>
            <span style={{ fontSize:"11px", color:C.muted }}>↓ {skill.installs.toLocaleString()}</span>
          </div>
          <span style={{ fontSize:"10px", padding:"2px 8px", borderRadius:"4px",
            background:`${INSTALL_COLOR[skill.installMethod]}18`, color:INSTALL_COLOR[skill.installMethod],
            fontFamily:"'JetBrains Mono',monospace" }}>
            {INSTALL_LABEL[skill.installMethod]}
          </span>
        </div>
      </div>
    </div>
  );
}

// ─── Division Filter Bar ──────────────────────────────────────────────────────
function DivisionFilterBar({ divState }) {
  const C = useT();
  const { selected, toggle, clear } = divState;
  return (
    <div style={{ display:"flex", alignItems:"center", gap:"6px", flexWrap:"wrap", padding:"10px 14px",
      background:C.surface, border:`1px solid ${C.border}`, borderRadius:"10px" }}>
      <span style={{ fontSize:"10px", color:C.dim, fontWeight:600, fontFamily:"'JetBrains Mono',monospace",
        textTransform:"uppercase", letterSpacing:"0.8px", flexShrink:0, marginRight:"4px" }}>Division</span>
      {DIVS.map(d=><DivisionChip key={d} division={d} active={selected.includes(d)} onClick={()=>toggle(d)} />)}
      {selected.length>0&&(
        <button onClick={clear} style={{ fontSize:"10px", color:C.dim, background:"none", border:"none",
          cursor:"pointer", fontFamily:"'Outfit',sans-serif", marginLeft:"4px", padding:"2px 6px", borderRadius:"4px" }}
          onMouseEnter={e=>e.currentTarget.style.color=C.red}
          onMouseLeave={e=>e.currentTarget.style.color=C.dim}>
          Clear all ✕
        </button>
      )}
    </div>
  );
}

// ─── Home View ────────────────────────────────────────────────────────────────
function HomeView({ onSelectSkill, setView, setSearchQuery, authUser }) {
  const C = useT();
  const [query, setQuery] = useState("");
  const handleSearch=()=>{ if(query.trim()){setSearchQuery(query);setView("search");} };
  const userDiv = authUser?USERS[authUser]?.division:null;
  const suggested = SKILLS.filter(s=>!userDiv||s.divisions.includes(userDiv)||s.category==="General").slice(0,4);

  return (
    <div style={{ maxWidth:"1100px", margin:"0 auto", padding:"40px 24px" }}>
      <div style={{ textAlign:"center", marginBottom:"48px" }}>
        <div style={{ display:"inline-flex", gap:"6px", padding:"4px 12px", borderRadius:"99px",
          background:C.accentDim, border:`1px solid ${C.accent}33`, fontSize:"11px", color:C.accent, marginBottom:"16px", fontWeight:500 }}>
          ⚡ Internal Skills Registry · v1.0
        </div>
        <h1 style={{ fontSize:"40px", fontWeight:800, margin:"0 0 12px", lineHeight:1.2 }}>
          <span style={{ color:C.text }}>Your organization's</span><br/>
          <span style={{ background:`linear-gradient(135deg,${C.accent},${C.purple})`,
            WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent",
            display:"inline-block" }}>shared intelligence</span>
        </h1>
        <p style={{ fontSize:"15px", color:C.muted, maxWidth:"480px", margin:"0 auto 28px", lineHeight:"1.6" }}>
          Discover, install, and share Claude skills across every team and role.
        </p>
        <div style={{ maxWidth:"560px", margin:"0 auto", position:"relative" }}>
          <input value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==="Enter"&&handleSearch()}
            placeholder="What do you need help with today?"
            style={{ width:"100%", padding:"14px 120px 14px 18px", borderRadius:"12px",
              background:C.surface, border:`1px solid ${C.borderHi}`, fontSize:"15px",
              color:C.text, outline:"none", fontFamily:"'Outfit',sans-serif",
              boxShadow:C.mode==="dark"?"0 4px 24px rgba(0,0,0,0.3)":"0 2px 12px rgba(0,0,0,0.08)" }} />
          <Btn primary onClick={handleSearch} style={{ position:"absolute", right:"6px", top:"50%", transform:"translateY(-50%)", padding:"7px 16px" }}>
            Search ↵
          </Btn>
        </div>
        <div style={{ display:"flex", gap:"8px", justifyContent:"center", marginTop:"16px", flexWrap:"wrap" }}>
          {CATS.filter(c=>c!=="All").map(cat=>(
            <button key={cat} onClick={()=>setView("filtered")}
              style={{ background:C.surface, border:`1px solid ${C.border}`, color:C.muted,
                padding:"5px 14px", borderRadius:"99px", fontSize:"12px", cursor:"pointer",
                fontFamily:"'Outfit',sans-serif", transition:"all 0.15s" }}
              onMouseEnter={e=>{ e.currentTarget.style.borderColor=C.accent+"55"; e.currentTarget.style.color=C.accent; }}
              onMouseLeave={e=>{ e.currentTarget.style.borderColor=C.border; e.currentTarget.style.color=C.muted; }}>
              {cat}
            </button>
          ))}
        </div>
      </div>

      {authUser&&suggested.length>0&&(
        <section style={{ marginBottom:"40px" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"14px" }}>
            <h2 style={{ fontSize:"16px", fontWeight:700, margin:0, color:C.text }}>✦ Suggested for You</h2>
            <span style={{ fontSize:"11px", color:C.dim, fontFamily:"'JetBrains Mono',monospace" }}>
              {USERS[authUser]?.division}
            </span>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))", gap:"14px" }}>
            {suggested.map(s=><SkillCard key={s.id} skill={s} onSelect={onSelectSkill} />)}
          </div>
        </section>
      )}

      <section>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"16px" }}>
          <h2 style={{ fontSize:"16px", fontWeight:700, margin:0, color:C.text }}>⭐ Featured Skills</h2>
          <button onClick={()=>setView("browse")} style={{ background:"none", border:"none", color:C.accent, cursor:"pointer", fontSize:"13px", fontFamily:"'Outfit',sans-serif" }}>View all →</button>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))", gap:"14px" }}>
          {SKILLS.filter(s=>s.featured).map(s=><SkillCard key={s.id} skill={s} onSelect={onSelectSkill} />)}
        </div>
      </section>
    </div>
  );
}

// ─── Browse View ──────────────────────────────────────────────────────────────
function BrowseView({ onSelectSkill, setView }) {
  const C = useT();
  const [activeCat, setActiveCat] = useState("All");
  const divState = useDivMultiSelect();
  const filtered = SKILLS.filter(s=>activeCat==="All"||s.category===activeCat).filter(s=>divState.matches(s));
  return (
    <div style={{ maxWidth:"1100px", margin:"0 auto", padding:"32px 24px" }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"18px" }}>
        <div>
          <h1 style={{ fontSize:"22px", fontWeight:700, margin:"0 0 4px", color:C.text }}>All Skills</h1>
          <span style={{ fontSize:"12px", color:C.muted }}>{filtered.length} skills</span>
        </div>
        <Btn onClick={()=>setView("filtered")}>⚙ Advanced Filters</Btn>
      </div>
      <div style={{ display:"flex", gap:"6px", marginBottom:"10px", flexWrap:"wrap" }}>
        {CATS.map(cat=>{const a=activeCat===cat; return (
          <button key={cat} onClick={()=>setActiveCat(cat)}
            style={{ padding:"5px 14px", borderRadius:"99px", fontSize:"12px", cursor:"pointer",
              fontFamily:"'Outfit',sans-serif", fontWeight:a?600:400, transition:"all 0.15s",
              border:`1px solid ${a?C.accent:C.border}`, background:a?C.accentDim:C.surface, color:a?C.accent:C.muted }}>
            {cat}
          </button>); })}
      </div>
      <div style={{ marginBottom:"20px" }}><DivisionFilterBar divState={divState} /></div>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))", gap:"14px" }}>
        {filtered.map(s=><SkillCard key={s.id} skill={s} onSelect={onSelectSkill} />)}
      </div>
    </div>
  );
}

// ─── Search View ──────────────────────────────────────────────────────────────
function SearchView({ query, setView, onSelectSkill }) {
  const C = useT();
  const divState = useDivMultiSelect();
  const base = query?SKILLS.filter(s=>
    s.name.toLowerCase().includes(query.toLowerCase())||
    s.shortDesc.toLowerCase().includes(query.toLowerCase())||
    s.tags.some(t=>t.includes(query.toLowerCase()))||
    s.divisions.some(d=>d.toLowerCase().includes(query.toLowerCase()))
  ):SKILLS;
  const results = base.filter(s=>divState.matches(s));
  return (
    <div style={{ maxWidth:"1100px", margin:"0 auto", padding:"32px 24px" }}>
      <div style={{ display:"flex", alignItems:"center", gap:"10px", marginBottom:"14px" }}>
        <button onClick={()=>setView("home")} style={{ background:"none", border:"none", color:C.muted, cursor:"pointer", fontSize:"20px" }}>←</button>
        <div>
          <h1 style={{ fontSize:"18px", fontWeight:700, margin:"0 0 2px", color:C.text }}>
            {query?<>Results for <span style={{ color:C.accent }}>"{query}"</span></>:"All Skills"}
          </h1>
          <span style={{ fontSize:"11px", color:C.muted }}>{results.length} skills · AI-semantic search active</span>
        </div>
      </div>
      {query&&<div style={{ padding:"10px 14px", background:C.accentDim, border:`1px solid ${C.accent}22`,
        borderRadius:"8px", marginBottom:"14px", fontSize:"12px", color:C.accent }}>
        ✦ Semantic search active
      </div>}
      <div style={{ marginBottom:"18px" }}><DivisionFilterBar divState={divState} /></div>
      {results.length===0?(
        <div style={{ textAlign:"center", padding:"60px 0", color:C.muted }}>
          <div style={{ fontSize:"32px", marginBottom:"12px" }}>🔍</div>
          <div style={{ fontSize:"16px", fontWeight:600, color:C.text }}>No skills found for "{query}"</div>
        </div>
      ):(
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))", gap:"14px" }}>
          {results.map(s=><SkillCard key={s.id} skill={s} onSelect={onSelectSkill} />)}
        </div>
      )}
    </div>
  );
}

// ─── Filtered View ────────────────────────────────────────────────────────────
function FilteredView({ onSelectSkill }) {
  const C = useT();
  const [cat, setCat]           = useState("All");
  const [sort, setSort]         = useState("Trending");
  const [verifiedOnly, setVer]  = useState(false);
  const [installFilter, setInst]= useState("All");
  const divState = useDivMultiSelect();

  const sortFn={
    "Trending":(a,b)=>b.installs-a.installs,"Most Installed":(a,b)=>b.installs-a.installs,
    "Highest Rated":(a,b)=>b.rating-a.rating,"Newest":(a,b)=>a.daysAgo-b.daysAgo,"Recently Updated":(a,b)=>a.daysAgo-b.daysAgo
  }[sort];

  const filtered=[...SKILLS]
    .filter(s=>cat==="All"||s.category===cat)
    .filter(s=>divState.matches(s))
    .filter(s=>!verifiedOnly||s.verified)
    .filter(s=>installFilter==="All"||s.installMethod===installFilter)
    .sort(sortFn);

  const pill=(label,active,onClick,color=C.accent)=>(
    <button onClick={onClick} style={{ padding:"5px 12px", borderRadius:"6px", fontSize:"12px", cursor:"pointer",
      fontFamily:"'Outfit',sans-serif", transition:"all 0.1s",
      border:`1px solid ${active?color:C.border}`, background:active?`${color}14`:"transparent", color:active?color:C.muted }}>
      {label}
    </button>
  );
  const section=(title,content)=>(
    <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:"12px", padding:"16px", marginBottom:"10px" }}>
      <h3 style={{ fontSize:"11px", fontWeight:600, color:C.dim, textTransform:"uppercase", letterSpacing:"1px", margin:"0 0 10px" }}>{title}</h3>
      {content}
    </div>
  );

  return (
    <div style={{ maxWidth:"1200px", margin:"0 auto", padding:"32px 24px", display:"flex", gap:"24px" }}>
      <div style={{ width:"230px", flexShrink:0 }}>
        <div style={{ position:"sticky", top:"80px" }}>
          {section("Category",<div style={{ display:"flex", flexDirection:"column", gap:"3px" }}>{CATS.map(c=>pill(c,cat===c,()=>setCat(c)))}</div>)}
          {/* Multi-select division */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:"12px", padding:"16px", marginBottom:"10px" }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"10px" }}>
              <h3 style={{ fontSize:"11px", fontWeight:600, color:C.dim, textTransform:"uppercase", letterSpacing:"1px", margin:0 }}>
                Division {divState.selected.length>0&&<span style={{ background:C.accentDim, color:C.accent, borderRadius:"99px", padding:"1px 7px", fontSize:"10px" }}>{divState.selected.length}</span>}
              </h3>
              {divState.selected.length>0&&(
                <button onClick={divState.clear} style={{ fontSize:"10px", color:C.dim, background:"none", border:"none", cursor:"pointer", fontFamily:"'Outfit',sans-serif" }}
                  onMouseEnter={e=>e.currentTarget.style.color=C.red} onMouseLeave={e=>e.currentTarget.style.color=C.dim}>
                  Clear ✕
                </button>
              )}
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:"4px" }}>
              {DIVS.map(d=>{
                const active=divState.selected.includes(d); const color=DIV_COLOR[d]||C.accent;
                return (
                  <button key={d} onClick={()=>divState.toggle(d)}
                    style={{ display:"flex", alignItems:"center", gap:"8px", padding:"5px 8px", borderRadius:"6px",
                      cursor:"pointer", textAlign:"left", fontFamily:"'Outfit',sans-serif", transition:"all 0.1s",
                      background:active?`${color}10`:"transparent", border:`1px solid ${active?color+"33":"transparent"}` }}>
                    <div style={{ width:"14px", height:"14px", borderRadius:"3px", flexShrink:0, transition:"all 0.12s",
                      border:`2px solid ${active?color:C.border}`, background:active?color:"transparent",
                      display:"flex", alignItems:"center", justifyContent:"center", fontSize:"9px", color:"#fff" }}>{active?"✓":""}</div>
                    <span style={{ fontSize:"12px", color:active?color:C.muted, fontWeight:active?600:400 }}>{d}</span>
                  </button>
                );
              })}
            </div>
          </div>
          {section("Sort By",<div style={{ display:"flex", flexDirection:"column", gap:"3px" }}>{SORTS.map(s=>pill(s,sort===s,()=>setSort(s)))}</div>)}
          {section("Install Method",<div style={{ display:"flex", flexDirection:"column", gap:"3px" }}>{["All","claude-code","mcp","manual"].map(m=>pill(m==="All"?"All":INSTALL_LABEL[m],installFilter===m,()=>setInst(m),INSTALL_COLOR[m]||C.accent))}</div>)}
          {section("Quality",
            <label style={{ display:"flex", alignItems:"center", gap:"8px", cursor:"pointer" }}>
              <input type="checkbox" checked={verifiedOnly} onChange={e=>setVer(e.target.checked)} style={{ accentColor:C.accent }} />
              <span style={{ fontSize:"12px", color:C.muted }}>Verified only</span>
            </label>
          )}
        </div>
      </div>
      <div style={{ flex:1 }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"14px" }}>
          <span style={{ fontSize:"13px", color:C.muted }}><span style={{ fontWeight:600, color:C.text }}>{filtered.length}</span> skills</span>
          <div style={{ display:"flex", gap:"6px", flexWrap:"wrap" }}>
            {cat!=="All"&&<span style={{ fontSize:"11px", padding:"3px 10px", borderRadius:"99px", background:C.accentDim, color:C.accent, border:`1px solid ${C.accent}30` }}>{cat} ✕</span>}
            {divState.selected.map(d=><span key={d} style={{ fontSize:"11px", padding:"3px 10px", borderRadius:"99px", background:`${DIV_COLOR[d]}14`, color:DIV_COLOR[d], border:`1px solid ${DIV_COLOR[d]}30` }}>{d} ✕</span>)}
            {verifiedOnly&&<span style={{ fontSize:"11px", padding:"3px 10px", borderRadius:"99px", background:C.amberDim, color:C.amber, border:`1px solid ${C.amber}30` }}>Verified ✕</span>}
          </div>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(240px,1fr))", gap:"14px" }}>
          {filtered.map(s=><SkillCard key={s.id} skill={s} onSelect={onSelectSkill} />)}
        </div>
      </div>
    </div>
  );
}

// ─── Reviews & Discussion ─────────────────────────────────────────────────────
function ReviewsTab({ skill, authUser, onAuthOpen }) {
  const C = useT();
  const [reviews, setReviews]   = useState(MOCK_REVIEWS.filter(r=>r.skillId===skill.id));
  const [comments, setComments] = useState(MOCK_COMMENTS.filter(c=>c.skillId===skill.id));
  const [activeTab, setActiveTab]   = useState("reviews");
  const [newRating, setNewRating]   = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [newReviewText, setNewReviewText] = useState("");
  const [newCommentText, setNewCommentText] = useState("");
  const [replyTarget, setReplyTarget] = useState(null);
  const [replyText, setReplyText]   = useState("");
  const [showReviewForm, setShowReviewForm] = useState(false);

  const submitReview=()=>{ if(!newRating||!newReviewText.trim())return; setReviews(r=>[{id:Date.now(),skillId:skill.id,user:authUser,rating:newRating,time:"just now",text:newReviewText,helpful:0,unhelpful:0},...r]); setNewRating(0);setNewReviewText("");setShowReviewForm(false); };
  const submitComment=()=>{ if(!newCommentText.trim())return; setComments(c=>[...c,{id:Date.now(),skillId:skill.id,user:authUser,time:"just now",text:newCommentText,replies:[],helpful:0}]); setNewCommentText(""); };
  const submitReply=id=>{ if(!replyText.trim())return; setComments(cs=>cs.map(c=>c.id===id?{...c,replies:[...c.replies,{id:Date.now(),user:authUser,time:"just now",text:replyText}]}:c)); setReplyText("");setReplyTarget(null); };

  const avgRating=reviews.length?(reviews.reduce((a,r)=>a+r.rating,0)/reviews.length).toFixed(1):0;
  const subTab=(label,val)=>(
    <button key={val} onClick={()=>setActiveTab(val)}
      style={{ padding:"7px 18px", fontSize:"13px", fontWeight:activeTab===val?600:400, cursor:"pointer",
        fontFamily:"'Outfit',sans-serif", border:"none", background:"none",
        color:activeTab===val?C.text:C.muted, borderBottom:`2px solid ${activeTab===val?C.accent:"transparent"}`, transition:"all 0.15s" }}>
      {label}
    </button>
  );
  const ta=(val,setVal,ph,rows=3)=>(
    <textarea value={val} onChange={e=>setVal(e.target.value)} placeholder={ph} rows={rows}
      style={{ width:"100%", background:C.inputBg, border:`1px solid ${C.border}`, borderRadius:"8px",
        padding:"10px 12px", fontSize:"13px", color:C.text, outline:"none",
        resize:"vertical", fontFamily:"'Outfit',sans-serif", lineHeight:"1.6" }} />
  );

  return (
    <div>
      <div style={{ display:"flex", borderBottom:`1px solid ${C.border}`, marginBottom:"20px" }}>
        {subTab(`Reviews (${reviews.length})`,"reviews")}
        {subTab(`Discussion (${comments.length})`,"discussion")}
      </div>

      {activeTab==="reviews"&&(
        <div>
          <div style={{ display:"flex", gap:"28px", alignItems:"center", marginBottom:"24px" }}>
            <div style={{ textAlign:"center" }}>
              <div style={{ fontSize:"48px", fontWeight:800, color:C.text, lineHeight:1 }}>{avgRating}</div>
              <div style={{ color:C.amber, fontSize:"16px", letterSpacing:"2px", margin:"6px 0" }}>{"★".repeat(Math.round(Number(avgRating)))}{"☆".repeat(5-Math.round(Number(avgRating)))}</div>
              <div style={{ fontSize:"12px", color:C.muted }}>{reviews.length} reviews</div>
            </div>
            <div style={{ flex:1 }}>
              {[5,4,3,2,1].map(n=>{
                const pct=Math.round((reviews.filter(r=>r.rating===n).length/Math.max(reviews.length,1))*100);
                return(<div key={n} style={{ display:"flex", alignItems:"center", gap:"8px", marginBottom:"5px" }}>
                  <span style={{ fontSize:"11px", color:C.muted, width:"12px" }}>{n}</span>
                  <div style={{ flex:1, height:"6px", borderRadius:"3px", background:C.border }}>
                    <div style={{ width:`${pct}%`, height:"100%", borderRadius:"3px", background:C.amber }} />
                  </div>
                  <span style={{ fontSize:"11px", color:C.dim, width:"28px" }}>{pct}%</span>
                </div>);
              })}
            </div>
            <div>{authUser?<Btn primary small onClick={()=>setShowReviewForm(!showReviewForm)}>{showReviewForm?"Cancel":"✎ Write Review"}</Btn>:<Btn small onClick={onAuthOpen}>Sign in to review</Btn>}</div>
          </div>
          {showReviewForm&&authUser&&(
            <div style={{ background:C.bg, border:`1px solid ${C.borderHi}`, borderRadius:"10px", padding:"16px", marginBottom:"20px" }}>
              <div style={{ display:"flex", gap:"10px", alignItems:"center", marginBottom:"12px" }}>
                <Avatar username={authUser} size={32} />
                <div>
                  <div style={{ fontSize:"13px", fontWeight:600, color:C.text }}>{USERS[authUser]?.name}</div>
                  <div style={{ fontSize:"10px", color:C.dim }}>{USERS[authUser]?.role}</div>
                </div>
              </div>
              <div style={{ display:"flex", gap:"4px", marginBottom:"12px" }}>
                {[1,2,3,4,5].map(n=>(
                  <span key={n} onClick={()=>setNewRating(n)} onMouseEnter={()=>setHoverRating(n)} onMouseLeave={()=>setHoverRating(0)}
                    style={{ fontSize:"24px", cursor:"pointer", color:(hoverRating||newRating)>=n?C.amber:C.border, transition:"color 0.1s" }}>★</span>
                ))}
                {(newRating||hoverRating)>0&&<span style={{ fontSize:"12px", color:C.muted, marginLeft:"6px", lineHeight:"28px" }}>{["","Poor","Fair","Good","Great","Excellent"][hoverRating||newRating]}</span>}
              </div>
              {ta(newReviewText,setNewReviewText,"Share your experience...")}
              <div style={{ display:"flex", gap:"8px", justifyContent:"flex-end", marginTop:"10px" }}>
                <Btn small onClick={()=>{setShowReviewForm(false);setNewRating(0);setNewReviewText("");}}>Cancel</Btn>
                <Btn primary small onClick={submitReview} style={{ opacity:newRating&&newReviewText.trim()?1:0.5 }}>Post Review</Btn>
              </div>
            </div>
          )}
          {reviews.map(r=>(
            <div key={r.id} style={{ padding:"16px", background:C.bg, borderRadius:"10px", border:`1px solid ${C.border}`, marginBottom:"10px" }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"10px" }}>
                <UserChip username={r.user} showRole />
                <div style={{ textAlign:"right" }}>
                  <div style={{ color:C.amber, fontSize:"13px" }}>{"★".repeat(r.rating)}{"☆".repeat(5-r.rating)}</div>
                  <div style={{ fontSize:"11px", color:C.dim }}>{r.time}</div>
                </div>
              </div>
              <p style={{ margin:"0 0 12px", fontSize:"13px", color:C.muted, lineHeight:"1.65" }}>{r.text}</p>
              <div style={{ display:"flex", gap:"10px", alignItems:"center" }}>
                <span style={{ fontSize:"11px", color:C.dim }}>Helpful?</span>
                <button onClick={()=>setReviews(rs=>rs.map(x=>x.id===r.id?{...x,helpful:x.helpful+1}:x))}
                  style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:"5px", padding:"2px 9px", fontSize:"11px", color:C.muted, cursor:"pointer", fontFamily:"'Outfit',sans-serif" }}>
                  👍 {r.helpful}
                </button>
                <button onClick={()=>setReviews(rs=>rs.map(x=>x.id===r.id?{...x,unhelpful:x.unhelpful+1}:x))}
                  style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:"5px", padding:"2px 9px", fontSize:"11px", color:C.muted, cursor:"pointer", fontFamily:"'Outfit',sans-serif" }}>
                  👎 {r.unhelpful}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab==="discussion"&&(
        <div>
          {authUser?(
            <div style={{ background:C.bg, border:`1px solid ${C.borderHi}`, borderRadius:"10px", padding:"14px", marginBottom:"20px" }}>
              <div style={{ display:"flex", gap:"10px", marginBottom:"10px" }}>
                <Avatar username={authUser} size={30} />
                <div style={{ flex:1 }}>{ta(newCommentText,setNewCommentText,"Ask a question or share a tip...",2)}</div>
              </div>
              <div style={{ display:"flex", justifyContent:"flex-end" }}>
                <Btn primary small onClick={submitComment} style={{ opacity:newCommentText.trim()?1:0.5 }}>Post Comment</Btn>
              </div>
            </div>
          ):(
            <div style={{ padding:"14px 16px", background:C.accentDim, border:`1px solid ${C.accent}22`,
              borderRadius:"10px", marginBottom:"20px", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <span style={{ fontSize:"13px", color:C.accent }}>Sign in to join the discussion</span>
              <Btn primary small onClick={onAuthOpen}>Sign In</Btn>
            </div>
          )}
          {comments.map(c=>(
            <div key={c.id} style={{ marginBottom:"16px" }}>
              <div style={{ padding:"14px 16px", background:C.bg, borderRadius:"10px 10px 0 0",
                border:`1px solid ${C.border}`, borderBottom:"none" }}>
                <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"8px" }}>
                  <UserChip username={c.user} showRole />
                  <span style={{ fontSize:"11px", color:C.dim }}>{c.time}</span>
                </div>
                <p style={{ margin:"0 0 10px", fontSize:"13px", color:C.muted, lineHeight:"1.65" }}>{c.text}</p>
                <div style={{ display:"flex", gap:"10px" }}>
                  <button onClick={()=>setComments(cs=>cs.map(x=>x.id===c.id?{...x,helpful:x.helpful+1}:x))}
                    style={{ background:"none", border:"none", cursor:"pointer", fontSize:"11px", color:C.dim, fontFamily:"'Outfit',sans-serif", padding:0 }}>
                    ↑ {c.helpful}
                  </button>
                  {authUser&&<button onClick={()=>setReplyTarget(replyTarget===c.id?null:c.id)}
                    style={{ background:"none", border:"none", cursor:"pointer", fontSize:"11px",
                      color:replyTarget===c.id?C.accent:C.dim, fontFamily:"'Outfit',sans-serif", padding:0 }}>
                    ↩ Reply
                  </button>}
                </div>
              </div>
              {c.replies.map(reply=>(
                <div key={reply.id} style={{ padding:"12px 16px 12px 32px", background:C.surfaceHi,
                  borderLeft:`3px solid ${C.accent}40`, border:`1px solid ${C.border}`, borderTop:"none" }}>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"6px" }}>
                    <UserChip username={reply.user} />
                    <span style={{ fontSize:"11px", color:C.dim }}>{reply.time}</span>
                  </div>
                  <p style={{ margin:0, fontSize:"13px", color:C.muted, lineHeight:"1.6" }}>{reply.text}</p>
                </div>
              ))}
              {replyTarget===c.id&&(
                <div style={{ padding:"12px 16px", background:C.surface,
                  borderLeft:`3px solid ${C.accent}60`, border:`1px solid ${C.borderHi}`, borderTop:"none", borderRadius:"0 0 10px 10px" }}>
                  <div style={{ display:"flex", gap:"8px" }}>
                    <Avatar username={authUser} size={26} />
                    <div style={{ flex:1 }}>
                      {ta(replyText,setReplyText,"Write a reply...",2)}
                      <div style={{ display:"flex", gap:"6px", justifyContent:"flex-end", marginTop:"8px" }}>
                        <Btn small onClick={()=>{setReplyTarget(null);setReplyText("");}}>Cancel</Btn>
                        <Btn primary small onClick={()=>submitReply(c.id)}>Reply</Btn>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              {replyTarget!==c.id&&c.replies.length===0&&<div style={{ height:"6px", background:C.bg, border:`1px solid ${C.border}`, borderTop:"none", borderRadius:"0 0 10px 10px" }} />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Skill Detail ─────────────────────────────────────────────────────────────
function SkillDetailView({ skill, setView, authUser, onAuthOpen }) {
  const C = useT();
  const [tab, setTab]       = useState("overview");
  const [installed, setInst] = useState(false);
  const [favorited, setFav]  = useState(false);
  const [reqAccess, setReqAccess] = useState(false);

  if(!skill) return null;
  const userDiv   = authUser?USERS[authUser]?.division:null;
  const hasAccess = !userDiv||skill.divisions.includes(userDiv);
  const tabs=["overview","how-to-use","install","reviews"];
  const tabLabels={overview:"Overview","how-to-use":"How to Use",install:"Install",reviews:"Reviews & Discussion"};
  const tabBtn=t=>(
    <button key={t} onClick={()=>setTab(t)}
      style={{ padding:"8px 18px", fontSize:"13px", fontWeight:tab===t?600:400, cursor:"pointer",
        fontFamily:"'Outfit',sans-serif", border:"none", background:"none",
        color:tab===t?C.text:C.muted, borderBottom:`2px solid ${tab===t?C.accent:"transparent"}`, transition:"all 0.15s", whiteSpace:"nowrap" }}>
      {tabLabels[t]}
    </button>
  );
  return (
    <div style={{ maxWidth:"900px", margin:"0 auto", padding:"32px 24px" }}>
      <button onClick={()=>setView("home")} style={{ background:"none", border:"none", color:C.muted,
        cursor:"pointer", fontSize:"13px", fontFamily:"'Outfit',sans-serif", marginBottom:"20px", display:"flex", alignItems:"center", gap:"6px" }}>
        ← Back to Marketplace
      </button>

      {authUser&&!hasAccess&&(
        <div style={{ padding:"16px 20px", background:C.amberDim, border:`1px solid ${C.amber}44`,
          borderRadius:"12px", marginBottom:"16px", display:"flex", justifyContent:"space-between", alignItems:"center", gap:"16px" }}>
          <div>
            <div style={{ fontSize:"14px", fontWeight:600, color:C.amber, marginBottom:"4px" }}>⚠ Access restricted for your division</div>
            <div style={{ fontSize:"12px", color:C.amber, opacity:0.8, lineHeight:"1.5" }}>
              Approved for: {skill.divisions.map(d=><strong key={d}> {d}</strong>)} · Your division: <strong>{userDiv}</strong>
            </div>
          </div>
          <Btn small onClick={()=>setReqAccess(!reqAccess)} style={{ whiteSpace:"nowrap", flexShrink:0 }}>
            {reqAccess?"✓ Requested":"Request Access"}
          </Btn>
        </div>
      )}

      <div style={{ background:C.surface, border:`1px solid ${C.borderHi}`, borderRadius:"14px", overflow:"hidden", marginBottom:"2px",
        boxShadow:C.mode==="light"?"0 2px 12px rgba(0,0,0,0.06)":"none" }}>
        <div style={{ height:"4px", background:`linear-gradient(90deg,${skill.accent},${skill.accent}44,transparent)` }} />
        <div style={{ padding:"24px 28px" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:"20px", marginBottom:"18px" }}>
            <div style={{ display:"flex", gap:"14px", alignItems:"flex-start" }}>
              <div style={{ width:"52px", height:"52px", borderRadius:"10px", background:`${skill.accent}18`,
                border:`1px solid ${skill.accent}30`, display:"flex", alignItems:"center", justifyContent:"center",
                fontSize:"24px", fontWeight:800, color:skill.accent, fontFamily:"'JetBrains Mono',monospace", flexShrink:0 }}>
                {skill.name[0]}
              </div>
              <div>
                <div style={{ display:"flex", alignItems:"center", gap:"8px", marginBottom:"4px" }}>
                  <h1 style={{ fontSize:"22px", fontWeight:700, margin:0, color:C.text }}>{skill.name}</h1>
                  {skill.verified&&<span style={{ fontSize:"11px", padding:"2px 7px", borderRadius:"4px", background:C.amberDim, color:C.amber, fontWeight:600 }}>✓ Verified</span>}
                  {skill.featured&&<span style={{ fontSize:"11px", padding:"2px 7px", borderRadius:"4px", background:C.accentDim, color:C.accent, fontWeight:600 }}>⭐ Featured</span>}
                </div>
                <div style={{ display:"flex", alignItems:"center", gap:"10px", fontSize:"12px", color:C.muted, flexWrap:"wrap" }}>
                  <span>by <span style={{ color:C.text }}>{skill.author}</span></span>
                  <Badge color={skill.authorType==="official"?C.accent:C.green}>{skill.authorType}</Badge>
                  <span style={{ fontFamily:"'JetBrains Mono',monospace", color:C.dim }}>v{skill.version}</span>
                </div>
                <div style={{ display:"flex", flexWrap:"wrap", gap:"4px", marginTop:"8px" }}>
                  {skill.divisions.map(d=><DivisionChip key={d} division={d} small />)}
                </div>
              </div>
            </div>
            <div style={{ display:"flex", gap:"8px", flexShrink:0, flexWrap:"wrap", justifyContent:"flex-end" }}>
              <Btn small onClick={()=>setFav(!favorited)} style={{ color:favorited?C.amber:C.muted }}>{favorited?"★ Saved":"☆ Save"}</Btn>
              <Btn small>↗ Fork</Btn>
              <Btn small>Follow</Btn>
              {authUser
                ?<Btn primary small disabled={!hasAccess&&!reqAccess} onClick={()=>hasAccess&&setInst(!installed)} style={!hasAccess?{opacity:0.5}:{}}>
                  {installed?"✓ Installed":hasAccess?"↓ Install":"🔒 Restricted"}
                </Btn>
                :<Btn primary small onClick={onAuthOpen}>Sign in to Install</Btn>}
            </div>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"1px", background:C.border, borderRadius:"10px", overflow:"hidden" }}>
            {[{icon:"↓",value:skill.installs,label:"Installs"},{icon:"★",value:skill.rating,label:"Rating"},{icon:"↗",value:skill.forks,label:"Forks"},{icon:"♡",value:skill.favorites,label:"Favorites"}].map((m,i)=>(
              <div key={i} style={{ background:C.surface, padding:"14px", textAlign:"center" }}>
                <div style={{ fontSize:"18px", fontWeight:700, color:C.text }}>{typeof m.value==="number"?m.value.toLocaleString():m.value}</div>
                <div style={{ fontSize:"10px", color:C.muted, marginTop:"2px" }}>{m.icon} {m.label}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ borderTop:`1px solid ${C.border}`, padding:"0 16px", display:"flex", overflowX:"auto" }}>
          {tabs.map(tabBtn)}
        </div>
      </div>

      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:"14px", padding:"28px", marginTop:"2px",
        boxShadow:C.mode==="light"?"0 2px 12px rgba(0,0,0,0.05)":"none" }}>
        {tab==="overview"&&(
          <div>
            <p style={{ fontSize:"14px", color:C.muted, lineHeight:"1.7", margin:"0 0 22px" }}>{skill.shortDesc}.</p>
            {[["When to Use",skill.whenToUse],].map(([h,body])=>(
              <div key={h}>
                <h3 style={{ fontSize:"12px", fontWeight:600, color:C.dim, textTransform:"uppercase", letterSpacing:"1px", margin:"0 0 8px" }}>{h}</h3>
                <div style={{ padding:"14px", background:C.bg, borderRadius:"8px", border:`1px solid ${C.border}`, marginBottom:"18px" }}>
                  <p style={{ margin:0, fontSize:"13px", color:C.muted, lineHeight:"1.7" }}>{body}</p>
                </div>
              </div>
            ))}
            <h3 style={{ fontSize:"12px", fontWeight:600, color:C.dim, textTransform:"uppercase", letterSpacing:"1px", margin:"0 0 8px" }}>Trigger Phrases</h3>
            <div style={{ display:"flex", flexWrap:"wrap", gap:"8px", marginBottom:"18px" }}>
              {skill.triggers.map(t=><span key={t} style={{ padding:"5px 12px", borderRadius:"6px", background:C.accentDim, color:C.accent, fontFamily:"'JetBrains Mono',monospace", fontSize:"12px", border:`1px solid ${C.accent}22` }}>"{t}"</span>)}
            </div>
            <h3 style={{ fontSize:"12px", fontWeight:600, color:C.dim, textTransform:"uppercase", letterSpacing:"1px", margin:"0 0 8px" }}>Authorized Divisions</h3>
            <div style={{ display:"flex", flexWrap:"wrap", gap:"8px" }}>{skill.divisions.map(d=><DivisionChip key={d} division={d} />)}</div>
          </div>
        )}
        {tab==="how-to-use"&&(
          <div>
            <h3 style={{ fontSize:"12px", fontWeight:600, color:C.dim, textTransform:"uppercase", letterSpacing:"1px", margin:"0 0 8px" }}>How to Use</h3>
            <div style={{ padding:"16px", background:C.bg, borderRadius:"8px", border:`1px solid ${C.border}`, marginBottom:"22px" }}>
              <p style={{ margin:0, fontSize:"13px", color:C.muted, lineHeight:"1.75" }}>{skill.howToUse}</p>
            </div>
            <h3 style={{ fontSize:"12px", fontWeight:600, color:C.dim, textTransform:"uppercase", letterSpacing:"1px", margin:"0 0 8px" }}>Best Prompts</h3>
            <div style={{ display:"flex", flexDirection:"column", gap:"8px", marginBottom:"22px" }}>
              {skill.bestPrompts.map((p,i)=>(
                <div key={i} style={{ padding:"12px 16px", background:C.bg, borderRadius:"8px", border:`1px solid ${C.border}`,
                  display:"flex", justifyContent:"space-between", alignItems:"center", gap:"12px" }}>
                  <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:"12px", color:C.muted }}>{p}</span>
                  <Btn small onClick={()=>navigator.clipboard?.writeText(p)}>Copy</Btn>
                </div>
              ))}
            </div>
            <div style={{ padding:"12px 16px", background:C.amberDim, borderRadius:"8px", border:`1px solid ${C.amber}22` }}>
              <p style={{ margin:0, fontSize:"13px", color:C.amber, opacity:0.85, lineHeight:"1.65" }}>⚠ {skill.notes}</p>
            </div>
          </div>
        )}
        {tab==="install"&&(
          <div>
            {!hasAccess&&authUser&&(
              <div style={{ padding:"12px 16px", background:C.redDim, border:`1px solid ${C.red}30`, borderRadius:"8px", marginBottom:"20px" }}>
                <div style={{ fontSize:"13px", color:C.red, fontWeight:600, marginBottom:"4px" }}>🔒 Installation restricted</div>
                <div style={{ fontSize:"12px", color:C.red, opacity:0.8, lineHeight:"1.5" }}>Your division ({userDiv}) is not authorized. Request access above.</div>
              </div>
            )}
            {[
              { method:"claude-code", label:"Claude Code CLI", icon:"⌨", cmd:`claude skill install ${skill.slug}`, desc:"Recommended for developers." },
              { method:"mcp", label:"MCP Server", icon:"⚡", cmd:`# SkillHub MCP → install_skill("${skill.slug}")`, desc:"For teams using the SkillHub MCP server." },
              { method:"manual", label:"Manual Install", icon:"📋", cmd:`# Copy SKILL.md to:\n/mnt/skills/user/${skill.slug}/SKILL.md`, desc:"Works in all Claude environments." },
            ].map(m=>(
              <div key={m.method} style={{ marginBottom:"14px", padding:"16px", background:C.bg, borderRadius:"10px",
                border:`1px solid ${m.method===skill.installMethod?INSTALL_COLOR[m.method]+"44":C.border}`,
                opacity:!hasAccess&&authUser?0.5:1 }}>
                <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"6px" }}>
                  <span style={{ fontWeight:600, fontSize:"14px", color:C.text }}>{m.icon} {m.label}</span>
                  {m.method===skill.installMethod&&<Badge color={INSTALL_COLOR[m.method]}>Recommended</Badge>}
                </div>
                <p style={{ fontSize:"12px", color:C.muted, margin:"0 0 10px" }}>{m.desc}</p>
                <div style={{ background:C.codeBg, borderRadius:"6px", padding:"10px 14px" }}>
                  <pre style={{ margin:0, fontSize:"11px", color:C.mode==="dark"?"#5af2b0":"#0a5c38",
                    fontFamily:"'JetBrains Mono',monospace", whiteSpace:"pre-wrap" }}>{m.cmd}</pre>
                </div>
              </div>
            ))}
          </div>
        )}
        {tab==="reviews"&&<ReviewsTab skill={skill} authUser={authUser} onAuthOpen={onAuthOpen} />}
      </div>
    </div>
  );
}

// ─── Root ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [isDark, setIsDark]           = useState(true);
  const [view, setView]               = useState("home");
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [authUser, setAuthUser]       = useState(null);
  const [showAuth, setShowAuth]       = useState(false);
  const [showSubmit, setShowSubmit]   = useState(false);

  const theme = isDark ? DARK : LIGHT;

  const handleSelectSkill = s => { setSelectedSkill(s); setView("detail"); };
  const handleSearch      = () => { if(searchQuery.trim()) setView("search"); };
  const handleLogin       = u => { setAuthUser(u); setShowAuth(false); };
  const handleLogout      = () => setAuthUser(null);

  return (
    <ThemeCtx.Provider value={theme}>
      <div style={{ background:theme.bg, minHeight:"100vh", color:theme.text,
        fontFamily:"'Outfit',sans-serif",
        transition:"background 0.3s, color 0.3s" }}>
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
          *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
          ::-webkit-scrollbar { width:4px; height:4px; }
          ::-webkit-scrollbar-thumb { background:${theme.scrollThumb}; border-radius:2px; }
          input, textarea { transition: background 0.3s, border-color 0.2s; }
          input::placeholder, textarea::placeholder { color:${theme.dim}; }
          * { transition: background-color 0.25s, border-color 0.2s, color 0.2s; }
        `}</style>

        {showAuth    && <AuthModal onLogin={handleLogin} onClose={()=>setShowAuth(false)} />}
        {showSubmit  && authUser && <SubmitModal authUser={authUser} onClose={()=>setShowSubmit(false)} />}

        <Nav view={view} setView={setView} searchQuery={searchQuery} setSearchQuery={setSearchQuery}
          onSearch={handleSearch} authUser={authUser} onAuthOpen={()=>setShowAuth(true)}
          onLogout={handleLogout} onSubmitOpen={()=>setShowSubmit(true)}
          isDark={isDark} onThemeToggle={()=>setIsDark(d=>!d)} />

        <div style={{ paddingTop:"60px" }}>
          {view==="home"    && <HomeView    onSelectSkill={handleSelectSkill} setView={setView} setSearchQuery={setSearchQuery} authUser={authUser} />}
          {view==="browse"  && <BrowseView  onSelectSkill={handleSelectSkill} setView={setView} />}
          {view==="search"  && <SearchView  query={searchQuery} setView={setView} onSelectSkill={handleSelectSkill} />}
          {view==="filtered"&& <FilteredView onSelectSkill={handleSelectSkill} />}
          {view==="detail"  && <SkillDetailView skill={selectedSkill} setView={setView} authUser={authUser} onAuthOpen={()=>setShowAuth(true)} />}
        </div>
      </div>
    </ThemeCtx.Provider>
  );
}
