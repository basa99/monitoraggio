"""Streamlit: parsing output di `top` e `df -h` da incolla utente."""

from __future__ import annotations

import math
import re
from typing import NamedTuple

import streamlit as st

BYTES_PER_KIB = 1024
BYTES_PER_MIB = 1024 * 1024
BYTES_PER_GIB = 1024 * 1024 * 1024


def bytes_to_mb_or_gb(num_bytes: float) -> tuple[float, str]:
    """Restituisce valore e suffisso MB se < 1 GiB, altrimenti GB (base 1024)."""
    if num_bytes >= BYTES_PER_GIB:
        return num_bytes / BYTES_PER_GIB, "GB"
    return num_bytes / BYTES_PER_MIB, "MB"


def format_with_percent(total_b: float, free_b: float) -> str:
    if total_b <= 0:
        return "non disponibile"
    pct_free = 100.0 * free_b / total_b
    v_tot, u_tot = bytes_to_mb_or_gb(total_b)
    v_fr, u_fr = bytes_to_mb_or_gb(free_b)
    return (
        f"totale **{v_tot:.2f} {u_tot}**, libera **{v_fr:.2f} {u_fr}** "
        f"({pct_free:.1f}% libera)"
    )


_DF_SUFFIX_TO_UNIT = {"K": "KB", "M": "MB", "G": "GB", "T": "TB"}


def format_df_numeric_part(num: float) -> str:
    """Intero senza decimali se la parte frazionaria è zero; altrimenti decimali senza zeri finali."""
    r = round(num, 12)
    ir = round(r)
    if math.isclose(r, ir, rel_tol=0.0, abs_tol=1e-9):
        return str(ir)
    return f"{r:.12f}".rstrip("0").rstrip(".")


def normalize_df_size_display(token: str) -> str | None:
    """Stesso ordine di grandezza di df -h (K/M/G/T) → KB/MB/GB/TB; virgola solo se parte decimale ≠ 0."""
    raw = token.strip()
    if not raw:
        return None
    m = re.match(
        r"^([\d.,]+)\s*([KMGTkmgt])(?:i?[Bb]?)?$",
        raw,
        re.IGNORECASE,
    )
    if not m:
        return None
    try:
        num = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    suf_key = m.group(2).upper()
    unit = _DF_SUFFIX_TO_UNIT.get(suf_key)
    if unit is None:
        return None
    return f"{format_df_numeric_part(num)}{unit}"


def parse_top(text: str) -> tuple[str | None, str | None, str | None]:
    """Estrae RAM, swap e load average dall'output di top."""
    ram_msg: str | None = None
    swap_msg: str | None = None
    load_msg: str | None = None

    # Load average (prima riga o dove compare)
    lm = re.search(
        r"load\s+averages?\s*:\s*([\d.,]+)\s*,\s*([\d.,]+)\s*,\s*([\d.,]+)",
        text,
        re.IGNORECASE,
    )
    if lm:
        a, b, c = lm.group(1).replace(",", "."), lm.group(2).replace(",", "."), lm.group(3).replace(",", ".")
        load_msg = f"**{a}**, **{b}**, **{c}** (1 / 5 / 15 min)"

    lines = text.splitlines()
    mem_total_b = mem_free_b = None
    swap_total_b = swap_free_b = None

    for raw in lines:
        line = raw.strip()

        # procps-ng: "MiB Mem :  31874.9 total,   8923.4 free," oppure KiB/GiB
        m_modern = re.search(
            r"(KiB|MiB|GiB)\s+Mem\s*:\s*([\d.,]+)\s+total.*?([\d.,]+)\s+free",
            line,
            re.IGNORECASE,
        )
        if m_modern:
            unit = m_modern.group(1).lower()
            total_v = float(m_modern.group(2).replace(",", "."))
            free_v = float(m_modern.group(3).replace(",", "."))
            mul = {"kib": BYTES_PER_KIB, "mib": BYTES_PER_MIB, "gib": BYTES_PER_GIB}[unit]
            mem_total_b = total_v * mul
            mem_free_b = free_v * mul
            continue

        # Formato classico: "Mem:   8178780k total,  ... 2000000k free"
        m_legacy = re.search(
            r"Mem\s*:\s*([\d.,]+)\s*([kmgt]?)\s*total.*?([\d.,]+)\s*([kmgt]?)\s*free",
            line,
            re.IGNORECASE,
        )
        if m_legacy:
            tv = float(m_legacy.group(1).replace(",", "."))
            fv = float(m_legacy.group(3).replace(",", "."))
            u1 = (m_legacy.group(2) or "k").lower()
            u2 = (m_legacy.group(4) or "k").lower()

            def legacy_mul(u: str) -> float:
                return {"k": BYTES_PER_KIB, "m": BYTES_PER_MIB, "g": BYTES_PER_GIB, "t": BYTES_PER_GIB * 1024}[u]

            mem_total_b = tv * legacy_mul(u1)
            mem_free_b = fv * legacy_mul(u2)
            continue

        # Swap moderna
        m_sw = re.search(
            r"(KiB|MiB|GiB)\s+Swap\s*:\s*([\d.,]+)\s+total.*?([\d.,]+)\s+free",
            line,
            re.IGNORECASE,
        )
        if m_sw:
            unit = m_sw.group(1).lower()
            total_v = float(m_sw.group(2).replace(",", "."))
            free_v = float(m_sw.group(3).replace(",", "."))
            mul = {"kib": BYTES_PER_KIB, "mib": BYTES_PER_MIB, "gib": BYTES_PER_GIB}[unit]
            swap_total_b = total_v * mul
            swap_free_b = free_v * mul
            continue

        # Swap legacy: "Swap:  2097148k total, ... 2097148k free"
        m_sw_l = re.search(
            r"Swap\s*:\s*([\d.,]+)\s*([kmgt]?)\s*total.*?([\d.,]+)\s*([kmgt]?)\s*free",
            line,
            re.IGNORECASE,
        )
        if m_sw_l:
            tv = float(m_sw_l.group(1).replace(",", "."))
            fv = float(m_sw_l.group(3).replace(",", "."))
            u1 = (m_sw_l.group(2) or "k").lower()
            u2 = (m_sw_l.group(4) or "k").lower()

            def legacy_mul2(u: str) -> float:
                return {"k": BYTES_PER_KIB, "m": BYTES_PER_MIB, "g": BYTES_PER_GIB, "t": BYTES_PER_GIB * 1024}[u]

            swap_total_b = tv * legacy_mul2(u1)
            swap_free_b = fv * legacy_mul2(u2)

    if mem_total_b is not None and mem_free_b is not None:
        ram_msg = format_with_percent(mem_total_b, mem_free_b)
    if swap_total_b is not None and swap_free_b is not None:
        swap_msg = format_with_percent(swap_total_b, swap_free_b)

    return ram_msg, swap_msg, load_msg


class DfRow(NamedTuple):
    mount: str
    size_disp: str
    avail_disp: str
    use_pct: str


def parse_df_h(text: str) -> dict[str, DfRow]:
    """Parsa df -h e indicizza per punto di mount."""
    targets = {"/data", "/archive", "/backup"}
    out: dict[str, DfRow] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("filesystem"):
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        mount = parts[-1]
        if mount not in targets:
            continue
        size_disp = normalize_df_size_display(parts[1])
        avail_disp = normalize_df_size_display(parts[3])
        use_pct = parts[4]
        if size_disp is None or avail_disp is None:
            continue
        out[mount] = DfRow(
            mount=mount,
            size_disp=size_disp,
            avail_disp=avail_disp,
            use_pct=use_pct,
        )
    return out


def format_partition_row(row: DfRow) -> str:
    return (
        f"dimensione totale **{row.size_disp}**, disponibile **{row.avail_disp}**, "
        f"utilizzo **{row.use_pct}**"
    )


def _clear_top_input() -> None:
    st.session_state["top_in"] = ""


def _clear_df_input() -> None:
    st.session_state["df_in"] = ""


def main() -> None:
    st.set_page_config(page_title="Monitoraggio Linux (top / df)", layout="wide")
    st.title("Monitoraggio risorse Linux")
    st.caption("Incolla l’output dei comandi eseguiti sul server.")

    col_top, col_rule, col_df = st.columns([1, 0.04, 1], gap="medium")

    with col_top:
        st.subheader("Output di `top`")
        top_text = st.text_area(
            "Incolla qui l’output di `top`",
            height=280,
            placeholder="Esempio: prima riga con load average, righe Mem/Swap …",
            key="top_in",
        )
        b_top_clear, b_top_run = st.columns(2)
        with b_top_clear:
            st.button("Svuota campo", key="btn_clear_top", on_click=_clear_top_input)
        with b_top_run:
            if st.button("Analizza top", key="btn_top"):
                if not top_text.strip():
                    st.warning("Incolla prima l’output di top.")
                else:
                    ram, swap, loadavg = parse_top(top_text)
                    st.session_state.top_ram = ram
                    st.session_state.top_swap = swap
                    st.session_state.top_loadavg = loadavg
                    st.session_state.top_has_result = True

        if st.session_state.get("top_has_result"):
            st.subheader("RAM")
            ram = st.session_state.get("top_ram")
            st.markdown(ram or "_Non sono riuscito a leggere Mem dalla clipboard — verifica il formato._")
            st.subheader("Swap")
            swap = st.session_state.get("top_swap")
            st.markdown(swap or "_Non sono riuscito a leggere Swap._")
            st.subheader("Load average")
            loadavg = st.session_state.get("top_loadavg")
            st.markdown(loadavg or "_Load average non trovato._")

    with col_rule:
        st.markdown(
            '<div style="border-left: 2px solid rgba(128, 128, 128, 0.45); min-height: 70vh; margin: 0 auto;"></div>',
            unsafe_allow_html=True,
        )

    with col_df:
        st.subheader("Output di `df -h`")
        df_text = st.text_area(
            "Incolla qui l’output di `df -h`",
            height=280,
            placeholder="Filesystem / Size / Used / Avail / Use% / Mounted on",
            key="df_in",
        )
        b_df_clear, b_df_run = st.columns(2)
        with b_df_clear:
            st.button("Svuota campo", key="btn_clear_df", on_click=_clear_df_input)
        with b_df_run:
            if st.button("Analizza df", key="btn_df"):
                if not df_text.strip():
                    st.warning("Incolla prima l’output di df -h.")
                else:
                    st.session_state.df_found = parse_df_h(df_text)
                    st.session_state.df_has_result = True

        if st.session_state.get("df_has_result"):
            found = st.session_state.df_found
            wanted = ["/data", "/archive", "/backup"]
            for mp in wanted:
                st.subheader(mp)
                if mp in found:
                    st.markdown(format_partition_row(found[mp]))
                else:
                    st.info(f"Mount **{mp}** non presente nell’output.")


if __name__ == "__main__":
    main()
