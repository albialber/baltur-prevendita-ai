import streamlit as st
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import re

st.set_page_config(page_title="Baltur PREVENDITA AI", layout="centered")

# Logo grande centrato da file locale
st.image("baltur_logo.png", width=300)

# Titolo senza emoticon
st.title("Baltur Prevendita AI")

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

    if righe_tabella:
        st.subheader("📊 Riepilogo preventivo")
        df_tabella = pd.DataFrame(righe_tabella)
        st.table(df_tabella)
        st.markdown(f"**Totale configurazione:** {totale_configurazione:,.2f} €")
