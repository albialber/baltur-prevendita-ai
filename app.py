import streamlit as st
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import re

# === Configuratore: importa le regole
from rules_configuratore_mk import ConfigInput, genera_distinta

st.set_page_config(page_title="Baltur PREVENDITA AI", layout="centered")

# Logo grande centrato da file locale
st.image("baltur_logo.png", width=300)

# Titolo senza emoticon
st.title("Baltur Prevendita AI")

# =========================
# **SEZIONE ORIGINALE** (ripristinata IDENTICA)
# =========================
descrizione = st.text_area(
    "Descrivi cosa ti serve (usa + per più prodotti, es. 2x pompa '300' + accumulo 200L)",
    height=150
)

mostra_netto = st.checkbox("Mostra prezzi netti invece del listino")

if mostra_netto:
    sconti = [
        st.number_input(f"Sconto {i+1}", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        for i in range(4)
    ]
else:
    sconti = []

# =========================
# **NUOVA SEZIONE**: CONFIGURATORE (aggiunta sotto, non altera la logica/UX di sopra)
# =========================
st.markdown("---")
st.subheader("🧩 Configuratore SMILE ENERGY MK")

# Scelta macro-configurazione (con opzione 'Nessuna' per non usarlo)
macro_label_to_value = {
    "Nessuna (usa solo la ricerca testuale)": None,
    "Cascata interno - in linea": "INT_LINEA",
    "Cascata interno - ad isola": "INT_ISOLA",
    "Cascata esterno": "ESTERNO",
    "Singola interno": "SINGOLO_INT",
    "Singola esterno": "SINGOLO_EST",
}
macro_label = st.selectbox(
    "Seleziona configurazione",
    list(macro_label_to_value.keys()),
    index=0
)
macro_value = macro_label_to_value[macro_label]

cfg_input = None

if macro_value in ("INT_LINEA", "INT_ISOLA", "ESTERNO"):
    st.caption("Seleziona quantità (totale 2–4 caldaie, anche modelli diversi).")
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
    st.caption(f"Totale caldaie selezionate: **{tot_calde}**")

    # Separatore (mappa etichetta -> valore atteso dalla logica)
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
        sottoopzione = st.radio("Sotto-opzione", ["KIT_TUBI", "KIT_TUBI_CIRC", "NESSUNA"], index=0, horizontal=True)

    if separatore_value == "SSB":
        ssb_code = st.text_input("Codice scambiatore SSB (opzionale)", value="") or None
    if separatore_value == "SII_PRO":
        sii_code = st.text_input("Codice scambiatore SII PRO (opzionale)", value="") or None

    centralina = st.selectbox("Centralina", ["ALPHA", "THETA", "OMEGA", "MODBUS", "0-10V"], index=0)

    # Costruisco l'input per la logica (dizionario come atteso)
    cfg_input = ConfigInput(
        macro=macro_value,
        caldaie=caldaie_sel,
        separatore=separatore_value,
        sottoopzione=sottoopzione,
        ssb_code=ssb_code,
        sii_code=sii_code,
        centralina=centralina,
    )

elif macro_value in ("SINGOLO_INT", "SINGOLO_EST"):
    st.caption("Configurazione singola")
    modello = st.selectbox("Modello", ["MK 50", "MK 70", "MK 90", "MK 115", "MK 160SP", "MK 160"], index=0)
    sottocat = st.radio("Sottocategoria", ["SSB", "EQUILIBRATORE"], index=0, horizontal=True)
    cfg_input = ConfigInput(
        macro=macro_value,
        singola_modello=modello,
        singola_sottocat=sottocat
    )

# =========================
# **BOTTONE ORIGINALE** (resta dov’è e fa tutto)
# =========================
if st.button("Genera preventivo"):
    with open("embeddings.pkl", "rb") as f:
        data = pickle.load(f)

    df = data["df"]

    testo_completo = (
        df["Codice"].fillna('').astype(str) + " " +
        df["Prodotto"].fillna('').astype(str) + " " +
        df["Descrizione"].fillna('').astype(str)
    ).str.lower()

    model = SentenceTransformer("all-MiniLM-L6-v2")

    righe_tabella = []
    totale_configurazione = 0.0

    # ======= Parte 1: RICERCA TESTUALE (identica alla tua) =======
    descrizioni_singole = [s.strip() for s in descrizione.split("+") if s.strip()]

    for singola in descrizioni_singole:
        query = singola.lower()

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
        prezzo_unitario = prodotto["Prezzo di listino"]

        if mostra_netto:
            for sconto in sconti:
                prezzo_unitario *= (1 - sconto / 100)

        prezzo_totale = prezzo_unitario * quantita
        totale_configurazione += prezzo_totale

        st.markdown(f"""
        🧾 **{prodotto['Prodotto']}**  
        **Codice:** `{prodotto['Codice']}`  
        **Quantità:** {quantita}  
        **Prezzo unitario:** {prezzo_unitario:,.2f} € ({'netto' if mostra_netto else 'listino'})  
        **Prezzo totale:** {prezzo_totale:,.2f} €  
        **Descrizione:** {prodotto['Descrizione']}  
        """)

        righe_tabella.append({
            "Codice": prodotto["Codice"],
            "Prodotto": prodotto["Prodotto"],
            "Quantità": quantita,
            "Prezzo unitario": f"{prezzo_unitario:,.2f} €",
            "Prezzo totale": f"{prezzo_totale:,.2f} €"
        })

    # ======= Parte 2: DISTINTA dal CONFIGURATORE (se usato) =======
    if cfg_input is not None:
        try:
            distinta = genera_distinta(cfg_input)   # List[LineItem] (code,name,qty)
            for item in distinta:
                rec = df[df["Codice"].astype(str) == str(item.code)]
                if rec.empty:
                    st.warning(f"Codice non trovato in listino: {item.code} ({item.name})")
                    continue
                prodotto_row = rec.iloc[0]

                prezzo_unitario = prodotto_row["Prezzo di listino"]
                if mostra_netto:
                    for sconto in sconti:
                        prezzo_unitario *= (1 - sconto / 100)

                prezzo_totale = prezzo_unitario * item.qty
                totale_configurazione += prezzo_totale

                # stampa breve (coerente con la parte sopra)
                st.markdown(f"""
                🧾 **{prodotto_row['Prodotto']}**  
                **Codice:** `{prodotto_row['Codice']}`  
                **Quantità:** {item.qty}  
                **Prezzo unitario:** {prezzo_unitario:,.2f} € ({'netto' if mostra_netto else 'listino'})  
                **Prezzo totale:** {prezzo_totale:,.2f} €  
                **Descrizione:** {prodotto_row['Descrizione']}  
                """)

                righe_tabella.append({
                    "Codice": prodotto_row["Codice"],
                    "Prodotto": prodotto_row["Prodotto"],
                    "Quantità": item.qty,
                    "Prezzo unitario": f"{prezzo_unitario:,.2f} €",
                    "Prezzo totale": f"{prezzo_totale:,.2f} €"
                })
        except Exception as e:
            st.error(f"Configuratore: {e}")

    # ======= Riepilogo finale (come già facevi) =======
    if righe_tabella:
        st.subheader("📊 Riepilogo preventivo")
        df_tabella = pd.DataFrame(righe_tabella)
        st.table(df_tabella)
        st.markdown(f"**Totale configurazione:** {totale_configurazione:,.2f} €")
