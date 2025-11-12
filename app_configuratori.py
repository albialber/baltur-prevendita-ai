import streamlit as st
import pickle
import pandas as pd
from typing import List, Dict

from rules_configuratore_mk import ConfigInput as ConfigInputMK, genera_distinta as genera_distinta_mk
from rules_configuratore_solare import ConfigSolareInput, genera_distinta_solare
from utils_catalogo import get_catalog_df, prezzo_con_sconti, rows_to_markdown_table

st.set_page_config(page_title="Baltur Configuratori", layout="centered")

# --- Stili grafici Baltur ---
st.markdown(
    """
    <style>
    div.stButton > button[kind="primary"]{
        background-color:#d11a2a;
        color:#fff;
        border-color:#d11a2a
    }
    div.stButton > button[kind="primary"]:hover{
        background-color:#b21220;
        border-color:#b21220
    }
    section.main table{
        width:100%;
        table-layout:fixed;
        border-collapse:collapse
    }
    section.main table th, section.main table td{
        white-space:nowrap;
        overflow:hidden;
        text-overflow:ellipsis;
        padding:0.35rem 0.6rem
    }
    section.main table th:nth-child(1), section.main table td:nth-child(1){width:12ch}
    section.main table th:nth-child(2), section.main table td:nth-child(2){width:28ch}
    section.main table th:nth-child(3), section.main table td:nth-child(3){width:9ch}
    section.main table th:nth-child(4), section.main table td:nth-child(4){width:16ch}
    section.main table th:nth-child(5), section.main table td:nth-child(5){width:16ch}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
st.image("baltur_logo.png", width=300)
st.title("Baltur Configuratori")

# --- Stato UI ---
st.session_state.setdefault("output_rows", [])
st.session_state.setdefault("totale_conf", 0.0)
st.session_state.setdefault("details_open", False)
st.session_state.setdefault("qty_edit_mode", False)
st.session_state.setdefault("qty_edit_values", [])
st.session_state.setdefault("descrizioni_map", {})
st.session_state.setdefault("unit_price_map", {})
st.session_state.setdefault("prodotto_map", {})

# --- Prezzi netti o di listino ---
mostra_netto = st.checkbox("Mostra prezzi netti invece del listino")
if mostra_netto:
    sconti = [st.number_input(f"Sconto {i+1}", 0.0, 100.0, 0.0, 0.5) for i in range(4)]
else:
    sconti = []

st.markdown("---")
st.subheader("🧩 Configuratore SMILE ENERGY MK")

# --- Selettori MK ---
macro_label_to_value = {
    "Cascata interno - in linea": "INT_LINEA",
    "Cascata interno - ad isola": "INT_ISOLA",
    "Cascata esterno": "ESTERNO",
    "Singola interno": "SINGOLO_INT",
    "Singola esterno": "SINGOLO_EST",
}
macro_label = st.selectbox("Seleziona configurazione", list(macro_label_to_value.keys()))
macro_value = macro_label_to_value[macro_label]

cfg_input_mk = None

if macro_value in ("INT_LINEA", "INT_ISOLA", "ESTERNO"):
    st.caption("Seleziona quantità (totale 2–4 caldaie, anche modelli diversi).")
    c1, c2, c3 = st.columns(3)
    with c1:
        mk50 = st.number_input("SMILE ENERGY MK 50", 0, 4, 0)
        mk70 = st.number_input("SMILE ENERGY MK 70", 0, 4, 0)
    with c2:
        mk90 = st.number_input("SMILE ENERGY MK 90", 0, 4, 0)
        mk115 = st.number_input("SMILE ENERGY MK 115", 0, 4, 0)
    with c3:
        mk160sp = st.number_input("SMILE ENERGY MK 160SP", 0, 4, 0)
        mk160 = st.number_input("SMILE ENERGY MK 160", 0, 4, 0)

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

    sep_options = {
        "NESSUNA": "NESSUNA",
        "SCAMBIATORE SALDOBRASATO SSB": "SSB",
        "SCAMBIATORE ISPEZIONABILE SII PRO": "SII_PRO",
        "EQUILIBRATORE DI PORTATA": "EQUILIBRATORE",
    }
    separatore_label = st.selectbox("Seleziona separatore idraulico", list(sep_options.keys()))
    separatore_value = sep_options[separatore_label]

    sottoopzione = None
    ssb_code = None
    sii_code = None

    if separatore_value in ("SSB", "EQUILIBRATORE"):
        sottoopzione = st.radio("Sotto-opzione", ["KIT_TUBI", "KIT_TUBI_CIRC", "NESSUNA"], index=0, horizontal=True)

    if separatore_value == "SSB":
        ssb_code = st.text_input("Codice scambiatore SSB (opzionale)") or None
    if separatore_value == "SII_PRO":
        sii_code = st.text_input("Codice scambiatore SII PRO (opzionale)") or None

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
    modello = st.selectbox("Modello", ["MK 50", "MK 70", "MK 90", "MK 115", "MK 160SP", "MK 160"], index=0)
    sottocat = st.radio("Sottocategoria", ["SSB", "EQUILIBRATORE"], index=0, horizontal=True)
    cfg_input_mk = ConfigInputMK(macro=macro_value, singola_modello=modello, singola_sottocat=sottocat)

st.markdown("---")
st.subheader("☀️ Configuratore solare termico")

if "show_solar" not in st.session_state:
    st.session_state["show_solar"] = False
if st.button("Apri configuratore solare termico"):
    st.session_state["show_solar"] = True

cfg_input_sol = None
if st.session_state["show_solar"]:
    tetto_map = {"Tetto inclinato a coppi": "INCLINATO_COPPI", "Tetto piano": "PIANO"}
    tetto_val = tetto_map[st.selectbox("Tipologia di tetto", list(tetto_map.keys()), index=0)]

    pannello_map = {"ETASUN 25": "ETASUN25", "ETASUN 20": "ETASUN20"}
    pannello_val = pannello_map[st.selectbox("Tipologia di pannello", list(pannello_map.keys()), index=0)]

    n_pannelli = int(st.number_input("Numero pannelli", 1, step=1, value=1))
    n_file = int(st.number_input("Numero file", 1, step=1, value=1))

    centr_label = st.selectbox("Tipo di centralina", ["SBMTDC_V5", "SBLTDC_V3"], index=0)
    centr_val = "SBMTDC_V5" if centr_label == "SBMTDC_V5" else "SBLTDC_V3"

    area = 2.35 if pannello_val == "ETASUN25" else 1.87
    superficie_tot = area * n_pannelli
    volume_consigliato = superficie_tot * 60
    st.info(f"Superficie totale: **{superficie_tot:.2f} m²**  •  Volume minimo consigliato: **{volume_consigliato:.0f} L**")

    cfg_input_sol = ConfigSolareInput(
        tetto=tetto_val,
        pannello=pannello_val,
        n_pannelli=n_pannelli,
        n_file=n_file,
        centralina=centr_val,
    )

VISIBLE_COLS = ["Codice", "Prodotto", "Quantità", "Prezzo unitario", "Prezzo totale"]

# --- Azione principale ---
if st.button("Genera preventivo", type="primary"):
    df = get_catalog_df()
    righe: List[Dict] = []
    totale = 0.0

    st.session_state["descrizioni_map"] = {}
    st.session_state["unit_price_map"] = {}
    st.session_state["prodotto_map"] = {}

    def add_line(codice: str, qty: int) -> float:
        """
        Aggiunge una riga in output e restituisce il totale riga per sommarlo a 'totale'.
        """
        rec = df[df["Codice"].astype(str) == str(codice)]
        if rec.empty:
            st.warning(f"Codice non trovato in listino: {codice}")
            return 0.0
        row = rec.iloc[0]
        price = float(row["Prezzo di listino"]) if "Prezzo di listino" in row else 0.0
        price_net = prezzo_con_sconti(price, sconti) if mostra_netto else price
        row_total = price_net * qty
        st.session_state["descrizioni_map"][str(codice)] = str(row.get("Descrizione", ""))
        st.session_state["unit_price_map"][str(codice)] = float(price_net)
        st.session_state["prodotto_map"][str(codice)] = str(row.get("Prodotto", ""))
        righe.append({
            "Codice": row.get("Codice", codice),
            "Prodotto": row.get("Prodotto", ""),
            "Quantità": int(qty),
            "Prezzo unitario": f"{price_net:,.2f} €",
            "Prezzo totale": f"{row_total:,.2f} €",
        })
        return float(row_total)

    # --- Distinta MK ---
    if cfg_input_mk is not None:
        try:
            for it in genera_distinta_mk(cfg_input_mk):
                totale += add_line(it.code, it.qty)
        except Exception as e:
            st.error(f"Configuratore MK: {e}")

    # --- Distinta Solare ---
    if cfg_input_sol is not None:
        try:
            for it in genera_distinta_solare(cfg_input_sol):
                totale += add_line(it.code, it.qty)
        except Exception as e:
            st.error(f"Configuratore solare: {e}")

    st.session_state["output_rows"] = righe
    st.session_state["totale_conf"] = float(totale)
    st.session_state["qty_edit_mode"] = False
    st.session_state["qty_edit_values"] = [int(r["Quantità"]) for r in righe]

    st.subheader("📊 Riepilogo preventivo")
    st.markdown(rows_to_markdown_table(righe, VISIBLE_COLS))
    st.markdown(f"**Totale configurazione:** {totale:,.2f} €")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📋 Dati per Order Entry"):
            payload = "\n".join(f"{r['Codice']};{int(r['Quantità'])}" for r in st.session_state["output_rows"])
            st.subheader("Dati per Order Entry")
            st.code(payload)
    with c2:
        if st.button("✏️ Modifica quantità"):
            st.session_state["qty_edit_mode"] = True
            st.session_state["qty_edit_values"] = [int(r.get("Quantità", 0)) for r in st.session_state["output_rows"]]
    with c3:
        if st.button("🔎 Dettagli"):
            st.session_state["details_open"] = not st.session_state.get("details_open", False)

    if st.session_state.get("details_open"):
        st.markdown("### Dettagli voci")
        for r in st.session_state["output_rows"]:
            codice = str(r.get("Codice", ""))
            nome = st.session_state["prodotto_map"].get(codice, r.get("Prodotto", ""))
            descr = st.session_state["descrizioni_map"].get(codice, "")
            st.markdown(f"**{nome}**  \n**Codice:** `{codice}`  \n**Quantità:** {int(r.get('Quantità', 0))}  \n**Descrizione:** {descr}")

    if st.session_state.get("qty_edit_mode"):
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
        c_ok, c_cancel = st.columns([1, 1])
        with c_ok:
            if st.button("♻️ Ricalcola"):
                updated = []
                new_total = 0.0
                for i, r in enumerate(st.session_state["output_rows"]):
                    codice = str(r.get("Codice", ""))
                    unit_raw = float(st.session_state["unit_price_map"].get(codice, 0.0))
                    q = int(new_qty[i])
                    row_total = unit_raw * q
                    updated.append({
                        "Codice": codice,
                        "Prodotto": r.get("Prodotto", ""),
                        "Quantità": q,
                        "Prezzo unitario": f"{unit_raw:,.2f} €",
                        "Prezzo totale": f"{row_total:,.2f} €",
                    })
                    new_total += row_total
                st.session_state["output_rows"] = updated
                st.session_state["totale_conf"] = float(new_total)
                st.session_state["qty_edit_mode"] = False
                st.success(f"Ricalcolo completato. Nuovo totale: {new_total:,.2f} €")
                st.markdown(rows_to_markdown_table(st.session_state["output_rows"], VISIBLE_COLS))
        with c_cancel:
            if st.button("Annulla modifiche"):
                st.session_state["qty_edit_mode"] = False
                st.session_state["qty_edit_values"] = []

# --- Persistenza UI ---
if st.session_state.get("output_rows") and not st.session_state.get("qty_edit_mode"):
    st.markdown(rows_to_markdown_table(st.session_state["output_rows"], VISIBLE_COLS))
    st.markdown(f"**Totale configurazione:** {st.session_state['totale_conf']:,.2f} €")

