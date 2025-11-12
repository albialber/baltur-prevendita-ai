import streamlit as st
import pandas as pd
import pickle
from typing import List


REQUIRED_COLS = {"Codice", "Prodotto", "Prezzo di listino", "Descrizione"}


@st.cache_data(show_spinner=False)
def get_catalog_df() -> pd.DataFrame:
"""Restituisce il DataFrame prodotti. Priorità: embeddings.pkl -> listino_prodotti.xlsx."""
# 1) embeddings.pkl con df
try:
with open("embeddings.pkl", "rb") as f:
data = pickle.load(f)
df = data.get("df")
if isinstance(df, pd.DataFrame) and REQUIRED_COLS.issubset(df.columns):
return df.copy()
except Exception:
pass
# 2) Excel di fallback
df = pd.read_excel("listino_prodotti.xlsx")
if not REQUIRED_COLS.issubset(df.columns):
raise ValueError(f"Il file listino deve contenere le colonne: {REQUIRED_COLS}")
return df.copy()


def prezzo_con_sconti(prezzo: float, sconti: List[float]) -> float:
p = float(prezzo)
for s in sconti:
p *= (1 - float(s)/100.0)
return p


# Tabella markdown coerente con le app


def _escape_md(text: str) -> str:
if text is None:
return ""
return str(text).replace("|", "\\|")


def rows_to_markdown_table(rows, headers):
md = "| " + " | ".join(headers) + " |\n"
md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
for r in rows:
cells = [
_escape_md(r.get("Codice", "")),
_escape_md(r.get("Prodotto", "")),
str(int(r.get("Quantità", 0))),
_escape_md(r.get("Prezzo unitario", "")),
_escape_md(r.get("Prezzo totale", "")),
]
md += "| " + " | ".join(cells) + " |\n"
return md
