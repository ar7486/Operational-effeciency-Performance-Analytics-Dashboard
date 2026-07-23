from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Operational Efficiency & Performance Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    :root {
        --text: #132028;
        --muted: #58656f;
        --accent: #0f766e;
        --border: rgba(19, 32, 40, 0.12);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(15, 118, 110, 0.10), transparent 28%),
            radial-gradient(circle at top right, rgba(180, 83, 9, 0.10), transparent 26%),
            linear-gradient(180deg, #f8f4ec 0%, #f3ede4 100%);
        color: var(--text);
        font-family: "Georgia", "Times New Roman", serif;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
    }

    .hero {
        padding: 1.6rem 1.8rem;
        border: 1px solid var(--border);
        border-radius: 24px;
        background: rgba(255, 250, 241, 0.8);
        backdrop-filter: blur(8px);
        box-shadow: 0 18px 40px rgba(19, 32, 40, 0.08);
    }

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: var(--accent);
        font-size: 0.76rem;
        font-weight: 700;
        margin-bottom: 0.65rem;
    }

    .title {
        font-size: clamp(2rem, 4vw, 3.45rem);
        line-height: 1.02;
        margin: 0;
        color: var(--text);
    }

    .subtitle {
        max-width: 760px;
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.6;
        margin-top: 0.9rem;
    }

    .metric-card,
    .panel {
        background: linear-gradient(180deg, rgba(255,255,255,0.86), rgba(247,239,226,0.8));
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1rem 1.1rem;
        box-shadow: 0 14px 30px rgba(19, 32, 40, 0.06);
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.84rem;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: var(--text);
    }

    .metric-delta {
        color: var(--accent);
        font-size: 0.84rem;
        margin-top: 0.3rem;
    }

    .section-heading {
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0 0 0.6rem 0;
        color: var(--text);
    }

    div[data-testid="stSidebar"] {
        background: rgba(255, 250, 241, 0.95);
        border-right: 1px solid rgba(19, 32, 40, 0.08);
    }

    .footer-note {
        color: var(--muted);
        font-size: 0.88rem;
        margin-top: 1rem;
    }
</style>
"""


@dataclass(frozen=True)
class DashboardData:
    frame: pd.DataFrame
    numeric_columns: list[str]
    categorical_columns: list[str]
    date_column: str | None


def make_demo_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-01-01", periods=240, freq="D")
    regions = ["North", "South", "East", "West"]
    teams = ["Alpha", "Beta", "Gamma"]
    channels = ["Retail", "Online", "Partner"]

    records: list[dict[str, object]] = []
    for idx, date in enumerate(dates):
        region = regions[idx % len(regions)]
        team = teams[idx % len(teams)]
        channel = channels[idx % len(channels)]
        base_volume = 180 + 35 * np.sin(idx / 12.0) + rng.normal(0, 12)
        efficiency = 0.72 + 0.08 * np.cos(idx / 18.0) + rng.normal(0, 0.03)
        response_time = 42 - 7 * efficiency + rng.normal(0, 2.5)
        defects = max(0, int(rng.poisson(2 + (1 - efficiency) * 3)))
        revenue = base_volume * (82 + rng.normal(0, 8))

        if idx in {53, 119, 182}:
            revenue *= 1.35
            response_time *= 1.5
            defects += 6

        records.append(
            {
                "date": date,
                "region": region,
                "team": team,
                "channel": channel,
                "transactions": max(60, int(base_volume)),
                "efficiency_score": round(float(np.clip(efficiency, 0.18, 0.98)), 3),
                "response_time_minutes": round(float(max(response_time, 6.5)), 2),
                "defects": defects,
                "revenue": round(float(max(revenue, 0)), 2),
            }
        )

    return pd.DataFrame.from_records(records)


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if file_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file type. Upload a CSV or Excel file.")


def normalize_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    for column in cleaned.columns:
        if pd.api.types.is_object_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].astype(str).str.strip()
    return cleaned


def detect_columns(frame: pd.DataFrame) -> DashboardData:
    numeric_columns = frame.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = frame.select_dtypes(exclude=[np.number]).columns.tolist()
    date_column = None
    for column in frame.columns:
        if "date" in column.lower() or "time" in column.lower():
            parsed = pd.to_datetime(frame[column], errors="coerce")
            if parsed.notna().mean() > 0.7:
                date_column = column
                break
    return DashboardData(frame=frame, numeric_columns=numeric_columns, categorical_columns=categorical_columns, date_column=date_column)


def convert_datetime_column(frame: pd.DataFrame, column: str | None) -> pd.DataFrame:
    if not column:
        return frame
    converted = frame.copy()
    converted[column] = pd.to_datetime(converted[column], errors="coerce")
    converted = converted.dropna(subset=[column])
    return converted


def filter_dataframe(
    frame: pd.DataFrame,
    date_column: str | None,
    selected_categories: dict[str, Iterable[str]],
    numeric_filters: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    filtered = frame.copy()

    if date_column and pd.api.types.is_datetime64_any_dtype(filtered[date_column]):
        date_min = filtered[date_column].min().date()
        date_max = filtered[date_column].max().date()
        selected_range = st.sidebar.date_input(
            "Date range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
        )
        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start, end = selected_range
            filtered = filtered[(filtered[date_column].dt.date >= start) & (filtered[date_column].dt.date <= end)]

    for column, choices in selected_categories.items():
        if choices:
            filtered = filtered[filtered[column].isin(list(choices))]

    for column, bounds in numeric_filters.items():
        lower, upper = bounds
        filtered = filtered[filtered[column].between(lower, upper)]

    return filtered


def detect_anomalies(frame: pd.DataFrame, metric: str) -> pd.Series:
    series = frame[metric].dropna()
    if series.empty:
        return pd.Series(dtype=bool)
    median = series.median()
    mad = np.median(np.abs(series - median))
    if mad == 0:
        return pd.Series(False, index=frame.index)
    modified_z_score = 0.6745 * (frame[metric] - median) / mad
    return modified_z_score.abs() > 3.5


def create_trend_figure(frame: pd.DataFrame, date_column: str | None, metric: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9.5, 3.6), dpi=150)
    if date_column and pd.api.types.is_datetime64_any_dtype(frame[date_column]):
        trend = frame.sort_values(date_column).set_index(date_column)[metric].rolling(7, min_periods=1).mean()
        ax.plot(trend.index, trend.values, color="#0f766e", linewidth=2.2)
        ax.fill_between(trend.index, trend.values, color="#0f766e", alpha=0.12)
        ax.set_xlabel("Date")
    else:
        ax.plot(frame.index, frame[metric], color="#0f766e", linewidth=2.0)
        ax.set_xlabel("Record")
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_title(f"Trend for {metric.replace('_', ' ').title()}", loc="left", pad=12, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    fig.tight_layout()
    return fig


def build_download(frame: pd.DataFrame) -> bytes:
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def metric_card(label: str, value: str, delta: str) -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta">{delta}</div>
    </div>
    """


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.sidebar.title("Controls")
    st.sidebar.caption("Upload your own dataset or explore a curated demo set.")
    uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

    source_frame = make_demo_data() if uploaded_file is None else load_uploaded_file(uploaded_file)
    source_frame = normalize_dataframe(source_frame)

    dashboard_data = detect_columns(source_frame)
    working_frame = convert_datetime_column(dashboard_data.frame, dashboard_data.date_column)

    if not dashboard_data.numeric_columns:
        st.error("The uploaded dataset does not contain any numeric columns to analyze.")
        st.stop()

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Independent Technical Project</div>
            <h1 class="title">Operational Efficiency & Performance Analytics Dashboard</h1>
            <p class="subtitle">
                A Streamlit dashboard for inspecting operational performance, isolating anomalies,
                and surfacing localized statistics from tabular business data with a clean, report-ready layout.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    category_filters: dict[str, list[str]] = {}
    for column in dashboard_data.categorical_columns[:4]:
        values = sorted(working_frame[column].dropna().astype(str).unique().tolist())
        category_filters[column] = st.sidebar.multiselect(f"{column.title()}", values, default=values[: min(3, len(values))])

    numeric_filters: dict[str, tuple[float, float]] = {}
    for column in dashboard_data.numeric_columns[:3]:
        min_value = float(np.nanmin(working_frame[column]))
        max_value = float(np.nanmax(working_frame[column]))
        numeric_filters[column] = st.sidebar.slider(
            column.replace("_", " ").title(),
            min_value=min_value,
            max_value=max_value,
            value=(min_value, max_value),
        )

    filtered_frame = filter_dataframe(working_frame, dashboard_data.date_column, category_filters, numeric_filters)

    if filtered_frame.empty:
        st.warning("No rows match the current filters. Broaden the selections to continue.")
        st.stop()

    metric_candidates = [column for column in dashboard_data.numeric_columns if column.lower() not in {dashboard_data.date_column or ""}]
    primary_metric = metric_candidates[0] if metric_candidates else dashboard_data.numeric_columns[0]
    anomaly_metric = next((column for column in dashboard_data.numeric_columns if "efficiency" in column.lower()), primary_metric)
    anomalies = detect_anomalies(filtered_frame, anomaly_metric)

    total_rows = len(filtered_frame)
    total_numeric = len(dashboard_data.numeric_columns)
    category_count = len(dashboard_data.categorical_columns)
    anomaly_count = int(anomalies.sum()) if not anomalies.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    cards = [
        metric_card("Filtered records", f"{total_rows:,}", "Current working set"),
        metric_card("Numeric columns", f"{total_numeric}", "Used for summary and filtering"),
        metric_card("Categorical columns", f"{category_count}", "Supports localized breakdowns"),
        metric_card("Anomalies", f"{anomaly_count}", f"Detected in {anomaly_metric.replace('_', ' ')}"),
    ]
    for container, card in zip((col1, col2, col3, col4), cards, strict=True):
        with container:
            st.markdown(card, unsafe_allow_html=True)

    left_col, right_col = st.columns((1.2, 1))
    with left_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Operational trend</div>', unsafe_allow_html=True)
        st.pyplot(create_trend_figure(filtered_frame, dashboard_data.date_column, primary_metric), clear_figure=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Localized statistics</div>', unsafe_allow_html=True)
        grouping_column = dashboard_data.categorical_columns[0] if dashboard_data.categorical_columns else None
        if grouping_column:
            localized = (
                filtered_frame.groupby(grouping_column, dropna=False)
                .agg(records=(primary_metric, "size"), average_metric=(primary_metric, "mean"), total_metric=(primary_metric, "sum"))
                .sort_values("records", ascending=False)
            )
            localized["average_metric"] = localized["average_metric"].round(2)
            st.dataframe(localized, use_container_width=True, height=320)
        else:
            st.info("Add at least one text or category column to unlock localized breakdowns.")
        st.markdown('</div>', unsafe_allow_html=True)

    lower_left, lower_right = st.columns((1, 1))
    with lower_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Anomaly review</div>', unsafe_allow_html=True)
        anomaly_frame = filtered_frame.loc[anomalies].copy() if not anomalies.empty else filtered_frame.head(0).copy()
        if anomaly_frame.empty:
            st.success("No statistical anomalies detected in the current slice.")
        else:
            show_columns = [column for column in [dashboard_data.date_column, anomaly_metric, primary_metric] if column]
            show_columns += [column for column in dashboard_data.categorical_columns[:2] if column not in show_columns]
            st.dataframe(anomaly_frame[show_columns].head(20), use_container_width=True, height=260)
        st.markdown('</div>', unsafe_allow_html=True)

    with lower_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Data preview</div>', unsafe_allow_html=True)
        st.dataframe(filtered_frame.head(25), use_container_width=True, height=320)
        st.markdown('</div>', unsafe_allow_html=True)

    st.download_button(
        label="Download filtered data as CSV",
        data=build_download(filtered_frame),
        file_name="operational_efficiency_filtered_data.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()