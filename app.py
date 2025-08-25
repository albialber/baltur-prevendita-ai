import streamlit as st
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import re

# === Configuratori ===
from rules_configuratore_mk import ConfigInput as ConfigInputMK, genera_distinta as genera_distinta_mk
from rules_configuratore_solare import ConfigSolareInput, genera_distinta_solare

# -------------------------------------------------------
# Impostazioni pagina
# -------------------------------------------------------
st.set_page_config(page_title="Baltur PREVENDITA AI", layout="centered")

# Logo grande centrato da file locale
st.image("baltur_logo.png", width=300)

# Titolo senza emoticon
st.title("Baltur Prevendita AI")

# -------------------------------------------------------
# Stato applicazione
# -------------------------------------------------------
if "output_rows" not in st.session_state:
    st.session_state["output_rows"] = []  # lista dizionari visibili in tabella
if "output_rows_internal" not in st.session_state:
    # con colonne ausiliarie per ricalcolo (es. UnitPriceRaw, Descrizione)
    st.session_state["output_rows_internal"] = []
if "totale_conf" not in st.session_state:
    st.session_state["totale_conf"] = 0.0
if "rendered_this_run" not in st.session_state:
    st.session_state["rendered_this_run"] = False
if "show_solar" not in st.session_state:
    st.session_state["show_solar"] = False
if "show_details" not in st.session_state:
    st.session_state["show_details"] = False
if "df_current_full" not in st.session_state:
    st.session_state["df_current_full"] = None  # dataframe completo (incluse colonne "nascoste")
if "df_original_qty" not in st.session_state:
    st.session_state["df_original_qty"] = None  # lista quantità originali (per abilitare Ricalcola)

# -------------------------------------------------------
# SEZIONE ORIGINALE: prompt testuale + sconti (INVARIATA)
# -------------------------------------------------------
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

# -------------------------------------------------------
# CONFIGURATORE SMILE ENERGY MK (INVARIATO NEL COMPORTAMENTO)
# -------------------------------------------------------
st.markdown("---")
st.subheader("🧩 Configuratore SMILE ENERGY MK")

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

cfg_input_mk = None

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

    cfg_input_mk = ConfigInputMK(
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
    cfg_input_mk = ConfigInputMK(
        macro=macro_value,
        singola_modello=modello,
        singola_sottocat=sottocat
    )

# -------------------------------------------------------
# NUOVA SEZIONE: Configuratore solare termico (AGGIUNTA)
# -------------------------------------------------------
st.markdown("---")
st.subheader("☀️ Configuratore solare termico")

# mostra gli step solo se l'utente clicca il bottone
if st.button("Apri configuratore solare termico"):
    st.session_state["show_solar"] = True

cfg_input_sol = None
if st.session_state["show_solar"]:
    # Step 1: tipologia tetto
    tetto_map = {"Tetto inclinato a coppi": "INCLINATO_COPPI", "Tetto piano": "PIANO"}
    tetto_label = st.selectbox("Tipologia di tetto", list(tetto_map.keys()), index=0)
    tetto_val = tetto_map[tetto_label]

    # Step 2: tipologia pannello
    pannello_map = {"ETASUN 25": "ETASUN25", "ETASUN 20": "ETASUN20"}
    pannello_label = st.selectbox("Tipologia di pannello", list(pannello_map.keys()), index=0)
    pannello_val = pannello_map[pannello_label]

    # Step 3: n. pannelli
    n_pannelli = st.number_input("Numero pannelli", min_value=1, step=1, value=1)

    # Step 4: n. file
    n_file = st.number_input("Numero file", min_value=1, step=1, value=1)

    # Step 5: centralina
    centr_label = st.selectbox("Tipo di centralina", ["SBMTDC_V5", "SBLTDC_V3"], index=0)
    centr_val = "SBMTDC_V5" if centr_label == "SBMTDC_V5" else "SBLTDC_V3"

    # Step 6: volume minimo consigliato (formula richiesta: area_totale * 60)
    area = 2.35 if pannello_val == "ETASUN25" else 1.87
    superficie_tot = area * n_pannelli
    volume_consigliato = superficie_tot * 60  # L
    st.info(
        f"Superficie totale: **{superficie_tot:.2f} m²**  •  "
        f"Volume minimo consigliato: **{volume_consigliato:.0f} L**"
    )

    cfg_input_sol = ConfigSolareInput(
        tetto=tetto_val,
        pannello=pannello_val,
        n_pannelli=int(n_pannelli),
        n_file=int(n_file),
        centralina=centr_val
    )

# -------------------------------------------------------
# Utils: sconti + riepilogo + Order Entry
# -------------------------------------------------------
def applica_sconti(prezzo: float, sconti: list[float]) -> float:
    p = float(prezzo)
    for s in sconti:
        p *= (1 - float(s)/100.0)
    return p

def df_to_markdown_table(df: pd.DataFrame) -> str:
    # converte una tabella in markdown pipe-friendly
    return df.to_markdown(index=False)

def show_summary_table_and_actions(df_full: pd.DataFrame, total: float):
    """Mostra tabella (editabile su Quantità) + azioni: ricalcola, copia tabella, dati order entry, dettagli.
       df_full deve contenere anche le colonne 'UnitPriceRaw' e 'Descrizione' (non mostrate).
    """
    if df_full is None or df_full.empty:
        return

    st.subheader("📊 Riepilogo preventivo")

    # Vista per l'utente (solo colonne visibili)
    visible_cols = ["Codice", "Prodotto", "Quantità", "Prezzo unitario", "Prezzo totale"]
    df_view = df_full[visible_cols].copy()

    # Editor: permetti modifica Quantità, nascondi indice
    edited = st.data_editor(
        df_view,
        hide_index=True,
        use_container_width=True,
        key="out_table_editor",
        disabled=["Codice", "Prodotto", "Prezzo unitario", "Prezzo totale"],  # solo Quantità editabile
    )

    # Rileva modifiche alle quantità
    orig_qty = st.session_state.get("df_original_qty")
    current_qty = edited["Quantità"].tolist()
    qty_modified = (orig_qty is not None) and (current_qty != orig_qty)

    # Totale corrente visualizzato
    st.markdown(f"**Totale configurazione:** {total:,.2f} €")

    # Azioni sotto tabella
    c1, c2, c3 = st.columns([1,1,1])

    with c1:
        # Ricalcolo abilitato solo se quantità modificate
        if st.button("♻️ Ricalcola", disabled=not qty_modified):
            df_new_view = edited.copy()
            # Ricostruisci df_full nuovo fondendo quantità aggiornate con dati tecnici originali
            df_old_full = st.session_state["df_current_full"].copy()
            df_old_full["Quantità"] = df_new_view["Quantità"].values  # mantieni stesso ordine
            # Ricalcola totali riga e totale
            new_total = 0.0
            for i in range(len(df_old_full)):
                unit_raw = float(df_old_full.loc[i, "UnitPriceRaw"])
                q = int(df_old_full.loc[i, "Quantità"])
                row_total = unit_raw * q
                df_old_full.loc[i, "Prezzo unitario"] = f"{unit_raw:,.2f} €"
                df_old_full.loc[i, "Prezzo totale"] = f"{row_total:,.2f} €"
                new_total += row_total

            # Aggiorna stato globale (per Order Entry e persistente)
            st.session_state["df_current_full"] = df_old_full
            st.session_state["df_original_qty"] = df_old_full["Quantità"].tolist()
            st.session_state["output_rows_internal"] = df_old_full.to_dict(orient="records")
            st.session_state["output_rows"] = df_old_full[visible_cols].to_dict(orient="records")
            st.session_state["totale_conf"] = float(new_total)

            st.success(f"Ricalcolo completato. Nuovo totale: {new_total:,.2f} €")

    with c2:
        if st.button("📋 Copia tabella (Markdown)"):
            df_for_copy = st.session_state.get("df_current_full", df_full)
            md = df_to_markdown_table(df_for_copy[visible_cols])
            st.subheader("Tabella (Markdown)")
            st.code(md, language=None)

    with c3:
        if st.button("📋 Dati per Order Entry"):
            df_for_copy = st.session_state.get("df_current_full", df_full)
            lines = [f"{str(r['Codice']).strip()};{int(r['Quantità'])}" for _, r in df_for_copy[visible_cols].iterrows()]
            payload = "\n".join(lines)
            st.subheader("Dati per Order Entry")
            st.code(payload, language=None)

    # Dettagli (toggle)
    if st.button("🔎 Dettagli"):
        st.session_state["show_details"] = not st.session_state.get("show_details", False)

    if st.session_state.get("show_details"):
        st.markdown("### Dettagli voci")
        df_for_det = st.session_state.get("df_current_full", df_full)
        for _, r in df_for_det.iterrows():
            st.markdown(
                f"**{r['Prodotto']}**  \n"
                f"**Codice:** `{r['Codice']}`  \n"
                f"**Quantità:** {int(r['Quantità'])}  \n"
                f"**Descrizione:** {r.get('Descrizione','')}"
            )

# -------------------------------------------------------
# GENERA PREVENTIVO (stessa logica consolidata + integrazioni)
# -------------------------------------------------------
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

    righe_tabella = []               # visivo (senza colonne tecniche)
    righe_tabella_internal = []      # con UnitPriceRaw e Descrizione
    totale_configurazione = 0.0

    # ======= Parte 1: RICERCA TESTUALE (logica invariata) =======
    descrizioni_singole = [s.strip() for s in (descrizione or "").split("+") if s.strip()]

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
        unit_raw = float(prodotto["Prezzo di listino"])

        if mostra_netto:
            for sconto in sconti:
                unit_raw *= (1 - sconto / 100)

        row_total = unit_raw * quantita
        totale_configurazione += row_total

        vis_full = {
            "Codice": str(prodotto["Codice"]),
            "Prodotto": str(prodotto["Prodotto"]),
            "Quantità": int(quantita),
            "Prezzo unitario": f"{unit_raw:,.2f} €",
            "Prezzo totale": f"{row_total:,.2f} €",
            "UnitPriceRaw": float(unit_raw),
            "Descrizione": str(prodotto["Descrizione"]),
        }
        righe_tabella_internal.append(vis_full)
        righe_tabella.append({k: vis_full[k] for k in ["Codice","Prodotto","Quantità","Prezzo unitario","Prezzo totale"]})

    # ======= Parte 2: DISTINTA dal CONFIGURATORE MK (logica invariata) =======
    if cfg_input_mk is not None:
        try:
            distinta = genera_distinta_mk(cfg_input_mk)   # List[LineItem]
            for item in distinta:
                rec = df[df["Codice"].astype(str) == str(item.code)]
                if rec.empty:
                    st.warning(f"Codice non trovato in listino: {item.code} ({item.name})")
                    continue
                prodotto_row = rec.iloc[0]

                unit_raw = float(prodotto_row["Prezzo di listino"])
                if mostra_netto:
                    for sconto in sconti:
                        unit_raw *= (1 - sconto / 100)

                row_total = unit_raw * item.qty
                totale_configurazione += row_total

                vis_full = {
                    "Codice": str(prodotto_row["Codice"]),
                    "Prodotto": str(prodotto_row["Prodotto"]),
                    "Quantità": int(item.qty),
                    "Prezzo unitario": f"{unit_raw:,.2f} €",
                    "Prezzo totale": f"{row_total:,.2f} €",
                    "UnitPriceRaw": float(unit_raw),
                    "Descrizione": str(prodotto_row["Descrizione"]),
                }
                righe_tabella_internal.append(vis_full)
                righe_tabella.append({k: vis_full[k] for k in ["Codice","Prodotto","Quantità","Prezzo unitario","Prezzo totale"]})
        except Exception as e:
            st.error(f"Configuratore MK: {e}")

    # ======= Parte 3: DISTINTA dal CONFIGURATORE SOLARE (logica invariata) =======
    if cfg_input_sol is not None:
        try:
            distinta_sol = genera_distinta_solare(cfg_input_sol)   # List[LineItem]
            for item in distinta_sol:
                rec = df[df["Codice"].astype(str) == str(item.code)]
                if rec.empty:
                    st.warning(f"Codice non trovato in listino (solare): {item.code} ({item.name})")
                    continue
                prodotto_row = rec.iloc[0]

                unit_raw = float(prodotto_row["Prezzo di listino"])
                if mostra_netto:
                    for sconto in sconti:
                        unit_raw *= (1 - sconto / 100)

                row_total = unit_raw * item.qty
                totale_configurazione += row_total

                vis_full = {
                    "Codice": str(prodotto_row["Codice"]),
                    "Prodotto": str(prodotto_row["Prodotto"]),
                    "Quantità": int(item.qty),
                    "Prezzo unitario": f"{unit_raw:,.2f} €",
                    "Prezzo totale": f"{row_total:,.2f} €",
                    "UnitPriceRaw": float(unit_raw),
                    "Descrizione": str(prodotto_row["Descrizione"]),
                }
                righe_tabella_internal.append(vis_full)
                righe_tabella.append({k: vis_full[k] for k in ["Codice","Prodotto","Quantità","Prezzo unitario","Prezzo totale"]})
        except Exception as e:
            st.error(f"Configuratore solare: {e}")

    # ======= Persistenza + Render Tabella / Azioni =======
    df_full = pd.DataFrame(righe_tabella_internal)  # include colonne tecniche
    # Salva stato
    st.session_state["output_rows"] = righe_tabella  # solo colonne visibili
    st.session_state["output_rows_internal"] = righe_tabella_internal
    st.session_state["totale_conf"] = float(totale_configurazione)
    st.session_state["df_current_full"] = df_full.copy()
    st.session_state["df_original_qty"] = df_full["Quantità"].tolist()
    st.session_state["rendered_this_run"] = True
    # Mostra tabella + azioni (primo elemento negli output)
    show_summary_table_and_actions(df_full, totale_configurazione)

# -------------------------------------------------------
# RENDER persistente (per far funzionare azioni post-rerun)
# -------------------------------------------------------
if st.session_state.get("output_rows_internal") and not st.session_state.get("rendered_this_run"):
    df_full = pd.DataFrame(st.session_state["output_rows_internal"])
    show_summary_table_and_actions(
        df_full,
        st.session_state.get("totale_conf", 0.0)
    )
