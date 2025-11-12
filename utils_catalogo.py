import pandas as pd
import pickle
import streamlit as st

# ==========================================================
# Utility per caricamento listino e tabelle
# ==========================================================

@st.cache_data(show_spinner=False)
def get_catalog_df() -> pd.DataFrame:
    """
    Carica il listino prodotti da embeddings.pkl o da prodotti.xlsx.
    Ritorna un DataFrame con le colonne standard:
    Codice, Prodotto, Prezzo di listino, Descrizione
    """
    try:
        with open("embeddings.pkl", "rb") as f:
            data = pickle.load(f)
        df = data["df"]
    except Exception:
        df = pd.read_excel("prodotti.xlsx")  # fallback
    colonne = ["Codice", "Prodotto", "Prezzo di listino", "Descrizione"]
    mancanti = [c for c in colonne if c not in df.columns]
    if mancanti:
        raise ValueError(f"Colonne mancanti nel listino: {mancanti}")
    return df[colonne].copy()


def prezzo_con_sconti(prezzo: float, sconti: list[float]) -> float:
    """
    Applica fino a 4 sconti cumulativi al prezzo.
    """
    p = float(prezzo)
    for s in sconti:
        p *= (1 - float(s) / 100.0)
    return p


def _escape_md(text: str) -> str:
    """Evita che simboli speciali rompano la tabella Markdown."""
    if text is None:
        return ""
    return str(text).replace("|", "\\|")


def rows_to_markdown_table(rows: list[dict], visible_cols: list[str]) -> str:
    """
    Converte una lista di dict (righe) in una tabella Markdown pulita.
    """
    if not rows:
        return "_Nessun elemento nella configurazione._"

    md = "| " + " | ".join(visible_cols) + " |\n"
    md += "| " + " | ".join(["---"] * len(visible_cols)) + " |\n"
    for r in rows:
        cells = []
        for col in visible_cols:
            val = r.get(col, "")
            cells.append(_escape_md(val))
        md += "| " + " | ".join(cells) + " |\n"
    return md
