import pandas as pd
import json
import streamlit as st

# Load JSON
def load_data():
    with open("output.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# Normalize into relational-like tables
players_df = pd.json_normalize(data)

stats_records, gamestats_records = [], []
for player in data:
    pid = player.get("player_id")
    for s in player.get("stats", []):
        s["player_id"] = pid
        stats_records.append(s)
    for g in player.get("gamestats", []):
        g["player_id"] = pid
        gamestats_records.append(g)

stats_df = pd.DataFrame(stats_records)
gamestats_df = pd.DataFrame(gamestats_records)

# Map player_id -> name
id_to_name = dict(zip(players_df["player_id"], players_df["name"]))
stats_df["player_name"] = stats_df["player_id"].map(id_to_name)
gamestats_df["player_name"] = gamestats_df["player_id"].map(id_to_name)

# --- Streamlit UI ---
st.set_page_config(page_title="Player Stats Dashboard", layout="wide")
st.title("⚽ Manuel ti voglio bene <3")

# Sidebar filters
teams = players_df["team_name_short"].dropna().unique()
selected_team = st.sidebar.selectbox("Select Team", ["All"] + list(teams))

seasons = stats_df["season"].dropna().unique()
selected_season = st.sidebar.selectbox("Select Season", ["All"] + list(seasons))

# Filtered view
filtered_players = players_df.copy()
if selected_team != "All":
    filtered_players = filtered_players[filtered_players["team_name_short"] == selected_team]

filtered_stats = stats_df.copy()
if selected_season != "All":
    filtered_stats = filtered_stats[filtered_stats["season"] == selected_season]

# Display tables
st.subheader("Players")
st.dataframe(filtered_players[["name", "role", "team_name_short", "country", "height"]])

st.subheader("Stats")
st.dataframe(filtered_stats[["player_name", "season", "tournament_name", "presenze", "gf", "assist", "min_playing_time"]])

# --- Example statistics ---
st.subheader("Statistics")

col1, col2 = st.columns(2)

with col1:
    top_scorers = filtered_stats.groupby("player_name")["gf"].sum().sort_values(ascending=False).head(10)
    st.write("Top Scorers")
    st.bar_chart(top_scorers)

with col2:
    if "assist" in filtered_stats.columns:
        top_assist = filtered_stats.groupby("player_name")["assist"].sum().sort_values(ascending=False).head(10)
        st.write("Top Assists")
        st.bar_chart(top_assist)

# Helper function for colored index display
def index_badge(label, value):
    if pd.isna(value):
        color, level = "grey", "-"
    elif value <= 2:
        color, level = "red", "Low"
    elif value == 3:
        color, level = "yellow", "Mid"
    else:
        color, level = "green", "High"
    st.markdown(f"<div style='padding:6px;border-radius:6px;background-color:{color};color:black;text-align:center;'>"
                f"<b>{label}:</b> {level} ({value})</div>", unsafe_allow_html=True)

# Player detail drill-down
st.subheader("Dettagli (Manuel tvb <3)")
player_list = filtered_players["name"].dropna().unique()
selected_player = st.selectbox("Choose a Player", player_list)

if selected_player:
    pid = filtered_players.loc[filtered_players["name"] == selected_player, "player_id"].iloc[0]
    player_stats = stats_df[stats_df["player_id"] == pid]
    player_games = gamestats_df[gamestats_df["player_id"] == pid]
    player_row = players_df[players_df["player_id"] == pid].iloc[0]

    # Show SOS Fanta Comment
    if "comment" in player_row and pd.notna(player_row["comment"]):
        st.markdown(f"**Commento SOS Fanta:** {player_row['comment']}")

    # Show Indices (Affidabilità, Titolarità, Integrità)
    st.markdown("### Indici Giocatore")
    c1, c2, c3 = st.columns(3)
    with c1:
        index_badge("Affidabilità", player_row.get("aff_index"))
    with c2:
        index_badge("Titolarità", player_row.get("tit_index"))
    with c3:
        index_badge("Integrità", player_row.get("inf_index"))

    if not player_stats.empty:
        presenze = player_stats["presenze"].sum()
        gf = player_stats["gf"].sum()
        assist = player_stats["assist"].sum()
        amm = player_stats["amm"].sum() if "amm" in player_stats else 0
        esp = player_stats["esp"].sum() if "esp" in player_stats else 0
        minutes = player_stats["min_playing_time"].sum()

        # Fantacalcio
        mv = player_games["vote"].mean() if "vote" in player_games else None
        fmv = player_games["vote"].mean() if "vote" in player_games else None  # simplified
        mv_last5 = player_games.tail(5)["vote"].mean() if "vote" in player_games else None
        fmv_last5 = mv_last5
        perc_voto6 = (player_games["vote"] >= 6).mean() * 100 if "vote" in player_games else None
        perc_voto65 = (player_games["vote"] >= 6.5).mean() * 100 if "vote" in player_games else None

        # Generali
        minuti_a_partita = minutes / presenze if presenze else 0
        precisione_passaggi = player_stats["accurate_passes_percentage"].mean()

        # Offensive
        tiri_a_partita = player_stats["total_shots"].sum() / presenze if presenze else 0
        tiri_in_porta = player_stats["shots_on_target"].sum() / presenze if presenze else 0
        gol_su_tiri = (gf / player_stats["total_shots"].sum()) * 100 if player_stats["total_shots"].sum() else 0
        gol_testa = player_stats["headed_goals"].sum()
        occasioni_mancate = player_stats["big_chances_missed"].sum()
        passaggi_chiave = player_stats["key_passes"].sum() / presenze if presenze else 0
        dribbling_success = player_stats["successful_dribbles_percentage"].mean()

        # Difensive
        cartellini_tot = amm + esp
        cartellini_a_partita = cartellini_tot / presenze if presenze else 0
        falli = player_stats["fouls"].sum() / presenze if presenze else 0
        palle_perse = player_stats["possession_lost"].sum() / presenze if presenze else 0
        recuperi = player_stats["interceptions"].sum() / presenze if presenze else 0
        duelli_vinti = player_stats["total_duels_won"].sum() / presenze if presenze else 0
        duelli_aerei = player_stats["aerial_duels_won"].sum() / presenze if presenze else 0

        # Layout
        st.markdown("### Player Dashboard")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.write("**Fantacalcio**")
            st.metric("MV", round(mv,2) if mv else "-")
            st.metric("FMV", round(fmv,2) if fmv else "-")
            st.metric("MV Ultime 5", round(mv_last5,2) if mv_last5 else "-")
            st.metric("FMV Ultime 5", round(fmv_last5,2) if fmv_last5 else "-")
            st.metric("% Partite Voto >= 6", f"{perc_voto6:.1f}%" if perc_voto6 else "-")
            st.metric("% Partite Voto >= 6.5", f"{perc_voto65:.1f}%" if perc_voto65 else "-")

        with c2:
            st.write("**Generali**")
            st.metric("Gol Totali", gf)
            st.metric("Assist Totali", assist)
            st.metric("Partite A Voto", len(player_games))
            st.metric("Partite Da Titolare", player_stats["starts_eleven"].sum())
            st.metric("Minuti A Partita", round(minuti_a_partita,1))
            st.metric("Precisione Passaggi", f"{precisione_passaggi:.1f}%")

        with c3:
            st.write("**Offensive**")
            st.metric("Tiri a Partita", round(tiri_a_partita,2))
            st.metric("Tiri in Porta/Partita", round(tiri_in_porta,2))
            st.metric("% Gol su Tiri", f"{gol_su_tiri:.1f}%")
            st.metric("Gol di Testa", gol_testa)
            st.metric("Occasioni Mancate", occasioni_mancate)
            st.metric("Passaggi Chiave/Partita", round(passaggi_chiave,2))
            st.metric("% Dribbling Riusciti", f"{dribbling_success:.1f}%")

        with c4:
            st.write("**Difensive**")
            st.metric("Cartellini a Partita", round(cartellini_a_partita,2))
            st.metric("Numero di Cartellini", cartellini_tot)
            st.metric("Falli a Partita", round(falli,2))
            st.metric("Palle Perse a Partita", round(palle_perse,2))
            st.metric("Recuperi a Partita", round(recuperi,2))
            st.metric("Duelli Vinti a Partita", round(duelli_vinti,2))
            st.metric("Duelli Aerei a Partita", round(duelli_aerei,2))

    # Show raw tables below
    st.write("### Season Stats (raw) (se proprio vuoi i dettagli come mammalab li ha fatti)")
    st.dataframe(player_stats.drop(columns=["player_id"]))
    if not player_games.empty:
        st.write("### Matchday Stats (raw) (specifico match)")
        st.dataframe(player_games.drop(columns=["player_id"]))
