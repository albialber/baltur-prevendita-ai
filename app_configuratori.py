import streamlit as st
import pickle
import pandas as pd
import numpy as np

from rules_configuratore_mk import (
    ConfigInput as ConfigInputMK,
    genera_distinta as genera_distinta_mk,
    BOILERS_POT,
)
from rules_configuratore_solare import ConfigSolareInput, genera_distinta_solare

# -------------------------------------------------------
# Impostazioni pagina
# -------------------------------------------------------
st.set_page_config(page_title="Baltur CONFIGURATORI", layout="centered")

# Stili: bottone primario rosso + tabelle markdown con stesso layout (larghezze fisse, niente a capo)
st.markdown(
    """
<style>
/* Bottone primario (solo quello che imposteremo come type="primary") */
div.stButton > button[kind="primary"]{
  background-color:#d11a2a !important;
  color:#ffffff !important;
  border-color:#d11a2a !important;
}
div.stButton > button[kind="primary"]:hover{
  background-color:#b21220 !important;
  border-color:#b21220 !important;
}

/* Tabelle Markdown uniformi (output e post-ricalcolo) */
section.main table{
  width:100%;
  table-layout:fixed;
  border-collapse:collapse;
}
section.main table th, section.main table td{
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
  padding:0.35rem 0.6rem;
}
/* Larghezze coerenti tra tutte le tabelle (regola per colonna) */
section.main table th:nth-child(1), section.main table td:nth-child(1){ width:12ch; }  /* Codice */
section.main table th:nth-child(2), section.main table td:nth-child(2){ width:28ch; }  /* Prodotto */
section.main table th:nth-child(3), section.main table td:nth-child(3){ width:9ch; }   /* Quantità */
section.main table th:nth-child(4), section.main table td:nth-child(4){ width:16ch; }  /* Prezzo unitario */
section.main table th:nth-child(5), section.main table td:nth-child(5){ width:16ch; }  /* Prezzo totale */
</style>
""",
    unsafe_allow_html=True,
)

# Logo grande centrato da file locale
st.image("baltur_logo.png", width=300)

# Titolo senza emoticon
st.title("Baltur Configuratori")

# -------------------------------------------------------
# Stato applicazione
# -------------------------------------------------------
if "output_rows" not in st.session_state:
    st.session_state["output_rows"] = []
if "totale_conf" not in st.session_state:
    st.session_state["totale_conf"] = 0.0

# flag per evitare doppia stampa nella stessa esecuzione
st.session_state["rendered_this_run"] = False

# visibilità configuratore solare
st.session_state.setdefault("show_solar", False)

# stati UI riepilogo
st.session_state.setdefault("details_open", False)
st.session_state.setdefault("qty_edit_mode", False)
st.session_state.setdefault("qty_edit_values", [])
st.session_state.setdefault("descrizioni_map", {})
st.session_state.setdefault("unit_price_map", {})
st.session_state.setdefault("prodotto_map", {})

# stato logiche INAIL e recap configurazione MK
st.session_state.setdefault("inail_esclusa", False)
st.session_state.setdefault("mk_recap_text", "")

# -------------------------------------------------------
# Controllo prezzi: listino / netti
# -------------------------------------------------------
mostra_netto = st.checkbox("Mostra prezzi netti invece del listino")

if mostra_netto:
    sconti = [
        st.number_input(f"Sconto {i+1}", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        for i in range(4)
    ]
else:
    sconti = []

# Etichette colonne e totale in base a listino/netto
if mostra_netto:
    current_col_pu = "Prezzo unitario (netto)"
    current_col_pt = "Prezzo totale (netto)"
    current_total_label = "Totale netto configurazione"
else:
    current_col_pu = "Prezzo unitario (listino)"
    current_col_pt = "Prezzo totale (listino)"
    current_total_label = "Totale listino configurazione"

# Valori di default presi da sessione per mantenere coerenza tra i rerun
col_pu = st.session_state.get("col_pu", current_col_pu)
col_pt = st.session_state.get("col_pt", current_col_pt)
total_label = st.session_state.get("total_label", current_total_label)

VISIBLE_COLS = ["Codice", "Prodotto", "Quantità", col_pu, col_pt]

# -------------------------------------------------------
# CONFIGURATORE SMILE ENERGY MK
# -------------------------------------------------------
st.markdown("---")
st.subheader("🧩 Configuratore SMILE ENERGY MK")

macro_label_to_value = {
    "Cascata interno - in linea": "INT_LINEA",
    "Cascata interno - ad isola": "INT_ISOLA",
    "Cascata esterno": "ESTERNO",
    "Singola interno": "SINGOLO_INT",
    "Singola esterno": "SINGOLO_EST",
}
macro_label = st.selectbox(
    "Seleziona configurazione",
    list(macro_label_to_value.keys()),
    index=0,
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
        index=0,
    )
    separatore_value = sep_label_to_value[separatore_label]

    sottoopzione = None
    ssb_code = None
    sii_code = None

    if separatore_value in ("SSB", "EQUILIBRATORE"):
        sottoopzione = st.radio(
            "Sotto-opzione",
            ["KIT_TUBI", "KIT_TUBI_CIRC", "NESSUNA"],
            index=0,
            horizontal=True,
        )

    if separatore_value == "SSB":
        ssb_code = st.text_input("Codice scambiatore SSB (opzionale)", value="") or None
    if separatore_value == "SII_PRO":
        sii_code = st.text_input("Codice scambiatore SII PRO (opzionale)", value="") or None

    centralina = st.selectbox(
        "Centralina", ["ALPHA", "THETA", "OMEGA", "MODBUS", "0-10V"], index=0
    )

    cfg_input_mk = ConfigInputMK(
        macro=macro_value,
        caldaie=caldaie_sel,
        separatore=separatore_value,
        sottoopzione=sottoopzione,
        ssb_code=ssb_code,
        sii_code=sii_code,
        centralina=centralina,
    )

    # Salva in sessione per il recap testuale
    st.session_state["mk_macro_label"] = macro_label
    st.session_state["mk_caldaie_sel"] = caldaie_sel
    st.session_state["mk_separatore_label"] = separatore_label
    st.session_state["mk_sottoopzione"] = sottoopzione or "Nessuna"
    st.session_state["mk_centralina"] = centralina

elif macro_value in ("SINGOLO_INT", "SINGOLO_EST"):
    st.caption("Configurazione singola")
    modello = st.selectbox(
        "Modello", ["MK 50", "MK 70", "MK 90", "MK 115", "MK 160SP", "MK 160"], index=0
    )
    sottocat = st.radio("Sottocategoria", ["SSB", "EQUILIBRATORE"], index=0, horizontal=True)

    cfg_input_mk = ConfigInputMK(
        macro=macro_value,
        singola_modello=modello,
        singola_sottocat=sottocat,
    )

    # Recap per singola
    full_name = f"SMILE ENERGY {modello}"
    st.session_state["mk_macro_label"] = macro_label
    st.session_state["mk_caldaie_sel"] = {full_name: 1}
    if sottocat == "SSB":
        st.session_state["mk_separatore_label"] = "SCAMBIATORE SALDOBRASATO SSB"
    else:
        st.session_state["mk_separatore_label"] = "EQUILIBRATORE DI PORTATA"
    st.session_state["mk_sottoopzione"] = "Nessuna"
    st.session_state["mk_centralina"] = "Nessuna"

# -------------------------------------------------------
# CONFIGURATORE SOLARE TERMICO
# -------------------------------------------------------
st.markdown("---")
st.subheader("☀️ Configuratore solare termico")

if st.button("Apri configuratore solare termico"):
    st.session_state["show_solar"] = True

cfg_input_sol = None
if st.session_state["show_solar"]:
    tetto_map = {
        "Tetto inclinato a coppi": "INCLINATO_COPPI",
        "Tetto piano": "PIANO",
    }
    tetto_label = st.selectbox("Tipologia di tetto", list(tetto_map.keys()), index=0)
    tetto_val = tetto_map[tetto_label]

    pannello_map = {"ETASUN 25": "ETASUN25", "ETASUN 20": "ETASUN20"}
    pannello_label = st.selectbox("Tipologia di pannello", list(pannello_map.keys()), index=0)
    pannello_val = pannello_map[pannello_label]

    n_pannelli = st.number_input("Numero pannelli", min_value=1, step=1, value=1)
    n_file = st.number_input("Numero file", min_value=1, step=1, value=1)

    centr_label = st.selectbox("Tipo di centralina", ["SBMTDC_V5", "SBLTDC_V3"], index=0)
    centr_val = "SBMTDC_V5" if centr_label == "SBMTDC_V5" else "SBLTDC_V3"

    # Calcolo volume consigliato (area_totale * 60)
    area = 2.35 if pannello_val == "ETASUN25" else 1.87
    superficie_tot = area * n_pannelli
    volume_consigliato = superficie_tot * 60
    st.info(
        f"Superficie totale: **{superficie_tot:.2f} m²**  •  "
        f"Volume minimo consigliato: **{volume_consigliato:.0f} L**"
    )

    cfg_input_sol = ConfigSolareInput(
        tetto=tetto_val,
        pannello=pannello_val,
        n_pannelli=int(n_pannelli),
        n_file=int(n_file),
        centralina=centr_val,
    )

# -------------------------------------------------------
# Helpers tabella Markdown
# -------------------------------------------------------
def _escape_md(text: str) -> str:
    if text is None:
        return ""
    return str(text).replace("|", "\\|" )


def rows_to_markdown_table(rows: list[dict]) -> str:
    headers = VISIBLE_COLS
    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for r in rows:
        cells = [
            _escape_md(r.get("Codice", "")),
            _escape_md(r.get("Prodotto", "")),
            str(int(r.get("Quantità", 0))),
            _escape_md(r.get(col_pu, "")),
            _escape_md(r.get(col_pt, "")),
        ]
        md += "| " + " | ".join(cells) + " |\n"
    return md

# -------------------------------------------------------
# Utils: sconti + riepilogo + azioni sotto tabella
# -------------------------------------------------------
def applica_sconti(prezzo: float, sconti: list[float]) -> float:
    p = float(prezzo)
    for s in sconti:
        p *= 1 - float(s) / 100.0
    return p


def mostra_riepilogo(rows: list[dict], totale: float):
    if not rows:
        return

    st.subheader("📊 Riepilogo preventivo")
    md_table = rows_to_markdown_table(rows)
    st.markdown(md_table)

    # Messaggio INAIL se necessario
    if st.session_state.get("inail_esclusa"):
        st.markdown(
            '<p style="color:red;"><strong>Valvola di sicurezza INAIL esclusa per questa configurazione</strong></p>',
            unsafe_allow_html=True,
        )

    st.markdown(f"**{total_label}:** {totale:,.2f} €")

    # Recap testuale configurazione MK (se presente)
    recap = st.session_state.get("mk_recap_text", "")
    if recap:
        st.markdown(recap)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("📋 Dati per Order Entry"):
            lines = []
            for r in st.session_state["output_rows"]:
                codice = str(r.get("Codice", "")).strip()
                quantita = int(r.get("Quantità", 0))
                lines.append(f"{codice};{quantita}")
            payload = "\n".join(lines)
            st.subheader("Dati per Order Entry")
            st.code(payload, language=None)

    with c2:
        if st.button("✏️ Modifica quantità"):
            st.session_state["qty_edit_mode"] = True
            st.session_state["qty_edit_values"] = [
                int(r.get("Quantità", 0)) for r in st.session_state["output_rows"]
            ]

    with c3:
        if st.button("🔎 Dettagli"):
            st.session_state["details_open"] = not st.session_state["details_open"]

    if st.session_state["details_open"]:
        st.markdown("### Dettagli voci")
        for r in st.session_state["output_rows"]:
            codice = str(r.get("Codice", ""))
            nome = st.session_state["prodotto_map"].get(codice, r.get("Prodotto", ""))
            descr = st.session_state["descrizioni_map"].get(codice, "")
            st.markdown(
                f"**{nome}**  \n"
                f"**Codice:** `{codice}`  \n"
                f"**Quantità:** {int(r.get('Quantità', 0))}  \n"
                f"**Descrizione:** {descr}"
            )

    if st.session_state["qty_edit_mode"]:
        st.markdown("### Modifica quantità")
        new_qty = []
        for i, r in enumerate(st.session_state["output_rows"]):
            codice = str(r.get("Codice", ""))
            nome = r.get("Prodotto", "")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**{nome}**  —  `{codice}`")
            with col2:
                val = st.number_input(
                    "Quantità",
                    min_value=0,
                    step=1,
                    value=int(st.session_state["qty_edit_values"][i]),
                    key=f"qty_input_{i}",
                )
                new_qty.append(int(val))

        st.caption("Quando hai finito, clicca **Ricalcola** per aggiornare i totali.")

        c_ok, c_cancel = st.columns([1, 1])
        with c_ok:
            if st.button("♻️ Ricalcola"):
                updated_rows = []
                new_total = 0.0
                for i, r in enumerate(st.session_state["output_rows"]):
                    codice = str(r.get("Codice", ""))
                    unit_raw = float(st.session_state["unit_price_map"].get(codice, 0.0))
                    q = int(new_qty[i])
                    row_total = unit_raw * q
                    updated_rows.append(
                        {
                            "Codice": codice,
                            "Prodotto": r.get("Prodotto", ""),
                            "Quantità": q,
                            col_pu: f"{unit_raw:,.2f} €",
                            col_pt: f"{row_total:,.2f} €",
                        }
                    )
                    new_total += row_total

                st.session_state["output_rows"] = updated_rows
                st.session_state["totale_conf"] = float(new_total)
                st.session_state["qty_edit_mode"] = False

                st.success(f"Ricalcolo completato. Nuovo totale: {new_total:,.2f} €")
                st.markdown("### Riepilogo aggiornato")
                st.markdown(rows_to_markdown_table(st.session_state["output_rows"]))
                st.markdown(f"**{total_label}:** {st.session_state['totale_conf']:,.2f} €")

        with c_cancel:
            if st.button("Annulla modifiche"):
                st.session_state["qty_edit_mode"] = False
                st.session_state["qty_edit_values"] = []

# -------------------------------------------------------
# GENERA PREVENTIVO
# -------------------------------------------------------
if st.button("Genera preventivo", type="primary"):
    # Aggiorna etichette colonne con lo stato corrente (listino/netto)
    col_pu = current_col_pu
    col_pt = current_col_pt
    total_label = current_total_label

    # Reset flag per questa esecuzione
    st.session_state["rendered_this_run"] = True
    st.session_state["inail_esclusa"] = False
    st.session_state["mk_recap_text"] = ""

    # Carica listino da embeddings.pkl
    with open("embeddings.pkl", "rb") as f:
        data = pickle.load(f)
    df = data["df"]

    righe_tabella = []
    totale_configurazione = 0.0

    # Reset mappe per dettagli e ricalcolo
    st.session_state["descrizioni_map"] = {}
    st.session_state["unit_price_map"] = {}
    st.session_state["prodotto_map"] = {}

    # -----------------------
    # Parte 1: DISTINTA MK
    # -----------------------
    # Calcola potenza totale MK per la logica INAIL (solo se configuratore MK usato)
    potenza_tot_mk = 0
    if cfg_input_mk is not None and hasattr(cfg_input_mk, "macro"):
        if cfg_input_mk.macro in ("INT_LINEA", "INT_ISOLA", "ESTERNO"):
            cald_dict = getattr(cfg_input_mk, "caldaie", {}) or {}
            for nome, qty in cald_dict.items():
                potenza_tot_mk += BOILERS_POT.get(nome, 0) * int(qty)

    inail_esclusa = potenza_tot_mk > 512

    if cfg_input_mk is not None:
        try:
            distinta_mk = genera_distinta_mk(cfg_input_mk)
            for item in distinta_mk:
                rec = df[df["Codice"].astype(str) == str(item.code)]
                if rec.empty:
                    st.warning(f"Codice non trovato in listino: {item.code} ({item.name})")
                    continue
                prodotto_row = rec.iloc[0]

                prezzo_unitario = float(prodotto_row["Prezzo di listino"])
                if mostra_netto:
                    prezzo_unitario = applica_sconti(prezzo_unitario, sconti)

                prezzo_totale = prezzo_unitario * item.qty
                totale_configurazione += prezzo_totale

                codice = str(prodotto_row["Codice"])
                st.session_state["descrizioni_map"][codice] = str(prodotto_row["Descrizione"])
                st.session_state["unit_price_map"][codice] = float(prezzo_unitario)
                st.session_state["prodotto_map"][codice] = str(prodotto_row["Prodotto"])

                righe_tabella.append(
                    {
                        "Codice": prodotto_row["Codice"],
                        "Prodotto": prodotto_row["Prodotto"],
                        "Quantità": item.qty,
                        col_pu: f"{prezzo_unitario:,.2f} €",
                        col_pt: f"{prezzo_totale:,.2f} €",
                    }
                )
        except Exception as e:
            st.error(f"Configuratore MK: {e}")

    # -----------------------
    # Parte 2: DISTINTA SOLARE
    # -----------------------
    if cfg_input_sol is not None:
        try:
            distinta_sol = genera_distinta_solare(cfg_input_sol)
            for item in distinta_sol:
                rec = df[df["Codice"].astype(str) == str(item.code)]
                if rec.empty:
                    st.warning(f"Codice non trovato in listino (solare): {item.code} ({item.name})")
                    continue
                prodotto_row = rec.iloc[0]

                prezzo_unitario = float(prodotto_row["Prezzo di listino"])
                if mostra_netto:
                    prezzo_unitario = applica_sconti(prezzo_unitario, sconti)

                prezzo_totale = prezzo_unitario * item.qty
                totale_configurazione += prezzo_totale

                codice = str(prodotto_row["Codice"])
                st.session_state["descrizioni_map"][codice] = str(prodotto_row["Descrizione"])
                st.session_state["unit_price_map"][codice] = float(prezzo_unitario)
                st.session_state["prodotto_map"][codice] = str(prodotto_row["Prodotto"])

                righe_tabella.append(
                    {
                        "Codice": prodotto_row["Codice"],
                        "Prodotto": prodotto_row["Prodotto"],
                        "Quantità": item.qty,
                        col_pu: f"{prezzo_unitario:,.2f} €",
                        col_pt: f"{prezzo_totale:,.2f} €",
                    }
                )
        except Exception as e:
            st.error(f"Configuratore solare: {e}")

    # Salva stato riepilogo
    st.session_state["output_rows"] = righe_tabella
    st.session_state["totale_conf"] = float(totale_configurazione)
    st.session_state["qty_edit_mode"] = False
    st.session_state["qty_edit_values"] = [int(r["Quantità"]) for r in righe_tabella]
    st.session_state["inail_esclusa"] = inail_esclusa

    # Salva etichette colonne e totale per i rerun successivi
    st.session_state["col_pu"] = col_pu
    st.session_state["col_pt"] = col_pt
    st.session_state["total_label"] = total_label

    # Costruisci testo recap configurazione MK (se presente)
    mk_macro_label = st.session_state.get("mk_macro_label")
    mk_caldaie_sel = st.session_state.get("mk_caldaie_sel", {})
    mk_separatore_label = st.session_state.get("mk_separatore_label", "Nessuna")
    mk_sottoopzione = st.session_state.get("mk_sottoopzione", "Nessuna")
    mk_centralina = st.session_state.get("mk_centralina", "Nessuna")

    recap_lines = []
    if mk_macro_label:
        recap_lines.append(f"Configurazione: {mk_macro_label}")

        # Layout caldaie
        layout_items = []
        for full_name, qty in mk_caldaie_sel.items():
            if qty <= 0:
                continue
            # Da "SMILE ENERGY MK 115" -> "MK 115"
            short = full_name.replace("SMILE ENERGY ", "").strip()
            layout_items.extend([short] * int(qty))
        layout_str = " + ".join(layout_items) if layout_items else "-"
        recap_lines.append(f"Layout caldaie: {layout_str}")

        recap_lines.append(f"Separatore idraulico: {mk_separatore_label}")
        recap_lines.append(f"Anello primario: {mk_sottoopzione}")
        recap_lines.append(f"Centralina: {mk_centralina}")

    st.session_state["mk_recap_text"] = "\n".join(recap_lines)

    # Mostra riepilogo per questa esecuzione
    mostra_riepilogo(righe_tabella, totale_configurazione)

# -------------------------------------------------------
# RENDER persistente (per Order Entry / Dettagli dopo il rerun)
# -------------------------------------------------------
if st.session_state.get("output_rows") and not st.session_state.get("rendered_this_run"):
    mostra_riepilogo(st.session_state["output_rows"], st.session_state["totale_conf"])

