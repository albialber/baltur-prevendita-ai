import streamlit as st
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import re

# Import dalla logica del configuratore
from rules_configuratore_mk import ConfigInput, genera_distinta

st.set_page_config(page_title="Baltur PREVENDITA AI", layout="centered")

# Logo e titolo
st.image("baltur_logo.png", width=300)
st.title("Baltur Prevendita AI")

# =========================
# CACHE RISORSE
# =========================
@st.cache_resource(show_spinner=False)
def load_embeddings():
    with open("embeddings.pkl", "rb") as f:
        data = pickle.load(f)
    df = data["df"]  # deve avere: Codice, Prodotto, Prezzo di listino, Descrizione
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return df, model

df, model = load_embeddings()

# Testo completo per filtri parole chiave
testo_completo = (
    df["Codice"].fillna('').astype(str) + " " +
    df["Prodotto"].fillna('').astype(str) + " " +
    df["Descrizione"].fillna('').astype(str)
).str.lower()

# =========================
# TAB
# =========================
tabs = st.tabs(["🔎 Ricerca testuale", "🧩 Configuratore SMILE ENERGY MK"])

# -------------------------
# TAB 1: Ricerca testuale
# -------------------------
with tabs[0]:
    descrizione = st.text_area(
        "Descrivi cosa ti serve (usa + per più prodotti, es. 2x pompa '300' + accumulo 200L)",
        height=150
    )

# -------------------------
# TAB 2: Configuratore
# -------------------------
with tabs[1]:
    st.markdown("Compila il configuratore. L’output verrà sommato alla ricerca testuale.")

    # Mappatura macro-configurazioni -> valori attesi dalla logica
    macro_label_to_value = {
        "Cascata interno - in linea": "INT_LINEA",
        "Cascata interno - ad isola": "INT_ISOLA",
        "Cascata esterno": "ESTERNO",
        "Singola interno": "SINGOLO_INT",
        "Singola esterno": "SINGOLO_EST",
    }
    macro_label = st.selectbox("Macro-configurazione", list(macro_label_to_value.keys()), index=0)
    macro_value = macro_label_to_value[macro_label]

    cfg_input = None  # lo costruiremo sotto

    # ===== CASCATA =====
    if macro_value in ("INT_LINEA", "INT_ISOLA", "ESTERNO"):
        st.subheader("Selezione caldaie (totale 2–4)")
        c1, c2, c3 = st.columns(3)
        with c1:
            mk50 = st.number_input("SMILE ENERGY MK 50", 0, 4, 0, step=1)
            mk70 = st.number_input("SMILE ENERGY MK 70", 0, 4, 0, step=1)
        with c2:
            mk90 = st.number_input("SMILE ENERGY MK 90", 0, 4, 0, step=1)
            mk115 = st.number_input("SMILE ENERGY MK 115", 0, 4, 0, step=1)
        with c3:
            mk160sp = st.number_input("SMILE ENERGY MK 160SP", 0, 4, 0, step=1)
            mk160 = st.number_input("SMILE ENERGY MK 160", 0, 4, 0, step=1)

        caldaie_sel = {
            "SMILE ENERGY MK 50": mk50,
            "SMILE ENERGY MK 70": mk70,
            "SMILE ENERGY MK 90": mk90,
            "SMILE ENERGY MK 115": mk115,
            "SMILE ENERGY MK 160SP": mk160sp,
            "SMILE ENERGY MK 160": mk160,
        }
        tot_calde = sum(caldaie_sel.values())
        st.caption(f"Totale caldaie selezionate: **{tot_calde}** (min 2, max 4)")

        # Selettori separatore + eventuale sotto-opzione
        sep_label_to_value = {
            "NESSUNA": "NESSUNA",
            "SCAMBIATORE SALDOBRASATO SSB": "SSB",
            "SCAMBIATORE ISPEZIONABILE SII PRO": "SII_PRO",
            "EQUILIBRATORE DI PORTATA": "EQUILIBRATORE",
        }
        separatore_label = st.selectbox(
            "Seleziona separatore idraulico",
            list(sep_label_to_value.keys()),
            index=0
        )
        separatore_value = sep_label_to_value[separatore_label]

        sottoopzione = None
        ssb_code = None
        sii_code = None

        if separatore_value in ("SSB", "EQUILIBRATORE"):
            sottoopzione = st.radio("Sotto-opzione", ["KIT_TUBI", "KIT_TUBI_CIRC", "NESSUNA"],
                                    index=0, horizontal=True)

        if separatore_value == "SSB":
            ssb_code = st.text_input("Codice scambiatore SSB (opzionale)", value="") or None

        if separatore_value == "SII_PRO":
            sii_code = st.text_input("Codice scambiatore SII PRO (opzionale)", value="") or None

        centralina = st.selectbox("Centralina", ["ALPHA", "THETA", "OMEGA", "MODBUS", "0-10V"], index=0)

        # Costruisco l'input per la logica (dizionario, non lista)
        cfg_input = ConfigInput(
            macro=macro_value,
            caldaie=caldaie_sel,
            separatore=separatore_value,
            sottoopzione=sottoopzione,
            ssb_code=ssb_code,
            sii_code=sii_code,
            centralina=centralina,
        )

    # ===== SINGOLA =====
    if macro_value in ("SINGOLO_INT", "SINGOLO_EST"):
        st.subheader("Configurazione singola")
        modello = st.selectbox("Modello", ["MK 50", "MK 70", "MK 90", "MK 115", "MK 160SP", "MK 160"], index=0)
        sottocat = st.radio("Sottocategoria", ["SSB", "EQUILIBRATORE"], index=0, horizontal=True)
        cfg_input = ConfigInput(
            macro=macro_value,
            singola_modello=modello,
            singola_sottocat=sottocat
        )

# -------------------------
# Prezzi e Sconti
# -------------------------
st.markdown("---")
mostra_netto = st.checkbox("Mostra prezzi netti invece del listino", value=mostra_netto)
if mostra_netto and not sconti:
    sconti = [
        st.number_input(f"Sconto {i+1}", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        for i in range(4)
    ]
elif not mostra_netto:
    sconti = [0.0, 0.0, 0.0, 0.0]

# -------------------------
# UTILS
# -------------------------
def applica_sconti(prezzo: float, sconti: list[float]) -> float:
    p = float(prezzo)
    for s in sconti:
        p *= (1 - float(s)/100.0)
    return p

def aggiungi_riga(righe_tabella: list, prodotto_row: pd.Series, quantita: int, mostra_netto: bool, sconti: list[float]) -> tuple[list, float]:
    prezzo_unitario = float(prodotto_row["Prezzo di listino"])
    if mostra_netto:
        prezzo_unitario = applica_sconti(prezzo_unitario, sconti)
    prezzo_totale = prezzo_unitario * quantita
    righe_tabella.append({
        "Codice": prodotto_row["Codice"],
        "Prodotto": prodotto_row["Prodotto"],
        "Quantità": quantita,
        "Prezzo unitario": f"{prezzo_unitario:,.2f} €",
        "Prezzo totale": f"{prezzo_totale:,.2f} €"
    })
    return righe_tabella, prezzo_totale

# -------------------------
# GENERA PREVENTIVO
# -------------------------
if st.button("Genera preventivo"):
    righe_tabella = []
    totale_configurazione = 0.0

    # ----- 1) Ricerca testuale + embedding -----
    descrizioni_singole = [s.strip() for s in (descrizione or "").split("+") if s.strip()]

    for singola in descrizioni_singole:
        query = singola.lower()

        # quantità (2x prodotto | prodotto x2)
        quantita = 1
        quant_match = re.search(r"^\s*(\d+)\s*[xX]\s*", query)
        if quant_match:
            quantita = int(quant_match.group(1))
            query = query[quant_match.end():]
        else:
            quant_match = re.search(r"[xX]\s*(\d+)$", query)
            if quant_match:
                quantita = int(quant_match.group(1))
                query = query[:quant_match.start()]

        # filtri
        keywords = [w for w in re.findall(r"\b\w{2,}\b", query) if w not in {"da","in","di","con","e"}]
        exact_keywords = re.findall(r"'([^']+)'|\"([^\"]+)\"", singola)
        exact_keywords = [ek[0] or ek[1] for ek in exact_keywords if ek[0] or ek[1]]

        maschera = testo_completo.apply(
            lambda x: all(k in x for k in keywords) and all(re.search(rf"\b{re.escape(k)}\b", x) for k in exact_keywords)
        )
        df_filtrato = df[maschera].copy()

        if df_filtrato.empty:
            st.warning(f"Nessun prodotto trovato per: **{singola}**")
            continue

        query_embedding = model.encode([singola])
        testo_emb = (
            df_filtrato["Codice"].fillna('').astype(str) + " " +
            df_filtrato["Prodotto"].fillna('').astype(str) + " " +
            df_filtrato["Descrizione"].fillna('').astype(str)
        ).tolist()
        emb_parziali = model.encode(testo_emb)

        index_parziale = faiss.IndexFlatL2(len(emb_parziali[0]))
        index_parziale.add(np.array(emb_parziali))

        D, I = index_parziale.search(np.array(query_embedding), 1)
        idx = I[0][0]

        prodotto = df_filtrato.iloc[idx]
        righe_tabella, subtot = aggiungi_riga(righe_tabella, prodotto, quantita, mostra_netto, sconti)
        totale_configurazione += subtot

    # ----- 2) Distinta dal configuratore -----
    if cfg_input is not None:
        try:
            distinta = genera_distinta(cfg_input)   # List[LineItem] con code,name,qty
            for item in distinta:
                rec = df[df["Codice"].astype(str) == str(item.code)]
                if rec.empty:
                    st.warning(f"Codice non trovato in listino: {item.code} ({item.name})")
                    continue
                prodotto_row = rec.iloc[0]
                righe_tabella, subtot = aggiungi_riga(righe_tabella, prodotto_row, item.qty, mostra_netto, sconti)
                totale_configurazione += subtot
        except Exception as e:
            st.error(f"Configuratore: {e}")

    # ----- 3) Output -----
    if righe_tabella:
        st.subheader("📊 Riepilogo preventivo")
        df_tabella = pd.DataFrame(righe_tabella)
        st.table(df_tabella)
        st.markdown(f"**Totale configurazione:** {totale_configurazione:,.2f} €")
    else:
        st.info("Nessuna voce da mostrare: compila la ricerca testuale e/o il configuratore, poi clicca **Genera preventivo**.")
