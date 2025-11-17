import streamlit as st
import pickle
import pandas as pd
import numpy as np

from rules_configuratore_mk import (
    ConfigInput as ConfigInputMK,
    genera_distinta as genera_distinta_mk,
    BOILERS_POT,
    SSB_MODELS,
    SII_PRO_MODELS,
)
from rules_configuratore_solare import ConfigSolareInput, genera_distinta_solare

# -------------------------------------------------------
# Impostazioni pagina
# -------------------------------------------------------
st.set_page_config(page_title="Baltur CONFIGURATORI", layout="centered")

# Stili
st.markdown(
    """
<style>
div.stButton > button[kind="primary"]{
  background-color:#d11a2a !important;
  color:#ffffff !important;
  border-color:#d11a2a !important;
}
div.stButton > button[kind="primary"]:hover{
  background-color:#b21220 !important;
  border-color:#b21220 !important;
}
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
section.main table th:nth-child(1), section.main table td:nth-child(1){ width:12ch; }
section.main table th:nth-child(2), section.main table td:nth-child(2){ width:28ch; }
section.main table th:nth-child(3), section.main table td:nth-child(3){ width:9ch; }
section.main table th:nth-child(4), section.main table td:nth-child(4){ width:16ch; }
section.main table th:nth-child(5), section.main table td:nth-child(5){ width:16ch; }
</style>
""",
    unsafe_allow_html=True,
)

# Logo + titolo
st.image("baltur_logo.png", width=300)
st.title("Baltur Configuratori")

# -------------------------------------------------------
# Stato applicazione
# -------------------------------------------------------
ss = st.session_state
if "output_rows" not in ss:
    ss["output_rows"] = []
if "totale_conf" not in ss:
    ss["totale_conf"] = 0.0

ss["rendered_this_run"] = False

ss.setdefault("show_mk", False)
ss.setdefault("show_solar", False)

ss.setdefault("details_open", False)
ss.setdefault("qty_edit_mode", False)
ss.setdefault("qty_edit_values", [])
ss.setdefault("descrizioni_map", {})
ss.setdefault("unit_price_map", {})
ss.setdefault("prodotto_map", {})

ss.setdefault("inail_esclusa", False)
ss.setdefault("mk_recap_text", "")
ss.setdefault("mk_macro_label", None)
ss.setdefault("mk_caldaie_sel", {})
ss.setdefault("mk_separatore_label", "")
ss.setdefault("mk_sottoopzione", "")
ss.setdefault("mk_centralina", "")

# -------------------------------------------------------
# Impostazioni prezzi (listino/netto)
# -------------------------------------------------------
mostra_netto = st.checkbox("Mostra prezzi netti invece del listino")

if mostra_netto:
    sconti = [
        st.number_input(f"Sconto {i+1}", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        for i in range(4)
    ]
else:
    sconti = []

if mostra_netto:
    current_col_pu = "Prezzo unitario (netto)"
    current_col_pt = "Prezzo totale (netto)"
    current_total_label = "Totale netto configurazione"
else:
    current_col_pu = "Prezzo unitario (listino)"
    current_col_pt = "Prezzo totale (listino)"
    current_total_label = "Totale listino configurazione"

# Valori usati per la tabella in questo rerun (salvati in sessione)
col_pu = ss.get("col_pu", current_col_pu)
col_pt = ss.get("col_pt", current_col_pt)
total_label = ss.get("total_label", current_total_label)

# -------------------------------------------------------
# CONFIGURATORE MK (con bottone di apertura)
# -------------------------------------------------------
st.markdown("---")
st.subheader("🔥 Configuratore SMILE ENERGY MK")

if st.button("Apri configuratore SMILE ENERGY MK"):
    ss["show_mk"] = True

cfg_input_mk = None

if ss["show_mk"]:
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

        # Scelta scambiatore SSB da elenco (come da versione precedente)
        if separatore_value == "SSB":
            ssb_labels = [name for _, name in SSB_MODELS]
            ssb_sel = st.selectbox(
                "Seleziona scambiatore SSB",
                ["Nessuno"] + ssb_labels,
                index=0,
            )
            if ssb_sel != "Nessuno":
                for code, name in SSB_MODELS:
                    if name == ssb_sel:
                        ssb_code = code
                        break

        # Scelta scambiatore SII PRO da elenco
        if separatore_value == "SII_PRO":
            sii_labels = [name for _, name in SII_PRO_MODELS]
            sii_sel = st.selectbox(
                "Seleziona scambiatore SII PRO",
                ["Nessuno"] + sii_labels,
                index=0,
            )
            if sii_sel != "Nessuno":
                for code, name in SII_PRO_MODELS:
                    if name == sii_sel:
                        sii_code = code
                        break

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

        # Dati per il recap finale
        ss["mk_macro_label"] = macro_label
        ss["mk_caldaie_sel"] = caldaie_sel
        ss["mk_separatore_label"] = separatore_label
        ss["mk_sottoopzione"] = sottoopzione or "Nessuna"
        ss["mk_centralina"] = centralina

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

        full_name = f"SMILE ENERGY {modello}"
        ss["mk_macro_label"] = macro_label
        ss["mk_caldaie_sel"] = {full_name: 1}
        if sottocat == "SSB":
            ss["mk_separatore_label"] = "SCAMBIATORE SALDOBRASATO SSB"
        else:
            ss["mk_separatore_label"] = "EQUILIBRATORE DI PORTATA"
        ss["mk_sottoopzione"] = "Nessuna"
        ss["mk_centralina"] = "Nessuna"

# -------------------------------------------------------
# CONFIGURATORE SOLARE (con bottone di apertura)
# -------------------------------------------------------
st.markdown("---")
st.subheader("☀️ Configuratore solare termico")

if st.button("Apri configuratore solare termico"):
    ss["show_solar"] = True

cfg_input_sol = None
if ss["show_solar"]:
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
# Helper per tabella markdown
# -------------------------------------------------------
def _escape_md(text: str) -> str:
    if text is None:
        return ""
    return str(text).replace("|", "\\|")

def rows_to_markdown_table(rows: list[dict]) -> str:
    """
    Intestazioni ora sempre allineate a col_pu/col_pt correnti,
    così non c'è mismatch tra scelta listino/netto e nomi colonna.
    """
    headers = ["Codice", "Prodotto", "Quantità", col_pu, col_pt]
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
# Utils prezzi / ricerca codice
# -------------------------------------------------------
def applica_sconti(prezzo: float, sconti: list[float]) -> float:
    p = float(prezzo)
    for s in sconti:
        p *= 1 - float(s) / 100.0
    return p

def _normalizza_codice(c: str) -> str:
    s = str(c).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s.lstrip("0") or "0"

def trova_prodotto_da_codice(df: pd.DataFrame, code: str):
    s_code = str(code).strip()
    mask = df["Codice"].astype(str) == s_code
    if mask.any():
        return df[mask].iloc[0]
    target = _normalizza_codice(s_code)
    mask2 = df["Codice"].apply(lambda x: _normalizza_codice(x) == target)
    if mask2.any():
        return df[mask2].iloc[0]
    return None

# -------------------------------------------------------
# Riepilogo + Order Entry + Dettagli + Modifica quantità
# -------------------------------------------------------
def mostra_riepilogo(rows: list[dict], totale: float):
    if not rows:
        return

    st.subheader("📊 Riepilogo preventivo")
    md_table = rows_to_markdown_table(rows)
    st.markdown(md_table)

    if ss.get("inail_esclusa"):
        st.markdown(
            '<p style="color:red;"><strong>Valvola di sicurezza INAIL esclusa per questa configurazione</strong></p>',
            unsafe_allow_html=True,
        )

    st.markdown(f"**{total_label}:** {totale:,.2f} €")

    # Recap finale in verticale (una voce per riga)
    recap = ss.get("mk_recap_text", "")
    if recap:
        st.markdown(recap)

    c1, c2, c3 = st.columns(3)

    # Dati per Order Entry
    with c1:
        if st.button("📋 Dati per Order Entry"):
            lines = []
            for r in ss["output_rows"]:
                codice = str(r.get("Codice", "")).strip()
                quantita = int(r.get("Quantità", 0))
                lines.append(f"{codice};{quantita}")
            payload = "\n".join(lines)
            st.subheader("Dati per Order Entry")
            st.code(payload, language=None)

    # Modifica quantità
    with c2:
        if st.button("✏️ Modifica quantità"):
            ss["qty_edit_mode"] = True
            ss["qty_edit_values"] = [
                int(r.get("Quantità", 0)) for r in ss["output_rows"]
            ]

    # Dettagli
    with c3:
        if st.button("🔎 Dettagli"):
            ss["details_open"] = not ss["details_open"]

    # Sezione dettagli
    if ss["details_open"]:
        st.markdown("### Dettagli voci")
        for r in ss["output_rows"]:
            codice = str(r.get("Codice", ""))
            nome = ss["prodotto_map"].get(codice, r.get("Prodotto", ""))
            descr = ss["descrizioni_map"].get(codice, "")
            st.markdown(
                f"**{nome}**  \n"
                f"**Codice:** `{codice}`  \n"
                f"**Quantità:** {int(r.get('Quantità', 0))}  \n"
                f"**Descrizione:** {descr}"
            )

    # Sezione modifica quantità
    if ss["qty_edit_mode"]:
        st.markdown("### Modifica quantità")
        new_qty = []
        for i, r in enumerate(ss["output_rows"]):
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
                    value=int(ss["qty_edit_values"][i]),
                    key=f"qty_input_{i}",
                )
                new_qty.append(int(val))

        st.caption("Quando hai finito, clicca **Ricalcola** per aggiornare i totali.")

        c_ok, c_cancel = st.columns([1, 1])
        with c_ok:
            if st.button("♻️ Ricalcola"):
                updated_rows = []
                new_total = 0.0
                for i, r in enumerate(ss["output_rows"]):
                    codice = str(r.get("Codice", ""))
                    unit_raw = float(ss["unit_price_map"].get(codice, 0.0))
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

                ss["output_rows"] = updated_rows
                ss["totale_conf"] = new_total
                ss["qty_edit_mode"] = False

                st.success(f"Ricalcolo completato. Nuovo totale: {new_total:,.2f} €")
                st.markdown("### Riepilogo aggiornato")
                st.markdown(rows_to_markdown_table(ss["output_rows"]))
                st.markdown(f"**{total_label}:** {ss['totale_conf']:,.2f} €")

        with c_cancel:
            if st.button("Annulla modifiche"):
                ss["qty_edit_mode"] = False
                ss["qty_edit_values"] = []

# -------------------------------------------------------
# GENERAZIONE PREVENTIVO
# -------------------------------------------------------
if st.button("Genera preventivo", type="primary"):
    # In questo run usiamo sempre i nomi coerenti alla scelta attuale
    col_pu = current_col_pu
    col_pt = current_col_pt
    total_label = current_total_label

    ss["rendered_this_run"] = True
    ss["inail_esclusa"] = False
    ss["mk_recap_text"] = ""

    # Blocco configurazione 4x MK160 (non omologata INAIL)
    invalid_mk_config = False
    if cfg_input_mk is not None and hasattr(cfg_input_mk, "macro"):
        if cfg_input_mk.macro in ("INT_LINEA", "INT_ISOLA", "ESTERNO"):
            cald_dict = getattr(cfg_input_mk, "caldaie", {}) or {}
            mk160_qty = int(cald_dict.get("SMILE ENERGY MK 160", 0))
            tot_qty = sum(int(v) for v in cald_dict.values())
            if mk160_qty == 4 and tot_qty == 4:
                invalid_mk_config = True

    if invalid_mk_config:
        ss["output_rows"] = []
        ss["totale_conf"] = 0.0
        ss["details_open"] = False
        ss["qty_edit_mode"] = False
        ss["qty_edit_values"] = []
        st.markdown(
            '<p style="color:red;"><strong>Configurazione non omologata INAIL, selezionare un\'altra combinazione di generatori</strong></p>',
            unsafe_allow_html=True,
        )
    else:
        # Carico listino da embeddings.pkl
        with open("embeddings.pkl", "rb") as f:
            data = pickle.load(f)
        df = data["df"]

        righe_tabella: list[dict] = []
        totale_configurazione = 0.0

        ss["descrizioni_map"] = {}
        ss["unit_price_map"] = {}
        ss["prodotto_map"] = {}

        # Calcolo potenza totale MK per eventuale esclusione INAIL
        potenza_tot_mk = 0
        if cfg_input_mk is not None and hasattr(cfg_input_mk, "macro"):
            if cfg_input_mk.macro in ("INT_LINEA", "INT_ISOLA", "ESTERNO"):
                cald_dict = getattr(cfg_input_mk, "caldaie", {}) or {}
                for nome, qty in cald_dict.items():
                    potenza_tot_mk += BOILERS_POT.get(nome, 0) * int(qty)

        inail_esclusa = potenza_tot_mk > 512

        # ---- Distinta MK ----
        if cfg_input_mk is not None:
            try:
                distinta_mk = genera_distinta_mk(cfg_input_mk)
                for item in distinta_mk:
                    prodotto_row = trova_prodotto_da_codice(df, item.code)
                    if prodotto_row is None:
                        st.warning(f"Codice non trovato in listino: {item.code} ({item.name})")
                        continue

                    prezzo_unitario = float(prodotto_row["Prezzo di listino"])
                    if mostra_netto:
                        prezzo_unitario = applica_sconti(prezzo_unitario, sconti)

                    prezzo_totale = prezzo_unitario * item.qty
                    totale_configurazione += prezzo_totale

                    codice = str(prodotto_row["Codice"]).strip()
                    ss["descrizioni_map"][codice] = str(prodotto_row["Descrizione"])
                    ss["unit_price_map"][codice] = float(prezzo_unitario)
                    ss["prodotto_map"][codice] = str(prodotto_row["Prodotto"])

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

        # ---- Distinta solare ----
        if cfg_input_sol is not None:
            try:
                distinta_sol = genera_distinta_solare(cfg_input_sol)
                for item in distinta_sol:
                    prodotto_row = trova_prodotto_da_codice(df, item.code)
                    if prodotto_row is None:
                        st.warning(f"Codice non trovato in listino (solare): {item.code} ({item.name})")
                        continue

                    prezzo_unitario = float(prodotto_row["Prezzo di listino"])
                    if mostra_netto:
                        prezzo_unitario = applica_sconti(prezzo_unitario, sconti)

                    prezzo_totale = prezzo_unitario * item.qty
                    totale_configurazione += prezzo_totale

                    codice = str(prodotto_row["Codice"]).strip()
                    ss["descrizioni_map"][codice] = str(prodotto_row["Descrizione"])
                    ss["unit_price_map"][codice] = float(prezzo_unitario)
                    ss["prodotto_map"][codice] = str(prodotto_row["Prodotto"])

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

        # Salvataggio stato finale
        ss["output_rows"] = righe_tabella
        ss["totale_conf"] = float(totale_configurazione)
        ss["qty_edit_mode"] = False
        ss["qty_edit_values"] = [int(r["Quantità"]) for r in righe_tabella]
        ss["inail_esclusa"] = inail_esclusa

        # Mantengo in sessione i nomi delle colonne utilizzate
        ss["col_pu"] = col_pu
        ss["col_pt"] = col_pt
        ss["total_label"] = total_label

        # Costruzione testo recap MK
        mk_macro_label = ss.get("mk_macro_label")
        mk_caldaie_sel = ss.get("mk_caldaie_sel", {})
        mk_separatore_label = ss.get("mk_separatore_label", "Nessuna")
        mk_sottoopzione = ss.get("mk_sottoopzione", "Nessuna")
        mk_centralina = ss.get("mk_centralina", "Nessuna")

        recap_md = ""
        if mk_macro_label:
            layout_items = []
            for full_name, qty in mk_caldaie_sel.items():
                if qty <= 0:
                    continue
                short = full_name.replace("SMILE ENERGY ", "").strip()
                layout_items.extend([short] * int(qty))
            layout_str = " + ".join(layout_items) if layout_items else "-"

            recap_md = (
                f"Configurazione: {mk_macro_label}  \n"
                f"Layout caldaie: {layout_str}  \n"
                f"Separatore idraulico: {mk_separatore_label}  \n"
                f"Anello primario: {mk_sottoopzione}  \n"
                f"Centralina: {mk_centralina}"
            )

        ss["mk_recap_text"] = recap_md

        # Output finale
        mostra_riepilogo(righe_tabella, totale_configurazione)

# Rerender persistente
if ss.get("output_rows") and not ss.get("rendered_this_run"):
    mostra_riepilogo(ss["output_rows"], ss["totale_conf"])
