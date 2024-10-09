"""
"""

import pathlib
import tempfile

import streamlit as st

import cellpy
from cellpy.utils import plotutils

DEVELOPER_MODE = False
c = None

st.title(":banana: nana :banana:")


# --- File settings ---
file_settings = st.expander("File settings", expanded=False)
instrument = file_settings.selectbox("Instrument: ", ["neware_txt", "arbin_res"])
model = file_settings.selectbox("Instrument model: ", ["uio_aga", "nn"])
raw_file_extension = file_settings.selectbox("Raw file extension: ", ["csv", "res"])


# --- Cell settings ---
cell_settings = st.expander("Cell information", expanded=True)
nom_cap_specifics = cell_settings.selectbox("Specific: ", ["gravimetric", "areal"])
cycle_mode = cell_settings.selectbox(
    "Cycle mode:",
    [
        "standard",
        "anode",
    ],
    help="select anode if you are testing anode in half-cell configuration",
)
mass = cell_settings.number_input(
    "Mass (mg):", min_value=0.0001, max_value=5000.0, value=1.0
)
nominal_capacity = cell_settings.number_input(
    "Nominal capacity (mAh/g):", min_value=10.0, max_value=5000.0, value=372.0
)
area = cell_settings.number_input(
    "Area (cm2):", min_value=0.0001, max_value=5000.0, value=1.0
)


def plot(
    c,
    do_cycle_plot=True,
    do_summary_plot=True,
    interactive=True,
    xlim=None,
    ylim=None,
    formation_cycles=3,
    **kwargs,
):
    if do_cycle_plot:
        xlim = cycle_plot(c, interactive, xlim, ylim, formation_cycles, **kwargs)

    if do_summary_plot:
        # --- Plotting ---
        summary_plot(c, interactive, **kwargs)


def summary_plot(c, interactive, **kwargs):
    fig_summary = plotutils.summary_plot(
        c,
        interactive=interactive,
        return_data=False,
        **kwargs,
    )
    if interactive:
        st.plotly_chart(
            fig_summary,
            use_container_width=True,
            # theme=None,
        )
    else:
        st.pyplot(fig_summary)


def cycle_plot(c, interactive, xlim, ylim, formation_cycles, **kwargs):
    if xlim is None:
        xlim = [-100, 2100]
    if ylim is None:
        ylim = [0, 1.05]

    fig_cycles = plotutils.plot_cycles(
        c,
        ylim=ylim,
        xlim=xlim,
        formation_cycles=formation_cycles,
        colormap="Blues_r",
        interactive=interactive,
        return_figure=True,
        **kwargs,
    )
    if interactive:
        st.plotly_chart(
            fig_cycles,
            use_container_width=True,
            # theme=None,
        )
    else:
        st.pyplot(fig_cycles)


@st.cache_data
def load_cell(
    tmp_file_names,
    nom_cap_specifics,
    cycle_mode,
    mass,
    nominal_capacity,
    area,
    instrument,
    model,
):
    if isinstance(tmp_file_names, list):
        tmp_file_names = sorted(tmp_file_names)

    # TODO: split this up into two steps (read and make summary)
    c = cellpy.get(
        tmp_file_names,
        instrument=instrument,
        mass=mass,
        area=area,
        cycle_mode=cycle_mode,
        nom_cap_specifics=nom_cap_specifics,
        nominal_capacity=nominal_capacity,
        refuse_copying=True,
        model=model,
    )

    return c


def preprocess_files(raw_file):
    if not len(raw_file):
        st.error("No files uploaded")
        st.stop()
    else:
        progress_bar = st.progress(0.0, "Reading file(s) ...")
        temporary_directory = pathlib.Path(tempfile.gettempdir())
        files = [p.name for p in raw_file]
        number_of_files = len(files)
        delta = 0.3 / number_of_files
        tmp_file_names = [temporary_directory / p.name for p in raw_file]

        for i, (f, t) in enumerate(zip(raw_file, tmp_file_names)):
            progress_bar.progress(i * delta, f"Reading file {i} ...")
            raw_bytes = f.read()
            with open(t, "wb") as b:
                b.write(raw_bytes)
        return tmp_file_names, progress_bar


# --- Upload file ---
raw_file = st.file_uploader(
    f"Upload raw file(s) (*.{raw_file_extension})",
    type=[raw_file_extension],
    accept_multiple_files=True,
)
button_load = st.button("Load file(s)")

# --- Process file ---
if raw_file is not None and button_load:
    print("Loading file(s)")
    print(f"raw_file: {raw_file}")
    tmp_file_names, progress_bar = preprocess_files(raw_file)
    progress_bar.progress(0.2, "Processing file(s) ...")
    c = load_cell(
        tmp_file_names,
        nom_cap_specifics,
        cycle_mode,
        mass,
        nominal_capacity,
        area,
        instrument,
        model,
    )
    st.session_state["c"] = c
    progress_bar.progress(1.0, "File Loaded")
    st.success("File loaded successfully")


# --- Plotting ---
if "c" in st.session_state:
    button_plot = False
    with st.form("plotting_form"):
        plot_settings = st.expander("Plot settings", expanded=True)
        do_cycle_plot = plot_settings.checkbox("Plot cycles", value=True)
        do_summary_plot = plot_settings.checkbox("Plot summary", value=True)
        interactive = plot_settings.checkbox("Interactive plots", value=True)
        button_plot = st.form_submit_button("Plot")

    if button_plot:
        if "c" not in st.session_state:
            st.error("No cell loaded")
        else:
            xlim = None
            ylim = None
            formation_cycles = 3
            c = st.session_state["c"]
            if do_cycle_plot:
                cycle_plot(
                    c,
                    interactive=interactive,
                    xlim=xlim,
                    ylim=ylim,
                    formation_cycles=formation_cycles,
                )
            if do_summary_plot:
                summary_plot(c, interactive=interactive)
