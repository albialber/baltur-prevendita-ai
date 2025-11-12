import streamlit as st
try:
for it in genera_distinta_solare(cfg_input_sol):
add_line(it.code, it.qty)
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
st.markdown(f"**{nome}** \n**Codice:** `{codice}` \n**Quantità:** {int(r.get('Quantità', 0))} \n**Descrizione:** {descr}")


if st.session_state.get("qty_edit_mode"):
st.markdown("### Modifica quantità")
new_qty = []
for i, r in enumerate(st.session_state["output_rows"]):
codice = str(r.get("Codice", ""))
nome = r.get("Prodotto", "")
col1, col2 = st.columns([2, 1])
with col1:
st.write(f"**{nome}** — `{codice}`")
with col2:
val = st.number_input("Quantità", min_value=0, step=1, value=int(st.session_state["qty_edit_values"][i]), key=f"qty_input_{i}")
new_qty.append(int(val))
c_ok, c_cancel = st.columns([1,1])
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


# Render persistente
if st.session_state.get("output_rows") and not st.session_state.get("qty_edit_mode"):
st.markdown(rows_to_markdown_table(st.session_state["output_rows"], VISIBLE_COLS))
st.markdown(f"**Totale configurazione:** {st.session_state['totale_conf']:,.2f} €")
