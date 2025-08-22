from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional, Literal

# -------------------------------------------------------
# Tipi
# -------------------------------------------------------
@dataclass
class LineItem:
    code: str
    name: str
    qty: int = 1

TettoTipo = Literal["INCLINATO_COPPI", "PIANO"]
PannelloTipo = Literal["ETASUN25", "ETASUN20"]
CentralinaTipo = Literal["SBMTDC_V5", "SBLTDC_V3"]

@dataclass
class ConfigSolareInput:
    tetto: TettoTipo
    pannello: PannelloTipo
    n_pannelli: int
    n_file: int
    centralina: CentralinaTipo

# -------------------------------------------------------
# Codici prodotto (da tue specifiche)
# -------------------------------------------------------
C: Dict[str, str] = {
    # Pannelli
    "ETASUN25": "84510031",
    "ETASUN20": "84510030",

    # Staffaggi tetto
    "STAFFA_COPPO": "96960241",
    "PERNO_TETTO_PIANO": "96960242",
    "KIT_INCLINAZIONE": "96960279",

    # Collettori idraulici
    "KIT_START": "96960274",
    "KIT_ESTENSIONE": "96960275",

    # Circolatori
    "CIRC_0_6": "84540070",
    "CIRC_6_12": "84540071",
    "CIRC_12_38": "84540072",

    # Disaeratore/Valvola/Regolatore
    "DISAERATORE": "96960908",
    "VALVOLA": "96960909",
    "REGOLATORE_PORTATA": "96960913",

    # Centraline
    "SBMTDC_V5": "84541030",
    "SBLTDC_V3": "84541031",
}

# Caratteristiche pannelli
AREA_M2 = {
    "ETASUN25": 2.35,
    "ETASUN20": 1.87,
}
PORTATA_UNI = 0.7  # dato tuo

# -------------------------------------------------------
# Utilità
# -------------------------------------------------------
def _merge_same_code(items: List[LineItem]) -> List[LineItem]:
    acc: Dict[str, LineItem] = {}
    order: List[str] = []
    for it in items:
        key = it.code or f"__NO_CODE__::{it.name}"
        if key not in acc:
            acc[key] = LineItem(code=it.code, name=it.name, qty=it.qty)
            order.append(key)
        else:
            acc[key].qty += it.qty
    return [acc[k] for k in order]

def _staffa_qty(n_pannelli: int) -> int:
    # dalla tua tabella: 1→4, 2→6, ... 10→22
    # formula generale coerente: 2*n + 2 (vale per n≥1)
    return 2 * n_pannelli + 2

def _distribuisci_in_file(n_tot: int, n_file: int) -> List[int]:
    """Distribuisce i pannelli tra le file (interi), il più uniforme possibile.
       Le prime 'resto' file hanno un pannello in più.
    """
    base = n_tot // n_file
    resto = n_tot % n_file
    return [(base + 1 if i < resto else base) for i in range(n_file)]

def _kit_start_qty(n_file: int) -> int:
    return n_file  # sempre 1 per fila

def _kit_estensione_qty(per_file: List[int]) -> int:
    # somma di (pannelli_fila - 1) per ogni fila (min 0)
    return sum(max(k - 1, 0) for k in per_file)

def _circolatore_code(pannello: PannelloTipo, n_pannelli: int) -> Optional[str]:
    portata = PORTATA_UNI * AREA_M2[pannello] * n_pannelli
    # tue soglie:
    # 0..6 => 84540070, 6..12 => 84540071, 12..38 => 84540072, >38 => nessuno
    # Implementazione con limiti inclusivi superiori:
    if portata <= 6:
        return C["CIRC_0_6"]
    elif portata <= 12:
        return C["CIRC_6_12"]
    elif portata <= 38:
        return C["CIRC_12_38"]
    else:
        return None

# -------------------------------------------------------
# Entry point: genera in ORDINE come richiesto
# -------------------------------------------------------
def genera_distinta_solare(cfg: ConfigSolareInput) -> List[LineItem]:
    if cfg.n_pannelli < 1 or cfg.n_file < 1:
        return []

    items: List[LineItem] = []

    # 1) Pannelli
    panel_code = C["ETASUN25"] if cfg.pannello == "ETASUN25" else C["ETASUN20"]
    panel_name = "ETASUN 25" if cfg.pannello == "ETASUN25" else "ETASUN 20"
    items.append(LineItem(panel_code, panel_name, cfg.n_pannelli))

    # 2) KIT START
    items.append(LineItem(C["KIT_START"], "KIT START", _kit_start_qty(cfg.n_file)))

    # 3) KIT ESTENSIONE
    distrib = _distribuisci_in_file(cfg.n_pannelli, cfg.n_file)
    items.append(LineItem(C["KIT_ESTENSIONE"], "KIT ESTENSIONE", _kit_estensione_qty(distrib)))

    # 4) Staffaggi
    if cfg.tetto == "INCLINATO_COPPI":
        items.append(LineItem(C["STAFFA_COPPO"], "STAFFA PER TEGOLA A COPPO", _staffa_qty(cfg.n_pannelli)))
    else:  # PIANO
        items.append(LineItem(C["PERNO_TETTO_PIANO"], "PERNO TETTO PIANO", _staffa_qty(cfg.n_pannelli)))
        items.append(LineItem(C["KIT_INCLINAZIONE"], "KIT INCLINAZIONE", cfg.n_pannelli + 1))

    # 5) Circolatore
    circ_code = _circolatore_code(cfg.pannello, cfg.n_pannelli)
    if circ_code:
        items.append(LineItem(circ_code, "CIRCOLATORE", 1))

    # 6) Disaeratore / Valvola / Regolatore di portata
    if cfg.n_file == 1:
        items.append(LineItem(C["DISAERATORE"], "DISAERATORE", 1))
        items.append(LineItem(C["VALVOLA"], "VALVOLA", 1))
        # regolatore = 0 se 1 fila
    else:
        items.append(LineItem(C["DISAERATORE"], "DISAERATORE", cfg.n_file))
        items.append(LineItem(C["VALVOLA"], "VALVOLA", cfg.n_file))
        items.append(LineItem(C["REGOLATORE_PORTATA"], "REGOLATORE DI PORTATA", cfg.n_file))

    # 7) Centralina (1 pezzo fisso)
    cent_code = C[cfg.centralina]
    cent_name = "SBMTDC_V5" if cfg.centralina == "SBMTDC_V5" else "SBLTDC_V3"
    items.append(LineItem(cent_code, f"CENTRALINA {cent_name}", 1))

    return _merge_same_code(items)
