from __future__ import annotations
"""PDF report helper – now with simple *flow layout*.

* start_report / finish_report
* page()           – opens a new US-letter page
* add_text()       – drops a line of text at the next free slot
* fig_stacked()    – inserts a full-width subplot at the next free slot
* enable_live_preview(True)
"""
from contextlib import contextmanager
from inspect import getmodule, stack
from pathlib import Path
from typing import Optional, Tuple

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

# ── globals ───────────────────────────────────────────────────────────
_PDF: PdfPages | None = None
_REPORT_PATH: Path | None = None
_SHOW_LIVE: bool = False

__all__ = [
    "start_report",
    "finish_report",
    "enable_live_preview",
    "page",
    "add_text",
    "fig_stacked",
]

# ── public helpers ────────────────────────────────────────────────────
def enable_live_preview(state: bool = True) -> None:
    global _SHOW_LIVE
    _SHOW_LIVE = state


def start_report(path: str | Path = "model_report.pdf", *, append: bool = False) -> None:
    global _PDF, _REPORT_PATH
    caller_dir = Path(getmodule(stack()[1][0]).__file__).parent
    _REPORT_PATH = (Path(path) if Path(path).is_absolute() else caller_dir / path).with_suffix(".pdf")
    if not append and _REPORT_PATH.exists():
        _REPORT_PATH.unlink()
    _PDF = PdfPages(_REPORT_PATH)
    print(f"📄  Report started → {_REPORT_PATH}  ({'append' if append else 'new'})")


def finish_report() -> None:
    global _PDF
    if _PDF is not None:
        _PDF.close()
        print(f"✅  Report written → {_REPORT_PATH}")
        _PDF = None


# ── layout helpers ────────────────────────────────────────────────────
def _next_slot(fig, height_frac: float) -> Tuple[float, float, float, float]:
    """Return [left, bottom, width, height] for the next item and update cursor."""
    if not hasattr(fig, "_cursor_y"):
        fig._cursor_y = 0.92          # first slot just below title area
    bottom = fig._cursor_y - height_frac
    if bottom < 0.05:
        raise RuntimeError("Not enough space left on this page; start a new page.")
    fig._cursor_y = bottom - 0.02     # add small gap
    return 0.06, bottom, 0.88, height_frac


# ── context managers ─────────────────────────────────────────────────
@contextmanager
def page(*, title: str | None = None, show: Optional[bool] = None):
    want_show = _SHOW_LIVE if show is None else show
    original_interactive = plt.isinteractive()
    if not want_show:
        plt.ioff()

    fig = plt.figure(figsize=(8.5, 11))
    fig._cursor_y = 0.94              # start cursor
    if title:
        fig.suptitle(title, y=0.97, fontsize=14)

    try:
        yield fig
        if _PDF:
            _PDF.savefig(fig)
        if want_show:
            plt.show(block=True)
    finally:
        plt.close(fig)
        plt.interactive(original_interactive)


def add_text(fig, text: str, *, fontsize: int = 10, lines: int | None = None):
    """Add a block of wrapped text at the next free slot."""
    if lines is None:
        lines = text.count("\n") + 1
    height = 0.03 * lines
    l, b, w, h = _next_slot(fig, height)
    fig.text(l, b + h/2, text, fontsize=fontsize, va="center", ha="left", wrap=True)

# --------------------------------------------------------------------
# Context manager – stacked figure, auto-spill to next page
# --------------------------------------------------------------------
@contextmanager
def fig_stacked(
    fig,
    subtitle: str,
    *,
    array_shape: Optional[Tuple[int, int]] = None,
    max_width_inches: Optional[float] = None,
    show: Optional[bool] = None,
):
    """
    Insert a subplot at the next vertical slot.  When the slot would
    overflow the current page a *fresh* page is opened automatically.

    Returns
    -------
    Axes object that you can plot into inside the `with` block.
    """
    import matplotlib.pyplot as plt
    from contextlib import nullcontext

    # -------------------------------- global / parent preview setting
    want_show = _SHOW_LIVE if show is None else show

    # ---- helper – open a *new* page (used only on spill-over) -------
    extra_page_cm = nullcontext()      # will stay a no-op in most calls

    def _maybe_new_page(cur_fig):
        remaining = cur_fig._cursor_y - 0.05   # keep bottom margin
        if remaining <= 0.02:                  # !! no room left !!
            # spin up a brand-new page *without* title
            nonlocal extra_page_cm
            extra_page_cm = page(show=show)    # page() is in same module
            return extra_page_cm.__enter__()
        return cur_fig

    # ---------------------------------------------------- select page
    fig = _maybe_new_page(fig)

    # ---------- geometry & slot computation -------------------------
    rows, cols = array_shape or (1, 1)
    aspect     = cols / rows

    total_width_in = 8.5
    margin_in      = 0.5                        # 0.25″ each side
    usable_w_in    = total_width_in - 2 * margin_in
    target_w_in    = (
        min(usable_w_in, max_width_inches) if max_width_inches else usable_w_in
    )
    width_frac     = target_w_in / total_width_in
    desired_h_frac = width_frac / aspect

    # how much vertical space truly remains on *this* page now?
    remaining      = fig._cursor_y - 0.05
    height_frac    = min(desired_h_frac, remaining - 0.02)

    # slot coords
    l, b, _, _ = _next_slot(fig, height_frac)
    w          = width_frac * (1 - 0.06 - 0.06)   # adjust for margins

    ax = fig.add_axes([l, b, w, height_frac])
    ax.set_title(subtitle, fontsize=11)

    try:
        yield ax
        if want_show:
            plt.show(block=True)
    finally:
        # close the extra spill-over page if we had to open one
        if extra_page_cm is not nullcontext():
            extra_page_cm.__exit__(None, None, None)




# # -------------------------------------------------------------------
# # 1.  Stacked top & bottom plots on a single page
# # -------------------------------------------------------------------
# with reu.page(title="Top vs. Bottom (stacked)", show=True) as pg:
#     reu.add_text(pg,
#                  "Vertical comparison of the first and last model layers.",
#                  fontsize=11)

#     # top layer (first slot)
#     with reu.fig_stacked(pg, "Top layer elevation",
#                          array_shape=_top.shape,max_width_inches=4) as ax:
#         im = ax.imshow(_top, cmap="terrain", origin="lower")
#         ax.figure.colorbar(im, ax=ax, label="ft")

#     # bottom layer (next slot)
#     with reu.fig_stacked(pg, "Bottom layer elevation (L40)",
#                          array_shape=_botms[-1].shape,max_width_inches=4) as ax:
#         im = ax.imshow(_botms[-1], cmap="terrain", origin="lower")
#         ax.figure.colorbar(im, ax=ax, label="ft")

# # -------------------------------------------------------------------
# # 2.  Overview: caption + one large plot
# # -------------------------------------------------------------------
# with reu.page(title="Model Domain – Top Layer") as pg:
#     reu.add_text(pg,
#                  "This page shows the raster-derived elevation used as the "
#                  "top of groundwater Layer 1.")

#     with reu.fig_stacked(pg, "Top layer elevation",
#                          array_shape=_top.shape,max_width_inches=4) as ax:
#         im = ax.imshow(_top, cmap="terrain", origin="lower")
#         ax.figure.colorbar(im, ax=ax, label="ft")

# # -------------------------------------------------------------------
# # 3.  Side-by-side comparison (manual layout inside the page)
# # -------------------------------------------------------------------
# with reu.page(title="Top vs. Bottom (side-by-side)") as pg:
#     gs = pg.add_gridspec(1, 2, left=0.05, right=0.95, top=0.92,
#                          bottom=0.05, wspace=0.15)
#     ax1 = pg.add_subplot(gs[0, 0])
#     ax2 = pg.add_subplot(gs[0, 1])

#     im1 = ax1.imshow(_top, cmap="terrain", origin="lower")
#     ax1.set_title("Top layer")
#     pg.colorbar(im1, ax=ax1, label="ft")

#     im2 = ax2.imshow(_botms[-1], cmap="terrain", origin="lower")
#     ax2.set_title("Bottom layer (L40)")
#     pg.colorbar(im2, ax=ax2, label="ft")

# # -------------------------------------------------------------------
# # Stack-up: top & bottom layers share all the remaining space equally
# # -------------------------------------------------------------------
# with reu.page(title="Top vs. Bottom (stacked)") as pg:
#     # 1) Caption (flows like any other text block)
#     reu.add_text(pg,
#                  "Vertical comparison of the first and last model layers.",
#                  fontsize=11)
#     top_of_plots = pg._cursor_y            # free space starts here

#     gs = pg.add_gridspec(
#         2, 1,
#         left   = 0.05,
#         right  = 0.95,
#         top    = top_of_plots,             # start exactly where cursor is
#         bottom = 0.05,                     # keep bottom margin
#         hspace = 0.15
#     )

#     # 3) Draw the two plots
#     ax1 = pg.add_subplot(gs[0, 0])
#     ax2 = pg.add_subplot(gs[1, 0])

#     im1 = ax1.imshow(_top, cmap="terrain", origin="lower")
#     ax1.set_title("Top layer elevation")
#     pg.colorbar(im1, ax=ax1, label="ft")

#     im2 = ax2.imshow(_botms[-1], cmap="terrain", origin="lower")
#     ax2.set_title("Bottom layer elevation (L40)")
#     pg.colorbar(im2, ax=ax2, label="ft")

#     # 4) Tell the flow-layout that we’ve consumed all remaining space
#     #    (so the next add_text / fig_stacked would force a new page).
#     pg._cursor_y = 0.03                    # a hair above bottom margin
