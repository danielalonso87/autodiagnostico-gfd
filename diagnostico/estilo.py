"""CSS do app (cartões, pílulas, alertas)."""

CSS = """
<style>
:root {--gf-good:#2C7A4C; --gf-bad:#B23F2B;}
.gf-sim {display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; margin-bottom:6px;}
@media (max-width: 560px){ .gf-sim {grid-template-columns:1fr;} }
.gf-sim div {background:#F2F4F1; border-radius:10px; padding:10px 12px; display:flex; flex-direction:column; gap:2px; min-width:0;}
.gf-sim span {font-size:.8rem; color:#5A6A6F;}
.gf-sim b {font-size:1.05rem; line-height:1.3; color:#13242B; overflow-wrap:anywhere;}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none !important;}
.block-container {padding-top: 2rem; padding-bottom: 4rem; max-width: 820px;}
h1, h2, h3 {letter-spacing: -0.01em;}
.gf-marca {display:flex; align-items:center; gap:10px; margin-bottom: .5rem;}
.gf-marca .sel {width:36px; height:36px; border-radius:9px; background:#17675A; color:#fff;
  display:grid; place-items:center; font-weight:700;}
.gf-marca b {display:block; line-height:1.2;}
.gf-marca span {font-size:.8rem; color:#5A6A6F;}
.gf-eyebrow {font-size:.75rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#17675A;}
.gf-muted {color:#5A6A6F;}
.gf-exemplo {font-size:.85rem; background:#E9EDE9; border-radius:8px; padding:8px 12px; color:#5A6A6F;}
.gf-pill {display:inline-block; font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  padding:3px 10px; border-radius:99px; white-space:nowrap;}
.gf-good {background:#E1F0E5; color:#2C7A4C;}
.gf-warn {background:#F6ECD8; color:#A86B12;}
.gf-bad  {background:#F6E0DA; color:#B23F2B;}
.gf-none {background:#E8ECEA; color:#7C8A8E;}
.gf-kpis {display:grid; grid-template-columns:repeat(3, 1fr); gap:12px;}
@media (max-width: 760px){ .gf-kpis {grid-template-columns:repeat(2, 1fr);} }
@media (max-width: 480px){ .gf-kpis {grid-template-columns:1fr;} }
.gf-kpi {background:#fff; border:1px solid #D5DCD7; border-top:4px solid #7C8A8E; border-radius:12px;
  padding:14px; display:flex; flex-direction:column; gap:4px;}
.gf-kpi.good {border-top-color:#2C7A4C;} .gf-kpi.warn {border-top-color:#C17F14;} .gf-kpi.bad {border-top-color:#B23F2B;}
.gf-kpi .lab {display:flex; justify-content:space-between; gap:8px; align-items:center;
  font-size:.8rem; font-weight:600; color:#5A6A6F;}
.gf-kpi .val {font-size:1.45rem; font-weight:700; font-variant-numeric:tabular-nums; color:#13242B;}
.gf-kpi .sub {font-size:.8rem; color:#5A6A6F; line-height:1.4;}
.gf-alerta {background:#fff; border:1px solid #D5DCD7; border-radius:12px; padding:14px 16px;
  display:grid; grid-template-columns:auto 1fr; gap:14px; margin-bottom:10px;}
.gf-alerta .n {width:30px; height:30px; border-radius:50%; display:grid; place-items:center; font-weight:700;}
.gf-alerta b {display:block; margin-bottom:2px; color:#13242B;}
.gf-alerta p {margin:0; font-size:.9rem; color:#5A6A6F;}
.gf-cta {background:#17675A; color:#fff; border-radius:16px; padding:22px 24px; margin: 8px 0 12px;}
.gf-cta h3 {color:#fff; margin:0 0 6px;}
.gf-cta p {margin:0; opacity:.9;}
.gf-legenda {display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; font-size:.85rem; color:#5A6A6F;}
</style>
"""
