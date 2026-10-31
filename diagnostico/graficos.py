"""Gráficos Plotly do resultado."""

from __future__ import annotations

import plotly.graph_objects as go

from .calculos import brl

COR = {"good": "#2C7A4C", "warn": "#C17F14", "bad": "#B23F2B", "accent": "#17675A",
       "trilho": "#E3E8E4", "texto": "#13242B", "suave": "#5A6A6F"}
FONTE = dict(family="Source Sans Pro, sans-serif", color=COR["texto"])


def anel_nota(nota: int, nivel: str) -> go.Figure:
    fig = go.Figure(go.Pie(
        values=[nota, 100 - nota], hole=0.78, sort=False, direction="clockwise",
        marker=dict(colors=[COR[nivel], COR["trilho"]]), textinfo="none", hoverinfo="skip",
    ))
    fig.update_layout(
        showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=190,
        paper_bgcolor="rgba(0,0,0,0)", font=FONTE,
        annotations=[
            dict(text=f"<b>{nota}</b>", x=0.5, y=0.56, font=dict(size=40, color=COR["texto"]), showarrow=False),
            dict(text="de 100", x=0.5, y=0.36, font=dict(size=13, color=COR["suave"]), showarrow=False),
        ],
    )
    return fig


def radar_pilares(pilares: dict) -> go.Figure:
    nomes = list(pilares.keys())
    valores = list(pilares.values())
    fig = go.Figure(go.Scatterpolar(
        r=valores + valores[:1], theta=nomes + nomes[:1], fill="toself",
        line=dict(color=COR["accent"], width=2), fillcolor="rgba(23,103,90,0.22)",
        marker=dict(size=7, color=COR["accent"]),
        hovertemplate="%{theta}: %{r}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, 100], tickvals=[25, 50, 75, 100], showticklabels=False,
                            gridcolor=COR["trilho"], linecolor=COR["trilho"]),
            angularaxis=dict(gridcolor=COR["trilho"], linecolor=COR["trilho"],
                             tickfont=dict(size=12, color=COR["suave"])),
        ),
        showlegend=False, margin=dict(l=60, r=60, t=20, b=20), height=300,
        paper_bgcolor="rgba(0,0,0,0)", font=FONTE,
    )
    return fig


def regua_equilibrio(faturamento: float, ponto_equilibrio: float) -> go.Figure:
    ok = faturamento >= ponto_equilibrio
    maximo = max(faturamento, ponto_equilibrio) * 1.18
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[maximo], y=[""], orientation="h", marker_color=COR["trilho"],
                         hoverinfo="skip", width=0.5))
    fig.add_trace(go.Bar(x=[faturamento], y=[""], orientation="h",
                         marker_color=COR["good" if ok else "bad"], width=0.5,
                         hovertemplate=f"Seu faturamento: {brl(faturamento)}<extra></extra>"))
    fig.add_vline(x=ponto_equilibrio, line_width=3, line_color=COR["texto"])
    fig.add_annotation(x=ponto_equilibrio, y=0.62, yref="paper", text=f"<b>Equilíbrio {brl(ponto_equilibrio)}</b>",
                       showarrow=False, yanchor="bottom", font=dict(size=13))
    fig.update_layout(
        barmode="overlay", showlegend=False, height=120, margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(visible=False, range=[0, maximo]), yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=FONTE,
    )
    return fig
