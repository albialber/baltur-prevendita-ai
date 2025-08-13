from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Literal

# =========================
# MODELLI & POTENZE (kW eq.)
# =========================
BOILERS_POT = {
    "SMILE ENERGY MK 50": 46,
    "SMILE ENERGY MK 70": 61,
    "SMILE ENERGY MK 90": 82,
    "SMILE ENERGY MK 115": 105,
    "SMILE ENERGY MK 160SP": 105,
    "SMILE ENERGY MK 160": 145,
}
BOILERS_ALIAS = {
    "MK 50": "SMILE ENERGY MK 50",
    "MK 70": "SMILE ENERGY MK 70",
    "MK 90": "SMILE ENERGY MK 90",
    "MK 115": "SMILE ENERGY MK 115",
    "MK 160SP": "SMILE ENERGY MK 160SP",
    "MK 160": "SMILE ENERGY MK 160",
}
MIN_QTY = 2
MAX_QTY = 4

# =========================
# CODICI (dal listino)
# =========================
C = {
    # Telai muro / isola
    "TELAIO_MURO_1E": "96870610",
    "TELAIO_MURO_2E": "96870611",
    "TELAIO_ISOLA_2E": "96870612",
    "TELAIO_ISOLA_4E": "96870613",

    # Box esterni + pannelli/estensioni
    "BOX_1_MOD_SE": "96870604",
    "KIT_PANNELLI_BOX_SE": "96870605",
    "KIT_ESTENSIONE_BOX_SE": "96870606",

    # INAIL / valvole INAIL / valvole intercettazione combustibile
    "KIT_INAIL_ORIZZ": "96870509",
    "KIT_INAIL_ENERGY": "96870503",
    "KIT_INAIL_SMILE160": "96870520",
    "VALV_2_7_BAR_1\":1_1_4F": "96870517",
    "VALV_4_BAR_1\":1_1_4F": "96870519",
    "VALV_2_7_BAR_1_2\"Fx3_4\"F": "96870516",
    "VALV_4_BAR_1_2\"Fx3_4\"F": "96870518",
    "VALV_INT_COMB_1": "96900033",
    "VALV_INT_COMB_1_1_2": "96900035",

    # Collettori (gas / MI-RI / scarico condensa)
    "COLL_GAS_1E": "96870505",
    "COLL_GAS_2E": "96870506",
    "COLL_MIRI_1E": "96870507",
    "COLL_MIRI_2E": "96870508",
    "COLL_SC_COND_1E": "96870510",
    "COLL_SC_COND_2E": "96870511",
    # Speciale isola
    "COLL_ISOLA_EXTRA": "96900182",

    # Fumisteria interna - collettori e tappi (in linea)
    "KIT_FUMI_D125_AT80": "96870700",
    "KIT_FUMI_D160_AT80": "96870701",
    "KIT_FUMI_D160_AT100": "96870702",
    "KIT_FUMI_D200_AT80": "96870703",
    "KIT_FUMI_D200_AT100": "96870704",
    "TAPPO_D125": "96870705",
    "TAPPO_D160": "96870706",
    "TAPPO_D200": "96870707",

    # Fumisteria interna - ad isola
    "COLL_ISOLA_D160": "96870727",
    "COLL_ISOLA_D200": "96870728",
    "ADATT_ISOLA_AT80": "96870729",
    "ADATT_ISOLA_AT100": "96870730",
    "TAPPO_ISOLA": "96870731",
    "TAPPO_ISOLA_D160": "96870706",
    "TAPPO_ISOLA_D200": "96870707",

    # Terminali per configurazioni esterne (al posto fumisteria interna)
    "TERMINALE_D80": "96600445",
    "TERMINALE_D100": "96600446",

    # Equilibratore + kit tubi + circolatori
    "EQUIL_DN65": "96870522",
    "EQUIL_DN100": "96870523",
    "KIT_TUBI_EQUIL_DN65": "96870017",
    "KIT_TUBI_EQUIL_DN100": "96870018",
    "KIT_TUBI_EQUIL_CIRC_DN65": "96870019",
    "KIT_TUBI_EQUIL_CIRC_DN100": "96870020",
    "CIRC_MAGNA1_50_100": "96870524",
    "CIRC_MAGNA1_65_150": "96870525",

    # Scambiatore SSB - kit tubi
    "KIT_TUBI_SCAMB_DX": "96870013",
    "KIT_TUBI_SCAMB_SX": "96870014",
    "KIT_TUBI_SCAMB_CIRC_DX": "96870015",
    "KIT_TUBI_SCAMB_CIRC_SX": "96870016",

    # Centraline
    "ALPHA_MASTER": "96870212",
    "ALPHA_SLAVE": "96870213",
    "THETA_KIT": "96910024",
    "THETA_IF_OT": "96870206",
    "OMEGA_BOX": "96870350",
    "OMEGA_IF_MODBUS_OT": "96870354",
    "MODBUS_IF": "96910035",
    "IF_0_10V": "96910025",

    # Caldaie (codici ufficiali per aggiunta in batteria)
    "MK50": "82000390",
    "MK70": "82000330",
    "MK90": "82000340",
    "MK115": "82000350",
    "MK160SP": "82000360",
    "MK160": "82000370",
}

# Mappa nomi "lunghi" -> codice per aggiungere le caldaie in distinta (cascata)
BOILERS_CODE_CASCATA = {
    "SMILE ENERGY MK 50": C["MK50"],
    "SMILE ENERGY MK 70": C["MK70"],
    "SMILE ENERGY MK 90": C["MK90"],
    "SMILE ENERGY MK 115": C["MK115"],
    "SMILE ENERGY MK 160SP": C["MK160SP"],
    "SMILE ENERGY MK 160": C["MK160"],
}

# (facoltativo) liste scambiatori per UI
SSB_MODELS: List[tuple[str, str]] = []
SII_PRO_MODELS: List[tuple[str, str]] = []

# =========================
# Tipi & strutture
# =========================
MacroCfg = Literal["INT_LINEA", "INT_ISOLA", "ESTERNO", "SINGOLO_INT", "SINGOLO_EST"]
Separatore = Literal["NESSUNA", "SSB", "SII_PRO", "EQUILIBRATORE"]
SottoOpz = Literal["KIT_TUBI", "KIT_TUBI_CIRC", "NESSUNA"]
Centralina = Literal["ALPHA", "THETA", "OMEGA", "MODBUS", "0-10V"]

@dataclass
class LineItem:
    code: str
    name: str
    qty: int = 1

@dataclass
class ConfigInput:
    macro: MacroCfg
    # cascata
    caldaie: Optional[Dict[str, int]] = None
    separatore: Optional[Separatore] = None
    sottoopzione: Optional[SottoOpz] = None
    ssb_code: Optional[str] = None
    sii_code: Optional[str] = None
    centralina: Optional[Centralina] = None
    # singola
    singola_modello: Optional[str] = None
    singola_sottocat: Optional[Literal["SSB", "EQUILIBRATORE"]] = None

# =========================
# Utilità comuni
# =========================
def _norm_boiler_name(name: str) -> str:
    return BOILERS_ALIAS.get(name, name)

def _potenze(caldaie: Dict[str, int]) -> Tuple[int, int, int, Dict[int, int]]:
    qty = 0
    potenze = []
    attacchi = {80: 0, 100: 0}
    for k, q in caldaie.items():
        std = _norm_boiler_name(k)
        if std not in BOILERS_POT:
            raise ValueError(f"Modello non riconosciuto: {k}")
        p = BOILERS_POT[std]
        qty += q
        potenze += [p] * q
        if p in (46, 61):
            attacchi[80] += q
        else:
            attacchi[100] += q
    if qty < MIN_QTY or qty > MAX_QTY:
        raise ValueError(f"Numero caldaie non valido: {qty} (min {MIN_QTY}, max {MAX_QTY})")
    ptot = sum(potenze)
    pmax = max(potenze) if potenze else 0
    return qty, ptot, pmax, attacchi

def _valvola_inail_cascata(pmax: int) -> LineItem:
    if pmax in (46, 61):
        return LineItem(C["VALV_2_7_BAR_1\":1_1_4F"], 'VALV. INAIL 2.7 BAR 1"Fx1"1/4F', 1)
    return LineItem(C["VALV_4_BAR_1\":1_1_4F"], 'VALV. INAIL 4 BAR 1"Fx1"1/4F', 1)

def _valvola_interc_comb(ptot: int) -> Optional[LineItem]:
    if ptot < 250:
        return LineItem(C["VALV_INT_COMB_1"], 'VALVOLA INTERC.NE COMB. 1"')
    if 250 <= ptot <= 450:
        return LineItem(C["VALV_INT_COMB_1_1_2"], 'VALVOLA INTERC.NE COMB. 1"1/2')
    return None

# =========================
# Telai
# =========================
def _telai_linea(qty: int) -> List[LineItem]:
    if qty == 2:
        return [LineItem(C["TELAIO_MURO_2E"], "KIT TELAIO MURO 2ELEM. ENERGY", 1)]
    if qty == 3:
        return [
            LineItem(C["TELAIO_MURO_2E"], "KIT TELAIO MURO 2ELEM. ENERGY", 1),
            LineItem(C["TELAIO_MURO_1E"], "KIT TELAIO MURO 1ELEM. ENERGY", 1),
        ]
    if qty == 4:
        return [LineItem(C["TELAIO_MURO_2E"], "KIT TELAIO MURO 2ELEM. ENERGY", 2)]
    raise ValueError("qty non gestita per telai linea")

def _telai_isola(qty: int) -> List[LineItem]:
    if qty == 2:
        return [LineItem(C["TELAIO_ISOLA_2E"], "KIT TELAIO ISOLA 2ELEM. ENERGY", 1)]
    if qty in (3, 4):
        return [LineItem(C["TELAIO_ISOLA_4E"], "KIT TELAIO ISOLA 4ELEM. ENERGY", 1)]
    raise ValueError("qty non gestita per telai isola")

# =========================
# Collettori
# =========================
def _collettori_linea(qty: int) -> List[LineItem]:
    if qty == 2:
        return [
            LineItem(C["COLL_GAS_2E"], "KIT COLLETTORE GAS 2E", 1),
            LineItem(C["COLL_MIRI_2E"], "KIT COLLETTORE MI-RI 2E", 1),
            LineItem(C["COLL_SC_COND_2E"], "KIT COLLETTORE SC.COND. 2E", 1),
        ]
    if qty == 3:
        return [
            LineItem(C["COLL_GAS_2E"], "KIT COLLETTORE GAS 2E", 1),
            LineItem(C["COLL_GAS_1E"], "KIT COLLETTORE GAS 1E", 1),
            LineItem(C["COLL_MIRI_2E"], "KIT COLLETTORE MI-RI 2E", 1),
            LineItem(C["COLL_MIRI_1E"], "KIT COLLETTORE MI-RI 1E", 1),
            LineItem(C["COLL_SC_COND_2E"], "KIT COLLETTORE SC.COND. 2E", 1),
            LineItem(C["COLL_SC_COND_1E"], "KIT COLLETTORE SC.COND. 1E", 1),
        ]
    if qty == 4:
        return [
            LineItem(C["COLL_GAS_2E"], "KIT COLLETTORE GAS 2E", 2),
            LineItem(C["COLL_MIRI_2E"], "KIT COLLETTORE MI-RI 2E", 2),
            LineItem(C["COLL_SC_COND_2E"], "KIT COLLETTORE SC.COND. 2E", 2),
        ]
    raise ValueError("qty non gestita per collettori linea")

def _collettori_isola(qty: int) -> List[LineItem]:
    if qty == 2:
        return [
            LineItem(C["COLL_GAS_1E"], "KIT COLLETTORE GAS 1E", 1),
            LineItem(C["COLL_MIRI_1E"], "KIT COLLETTORE MI-RI 1E", 1),
            LineItem(C["COLL_SC_COND_1E"], "KIT COLLETTORE SC.COND. 1E", 1),
            LineItem(C["COLL_ISOLA_EXTRA"], "ACCESSORIO ISOLA", 1),
        ]
    if qty == 3:
        return [
            LineItem(C["COLL_GAS_2E"], "KIT COLLETTORE GAS 2E", 1),
            LineItem(C["COLL_GAS_1E"], "KIT COLLETTORE GAS 1E", 1),
            LineItem(C["COLL_MIRI_2E"], "KIT COLLETTORE MI-RI 2E", 1),
            LineItem(C["COLL_MIRI_1E"], "KIT COLLETTORE MI-RI 1E", 1),
            LineItem(C["COLL_SC_COND_2E"], "KIT COLLETTORE SC.COND. 2E", 1),
            LineItem(C["COLL_SC_COND_1E"], "KIT COLLETTORE SC.COND. 1E", 1),
            LineItem(C["COLL_ISOLA_EXTRA"], "ACCESSORIO ISOLA", 1),
        ]
    if qty == 4:
        return [
            LineItem(C["COLL_GAS_2E"], "KIT COLLETTORE GAS 2E", 2),
            LineItem(C["COLL_MIRI_2E"], "KIT COLLETTORE MI-RI 2E", 2),
            LineItem(C["COLL_SC_COND_2E"], "KIT COLLETTORE SC.COND. 2E", 2),
            LineItem(C["COLL_ISOLA_EXTRA"], "ACCESSORIO ISOLA", 1),
        ]
    raise ValueError("qty non gestita per collettori isola")

# =========================
# Fumisteria (interno)
# =========================
def _fumisteria_linea(ptot: int, attacchi: Dict[int, int]) -> List[LineItem]:
    items: List[LineItem] = []
    if ptot <= 160:
        if attacchi[80] > 0:
            items.append(LineItem(C["KIT_FUMI_D125_AT80"], "KIT COL.RE FUMI D125 AT.DN80", attacchi[80]))
        items.append(LineItem(C["TAPPO_D125"], "TAPPO COL.RE FUMI D125", 1))
    elif 161 <= ptot <= 260:
        if attacchi[80] > 0:
            items.append(LineItem(C["KIT_FUMI_D160_AT80"], "KIT COL.RE FUMI D160 AT.DN80", attacchi[80]))
        if attacchi[100] > 0:
            items.append(LineItem(C["KIT_FUMI_D160_AT100"], "KIT COL.RE FUMI D160 AT.DN100", attacchi[100]))
        items.append(LineItem(C["TAPPO_D160"], "TAPPO COL.RE FUMI D160", 1))
    else:
        if attacchi[80] > 0:
            items.append(LineItem(C["KIT_FUMI_D200_AT80"], "KIT COL.RE FUMI D200 AT.DN80", attacchi[80]))
        if attacchi[100] > 0:
            items.append(LineItem(C["KIT_FUMI_D200_AT100"], "KIT COL.RE FUMI D200 AT.DN100", attacchi[100]))
        items.append(LineItem(C["TAPPO_D200"], "TAPPO COL.RE FUMI D200", 1))
    return items

def _fumisteria_isola(ptot: int, attacchi: Dict[int, int], qty: int) -> List[LineItem]:
    items: List[LineItem] = []
    if ptot <= 260:
        if qty == 2:
            items.append(LineItem(C["COLL_ISOLA_D160"], "COLLETTORE ISOLA D160", 1))
            items.append(LineItem(C["TAPPO_ISOLA_D160"], "TAPPO COL.RE FUMI D160", 1))
        elif qty == 3:
            items.append(LineItem(C["COLL_ISOLA_D160"], "COLLETTORE ISOLA D160", 2))
            items.append(LineItem(C["TAPPO_ISOLA_D160"], "TAPPO COL.RE FUMI D160", 1))
            items.append(LineItem(C["TAPPO_ISOLA"], "TAPPO ACCESSORIO ISOLA", 1))
        elif qty == 4:
            items.append(LineItem(C["COLL_ISOLA_D160"], "COLLETTORE ISOLA D160", 2))
        if attacchi[80] > 0:
            items.append(LineItem(C["ADATT_ISOLA_AT80"], "ADATTATORE ISOLA AT80", attacchi[80]))
        if attacchi[100] > 0:
            items.append(LineItem(C["ADATT_ISOLA_AT100"], "ADATTATORE ISOLA AT100", attacchi[100]))
    else:
        if qty == 2:
            items.append(LineItem(C["COLL_ISOLA_D200"], "COLLETTORE ISOLA D200", 1))
            items.append(LineItem(C["TAPPO_ISOLA_D200"], "TAPPO COL.RE FUMI D200", 1))
        elif qty == 3:
            items.append(LineItem(C["COLL_ISOLA_D200"], "COLLETTORE ISOLA D200", 2))
            items.append(LineItem(C["TAPPO_ISOLA_D200"], "TAPPO COL.RE FUMI D200", 1))
            items.append(LineItem(C["TAPPO_ISOLA"], "TAPPO ACCESSORIO ISOLA", 1))
        elif qty == 4:
            items.append(LineItem(C["COLL_ISOLA_D200"], "COLLETTORE ISOLA D200", 2))
        if attacchi[80] > 0:
            items.append(LineItem(C["ADATT_ISOLA_AT80"], "ADATTATORE ISOLA AT80", attacchi[80]))
        if attacchi[100] > 0:
            items.append(LineItem(C["ADATT_ISOLA_AT100"], "ADATTATORE ISOLA AT100", attacchi[100]))
    return items

# =========================
# Scenari separatore (cascata)
# =========================
def _acc_nessuna(pmax: int, ptot: int) -> List[LineItem]:
    items = [LineItem(C["KIT_INAIL_ORIZZ"], "KIT INAIL ORIZZONTALE", 1)]
    items.append(_valvola_inail_cascata(pmax))
    vcomb = _valvola_interc_comb(ptot)
    if vcomb: items.append(vcomb)
    return items

def _acc_ssb(pmax: int, ptot: int, sottoopzione: SottoOpz, ssb_code: Optional[str]) -> List[LineItem]:
    items: List[LineItem] = []
    if sottoopzione == "KIT_TUBI":
        items.append(LineItem(C["KIT_TUBI_SCAMB_DX"], "KIT TUBI SCAMBIATORE BOX DX", 1))
        items.append(_valvola_inail_cascata(pmax))
    elif sottoopzione == "KIT_TUBI_CIRC":
        items.append(LineItem(C["KIT_TUBI_SCAMB_CIRC_DX"], "KIT TUBI SCAMB.-CIRCOL. BOX DX", 1))
        items.append(_valvola_inail_cascata(pmax))
        circ = C["CIRC_MAGNA1_50_100"] if ptot < 280 else C["CIRC_MAGNA1_65_150"]
        items.append(LineItem(circ, "CIRCOLATORE SECONDARIO", 1))
    else:
        items.append(LineItem(C["KIT_INAIL_ORIZZ"], "KIT INAIL ORIZZONTALE", 1))
        items.append(_valvola_inail_cascata(pmax))
    vcomb = _valvola_interc_comb(ptot)
    if vcomb: items.append(vcomb)
    if ssb_code:
        items.append(LineItem(ssb_code, "SCAMBIATORE SSB SELEZIONATO", 1))
    return items

def _acc_sii(pmax: int, ptot: int, sii_code: Optional[str]) -> List[LineItem]:
    items = [LineItem(C["KIT_INAIL_ORIZZ"], "KIT INAIL ORIZZONTALE", 1), _valvola_inail_cascata(pmax)]
    vcomb = _valvola_interc_comb(ptot)
    if vcomb: items.append(vcomb)
    if sii_code:
        items.append(LineItem(sii_code, "SCAMBIATORE SII PRO SELEZIONATO", 1))
    return items

def _acc_equil(ptot: int, pmax: int, sottoopzione: SottoOpz) -> List[LineItem]:
    dn = "DN65" if ptot < 280 else "DN100"
    items: List[LineItem] = []
    if sottoopzione == "KIT_TUBI":
        items.append(LineItem(C[f"EQUIL_{dn}"], f"EQUILIBRATORE BOX {dn}", 1))
        items.append(LineItem(C[f"KIT_TUBI_EQUIL_{dn}"], f"KIT TUBI EQUILIBRATORE BOX {dn}", 1))
        items.append(_valvola_inail_cascata(pmax))
    elif sottoopzione == "KIT_TUBI_CIRC":
        items.append(LineItem(C[f"EQUIL_{dn}"], f"EQUILIBRATORE BOX {dn}", 1))
        items.append(LineItem(C[f"KIT_TUBI_EQUIL_CIRC_{dn}"], f"KIT TUBI EQUIL.-CIRC. BOX {dn}", 1))
        items.append(_valvola_inail_cascata(pmax))
        circ = C["CIRC_MAGNA1_50_100"] if dn == "DN65" else C["CIRC_MAGNA1_65_150"]
        items.append(LineItem(circ, "CIRCOLATORE SECONDARIO", 1))
    else:
        items.append(LineItem(C["KIT_INAIL_ORIZZ"], "KIT INAIL ORIZZONTALE", 1))
        items.append(_valvola_inail_cascata(pmax))
        items.append(LineItem(C[f"EQUIL_{dn}"], f"EQUILIBRATORE BOX {dn}", 1))
    vcomb = _valvola_interc_comb(ptot)
    if vcomb: items.append(vcomb)
    return items

# =========================
# Centraline
# =========================
def _centralina_items(centralina: Centralina, qty_cald: int) -> List[LineItem]:
    if centralina == "ALPHA":
        return [
            LineItem(C["ALPHA_MASTER"], "ALPHA MASTER CONTROL", 1),
            LineItem(C["ALPHA_SLAVE"], "ALPHA SLAVE", max(qty_cald - 1, 0)),
        ]
    if centralina == "THETA":
        return [
            LineItem(C["THETA_KIT"], "KIT CENTR. CLIMATICA THETA", 1),
            LineItem(C["THETA_IF_OT"], "SCHEDA INTERFACCIA OPENTHERM", qty_cald),
        ]
    if centralina == "OMEGA":
        return [
            LineItem(C["OMEGA_BOX"], "OMEGA CONTROL BOX", 1),
            LineItem(C["OMEGA_IF_MODBUS_OT"], "OMEGA INTERFACCIA MODBUS-OT", qty_cald),
        ]
    if centralina == "MODBUS":
        return [LineItem(C["MODBUS_IF"], "SCHEDA INTERF. OT-MODBUS MK/TK", qty_cald)]
    if centralina == "0-10V":
        return [LineItem(C["IF_0_10V"], "SCHEDA INTERFAC. 0-10V ENERGY", qty_cald)]
    raise ValueError("Centralina non riconosciuta")

# =========================
# Esterno: terminali + box/pannelli
# =========================
def _terminali_esterno(attacchi: Dict[int, int]) -> List[LineItem]:
    items: List[LineItem] = []
    if attacchi[80] > 0:
        items.append(LineItem(C["TERMINALE_D80"], "TERMINALE SCARICO D80", attacchi[80]))
    if attacchi[100] > 0:
        items.append(LineItem(C["TERMINALE_D100"], "TERMINALE SCARICO D100", attacchi[100]))
    return items

def _box_pannelli_esterno(separatore: Separatore, sottoopzione: Optional[SottoOpz], qty_cald: int) -> List[LineItem]:
    add = 0
    if separatore == "SII_PRO":
        add = 2
    elif separatore == "SSB":
        add = 1 if sottoopzione in ("KIT_TUBI", "KIT_TUBI_CIRC") else 2
    elif separatore == "EQUILIBRATORE":
        add = 1 if sottoopzione == "KIT_TUBI" else 2
    elif separatore == "NESSUNA":
        add = 1
    return [
        LineItem(C["BOX_1_MOD_SE"], "BOX 1 MODULO ENERGY SE", qty_cald + add),
        LineItem(C["KIT_PANNELLI_BOX_SE"], "KIT PANNELLI BOX ENERGY SE", 1)
    ]

# =========================
# Helper: aggiungi caldaie in distinta (cascata)
# =========================
def _boiler_lines_cascata(caldaie: Dict[str, int]) -> List[LineItem]:
    items: List[LineItem] = []
    for full_name, qty in caldaie.items():
        if qty <= 0:
            continue
        code = BOILERS_CODE_CASCATA.get(full_name)
        if not code:
            continue
        items.append(LineItem(code, full_name, qty))
    return items

# =========================
# GENERATORE DISTINTA
# =========================
def genera_distinta(cfg: ConfigInput) -> List[LineItem]:
    if cfg.macro in ("INT_LINEA", "INT_ISOLA", "ESTERNO"):
        if not cfg.caldaie or not cfg.separatore or not cfg.centralina:
            raise ValueError("Per le configurazioni in cascata servono caldaie, separatore e centralina.")
        qty, ptot, pmax, att = _potenze(cfg.caldaie)

        # Telai & Collettori
        if cfg.macro == "INT_LINEA":
            telai = _telai_linea(qty)
            coll = _collettori_linea(qty)
        elif cfg.macro == "INT_ISOLA":
            telai = _telai_isola(qty)
            coll = _collettori_isola(qty)
        else:  # ESTERNO -> collettori come interno in linea (richiesta)
            telai = []
            coll = _collettori_linea(qty)

        # Accessori per separatore
        if cfg.separatore == "NESSUNA":
            acc = _acc_nessuna(pmax, ptot)
        elif cfg.separatore == "SSB":
            if not cfg.sottoopzione:
                raise ValueError("Per SSB serve la sotto-opzione.")
            acc = _acc_ssb(pmax, ptot, cfg.sottoopzione, cfg.ssb_code)
        elif cfg.separatore == "SII_PRO":
            acc = _acc_sii(pmax, ptot, cfg.sii_code)
        elif cfg.separatore == "EQUILIBRATORE":
            if not cfg.sottoopzione:
                raise ValueError("Per EQUILIBRATORE serve la sotto-opzione.")
            acc = _acc_equil(ptot, pmax, cfg.sottoopzione)
        else:
            raise ValueError("Separatore non riconosciuto")

        # Fumi / terminali
        if cfg.macro == "INT_LINEA":
            fumi = _fumisteria_linea(ptot, att)
        elif cfg.macro == "INT_ISOLA":
            fumi = _fumisteria_isola(ptot, att, qty)
        else:
            fumi = _terminali_esterno(att)

        # Centralina
        centr = _centralina_items(cfg.centralina, qty)

        # **Aggiunta richiesta**: caldaie sempre in distinta per le configurazioni in batteria
        boilers = _boiler_lines_cascata(cfg.caldaie)

        out = []
        out += boilers + telai + coll + acc + fumi + centr

        # Esterno: box/pannelli
        if cfg.macro == "ESTERNO":
            out += _box_pannelli_esterno(cfg.separatore, cfg.sottoopzione, qty)

        return _merge_same_code(out)

    # SINGOLE (immutato)
    if cfg.macro in ("SINGOLO_INT", "SINGOLO_EST"):
        if not cfg.singola_modello or not cfg.singola_sottocat:
            raise ValueError("Per le singole servono modello e sottocategoria.")
        return _distinta_singola(cfg)
    raise ValueError("Macro configurazione non riconosciuta.")

def _merge_same_code(items: List[LineItem]) -> List[LineItem]:
    acc: Dict[str, LineItem] = {}
    ordered: List[str] = []
    for it in items:
        if not it.code:
            continue
        if it.code not in acc:
            acc[it.code] = LineItem(it.code, it.name, it.qty)
            ordered.append(it.code)
        else:
            acc[it.code].qty += it.qty
    return [acc[c] for c in ordered]

# =========================
# DISTINTE - SINGOLE (come versione precedente; non modificata)
# =========================
def _distinta_singola(cfg: ConfigInput) -> List[LineItem]:
    m = cfg.singola_modello.strip().upper().replace(" ", "")
    cat = cfg.singola_sottocat

    def LI(code, name, qty=1): return LineItem(code, name, qty)

    out: List[LineItem] = []

    if cfg.macro == "SINGOLO_INT":
        if cat == "SSB":
            if m == "MK50":
                out = [LI(C["MK50"], "SMILE ENERGY MK 50"),
                       LI("96870026", "KIT TUBI SCAMBIATORE (INT)"),
                       LI(C["KIT_INAIL_ENERGY"], "KIT INAIL ENERGY"),
                       LI("96900326", "SSB 55"),
                       LI(C["VALV_2_7_BAR_1_2\"Fx3_4\"F"], "VALV. INAIL 2.7 BAR 1/2\"Fx3/4\"F")]
            elif m == "MK70":
                out = [LI(C["MK70"], "SMILE ENERGY MK 70"),
                       LI("96870026", "KIT TUBI SCAMBIATORE (INT)"),
                       LI(C["KIT_INAIL_ENERGY"], "KIT INAIL ENERGY"),
                       LI("96900327", "SSB 68"),
                       LI(C["VALV_2_7_BAR_1_2\"Fx3_4\"F"], "VALV. INAIL 2.7 BAR 1/2\"Fx3/4\"F")]
            elif m == "MK90":
                out = [LI(C["MK90"], "SMILE ENERGY MK 90"),
                       LI("96870026", "KIT TUBI SCAMBIATORE (INT)"),
                       LI(C["KIT_INAIL_ENERGY"], "KIT INAIL ENERGY"),
                       LI("96900328", "SSB 90"),
                       LI(C["VALV_4_BAR_1_2\"Fx3_4\"F"], "VALV. INAIL 4 BAR 1/2\"Fx3/4\"F")]
            elif m == "MK115":
                out = [LI(C["MK115"], "SMILE ENERGY MK 115"),
                       LI("96870026", "KIT TUBI SCAMBIATORE (INT)"),
                       LI(C["KIT_INAIL_ENERGY"], "KIT INAIL ENERGY"),
                       LI("96900329", "SSB 115"),
                       LI(C["VALV_4_BAR_1_2\"Fx3_4\"F"], "VALV. INAIL 4 BAR 1/2\"Fx3/4\"F")]
            elif m == "MK160SP":
                out = [LI(C["MK160SP"], "SMILE ENERGY MK 160SP"),
                       LI("96870027", "KIT TUBI SCAMBIATORE (INT) 160"),
                       LI("96870529", "KIT INAIL SMILE ENERGY 160SP"),
                       LI("96900331", "SSB 180"),
                       LI(C["VALV_4_BAR_1_2\"Fx3_4\"F"], "VALV. INAIL 4 BAR 1/2\"Fx3/4\"F")]
            elif m == "MK160":
                out = [LI(C["MK160"], "SMILE ENERGY MK 160"),
                       LI("96870027", "KIT TUBI SCAMBIATORE (INT) 160"),
                       LI("96870529", "KIT INAIL SMILE ENERGY 160"),
                       LI("96900331", "SSB 180"),
                       LI(C["VALV_4_BAR_1_2\"Fx3_4\"F"], "VALV. INAIL 4 BAR 1/2\"Fx3/4\"F")]

        elif cat == "EQUILIBRATORE":
            if m in ("MK160", "MK160SP"):
                raise ValueError("Equilibratore non selezionabile per MK 160 / 160SP (singola).")
            base = [
                ("MK50", C["MK50"], "SMILE ENERGY MK 50", C["VALV_2_7_BAR_1_2\"Fx3_4\"F"]),
                ("MK70", C["MK70"], "SMILE ENERGY MK 70", C["VALV_2_7_BAR_1_2\"Fx3_4\"F"]),
                ("MK90", C["MK90"], "SMILE ENERGY MK 90", C["VALV_4_BAR_1_2\"Fx3_4\"F"]),
                ("MK115", C["MK115"], "SMILE ENERGY MK 115", C["VALV_4_BAR_1_2\"Fx3_4\"F"]),
            ]
            for key, code_boiler, name_boiler, valv_code in base:
                if m == key:
                    out = [LI(code_boiler, name_boiler),
                           LI("96870515", "EQUILIBRATORE (INT)"),
                           LI("96870512", "KIT TUBI EQUIL (INT)"),
                           LI(C["KIT_INAIL_ENERGY"], "KIT INAIL ENERGY"),
                           LI(valv_code, "VALV. INAIL"),
                           LI("96870500", "ACCESSORIO EQUIL (INT)")]
                    break

    elif cfg.macro == "SINGOLO_EST":
        if cat == "SSB":
            base = {
                "MK50": (C["MK50"], "96900326"),
                "MK70": (C["MK70"], "96900327"),
                "MK90": (C["MK90"], "96900328"),
                "MK115": (C["MK115"], "96900329"),
                "MK160SP": (C["MK160SP"], "96900331"),
                "MK160": (C["MK160"], "96900331"),
            }
            if m not in base: raise ValueError("Modello singola non riconosciuto")
            boiler_code, ssb = base[m]
            out = [LI(boiler_code, f"SMILE ENERGY {m.replace('MK','MK ')}"),
                   LI("96870026" if m in ("MK50","MK70","MK90","MK115") else "96870027", "KIT TUBI SCAMB. (EST)"),
                   LI(C["KIT_INAIL_ENERGY"] if m not in ("MK160","MK160SP") else C["KIT_INAIL_SMILE160"], "KIT INAIL"),
                   LI(ssb, "SCAMBIATORE SSB"),
                   LI(C["VALV_2_7_BAR_1_2\"Fx3_4\"F"] if m in ("MK50","MK70") else C["VALV_4_BAR_1_2\"Fx3_4\"F"], "VALV. INAIL"),
                   LI(C["BOX_1_MOD_SE"], "BOX 1 MODULO ENERGY SE"),
                   LI(C["KIT_PANNELLI_BOX_SE"], "KIT PANNELLI BOX ENERGY SE")]
            if m in ("MK160","MK160SP"):
                out.append(LI(C["KIT_ESTENSIONE_BOX_SE"], "KIT ESTENSIONE BOX MODULO SE"))
        elif cat == "EQUILIBRATORE":
            if m in ("MK160", "MK160SP"):
                raise ValueError("Equilibratore non selezionabile per MK 160 / 160SP (singola esterna).")
            base = {
                "MK50": (C["MK50"], C["VALV_2_7_BAR_1_2\"Fx3_4\"F"]),
                "MK70": (C["MK70"], C["VALV_2_7_BAR_1_2\"Fx3_4\"F"]),
                "MK90": (C["MK90"], C["VALV_4_BAR_1_2\"Fx3_4\"F"]),
                "MK115": (C["MK115"], C["VALV_4_BAR_1_2\"Fx3_4\"F"]),
            }
            boiler_code, valv = base[m]
            out = [LI(boiler_code, f"SMILE ENERGY {m.replace('MK','MK ')}"),
                   LI("96870515", "EQUILIBRATORE (EST)"),
                   LI("96870512", "KIT TUBI EQUIL (EST)"),
                   LI(C["KIT_INAIL_ENERGY"], "KIT INAIL ENERGY"),
                   LI(valv, "VALV. INAIL"),
                   LI("96870500", "ACCESSORIO EQUIL (EST)"),
                   LI(C["BOX_1_MOD_SE"], "BOX 1 MODULO ENERGY SE"),
                   LI(C["KIT_PANNELLI_BOX_SE"], "KIT PANNELLI BOX ENERGY SE"),
                   LI(C["KIT_ESTENSIONE_BOX_SE"], "KIT ESTENSIONE BOX MODULO SE")]
        else:
            raise ValueError("Sottocategoria singola esterna non riconosciuta")

    return _merge_same_code(out)
