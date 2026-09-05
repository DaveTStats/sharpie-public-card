"""Public, read-only Scout research board and mobile presentation."""
from pathlib import Path
import pandas as pd
import streamlit as st


def mobile_style():
    st.markdown('''<style>
    .stApp {background:#101513;color:#f1f6f2;}
    .block-container {max-width:1120px;padding:1rem 1rem 3rem;}
    .stApp p,.stApp label,[data-testid="stCaptionContainer"] {color:#cbd8d0;}
    h1,h2,h3 {color:#ffe081!important;letter-spacing:0!important;}
    .hero,.sharpie-stage {background:#17231e!important;box-shadow:none!important;border-color:#365346!important;border-radius:8px!important;}
    .pick,.hold-card,.card,.roi-card {border-radius:8px!important;box-shadow:none!important;background:#17201b!important;}
    .pick.locked {border-left:5px solid #78e09d!important;}
    .hold-card {border-left:5px solid #ffe081!important;}
    [data-baseweb="tab-list"] {gap:8px;flex-wrap:wrap;height:auto!important;padding:10px 0;}
    [data-baseweb="tab"] {background:#203c2b!important;color:#c4ebce!important;border:1px solid #42694f!important;border-radius:999px!important;padding:9px 16px!important;height:42px!important;}
    [data-baseweb="tab"][aria-selected="true"] {background:#9becae!important;color:#102315!important;}
    [data-baseweb="tab-highlight"],[data-baseweb="tab-border"] {display:none;}
    [data-testid="stMetricLabel"] p {color:#ffe081!important;}
    [data-testid="stMetricValue"] {font-size:1.65rem!important;color:#f1f6f2!important;}
    .big {overflow-wrap:anywhere;font-size:1.55rem!important;line-height:1.45!important;}
    .status-badge,.sol-badge {white-space:normal;line-height:1.5;}
    @media(max-width:600px){
      .block-container{padding:.6rem .75rem 2rem;}
      .sharpie-stage{min-height:210px!important;height:auto!important;}
      .sharpie-bubbles{display:none!important;}
      .pick,.hold-card{padding:14px!important;}
      [data-baseweb="tab"]{font-size:.84rem!important;padding:8px 12px!important;}
      [data-testid="stMetricValue"]{font-size:1.35rem!important;}
    }
    @media(prefers-reduced-motion:reduce){*{animation:none!important;}}
    </style>''',unsafe_allow_html=True)


def read(path):
    try:
        return pd.read_csv(path)
    except (FileNotFoundError,pd.errors.EmptyDataError):
        return pd.DataFrame()


def render_scout(root):
    folder=Path(root)/'outputs/astra_validation'
    st.subheader('Scout | Research Dugout')
    st.caption('Independent challenger • paper selections • Astra research')
    boards=sorted(folder.glob('shadow_*.csv'),reverse=True)
    if not boards:
        st.info('Scout is waiting for its first daily research board.')
        return
    dates={p.stem.removeprefix('shadow_'):p for p in boards}
    day=st.selectbox('Board date',list(dates),key='scout_date')
    board=read(dates[day])
    if board.empty:
        st.info('No research candidates recorded for this date.')
        return
    st.warning('Research only. This snapshot has not been verified as pregame, and Scout has not earned promotion to live picks.')
    st.caption('Captured '+str(board.captured_at_utc.iloc[0])+' | '+str(board.version.iloc[0]))
    query=st.text_input('Find a hitter or team',placeholder='Player, team, or opponent',key='scout_search')
    ordering=st.radio('Rank by',['Estimated value','Hit probability'],horizontal=True,key='scout_sort')
    positive=st.toggle('Positive estimated value only',value=True,key='scout_positive')
    view=board.copy()
    if positive:
        view=view[view.astra_ev.gt(0)]
    if query:
        text=view[['player','team','opponent']].fillna('').agg(' '.join,axis=1)
        view=view[text.str.contains(query,case=False,regex=False)]
    view=view.sort_values('astra_ev' if ordering=='Estimated value' else 'astra_probability',ascending=False)
    st.caption(f'{len(view)} matching hitters. Rankings below reflect the selected sort; no wagers are committed.')
    for i,(_,row) in enumerate(view.head(5).iterrows(),1):
        with st.container(border=True):
            st.markdown(f'**{i}. {str(row.player).title()} | {str(row.team).upper()} vs {str(row.opponent).upper()}**')
            st.caption('PAPER WATCH • '+day)
            a,b,c=st.columns(3)
            a.metric('Hit estimate',f'{row.astra_probability:.1%}')
            b.metric('Saved odds',f'{row.odds:+.0f}')
            c.metric('Estimated EV',f'{row.astra_ev:+.1%}')
            st.progress(float(max(0,min(1,row.astra_probability))))
            with st.expander('Scout’s read'):
                st.write('This estimate blends the market probability with the calibrated model average. Historical calibration uses earlier settled games. Positive estimated value means the estimate exceeds the saved price’s break-even probability; it does not establish a profitable bet.')
    st.subheader('Compare Hitters')
    names=st.multiselect('Compare up to three',board.player.tolist(),max_selections=3,key='scout_compare')
    if names:
        comp=board[board.player.isin(names)].set_index('player')
        st.bar_chart(comp[['astra_probability']])
        st.dataframe(comp[['team','opponent','odds','astra_ev']],use_container_width=True)
    with st.expander('Price and return calculator'):
        price=st.number_input('American odds',value=-200,step=5,key='scout_odds')
        stake=st.number_input('Hypothetical stake ($)',min_value=0.,value=10.,step=1.,key='scout_stake')
        if abs(price)<100:
            st.info('Enter valid American odds: -100 or shorter, or +100 or longer.')
        else:
            payout=100/-price if price<0 else price/100
            st.write(f'Break-even hit rate: {1/(1+payout):.1%}. Profit on a win: ${stake*payout:.2f}. Loss on a miss: ${stake:.2f}.')
    st.subheader('Research Scoreboard')
    comparison=read(folder/'model_comparison.csv')
    sizing=read(folder/'sizing_scenarios.csv')
    if len(comparison):
        st.caption('Retrospective probability error. Lower Brier score is better. Historical feature timing is unverified.')
        st.bar_chart(comparison.set_index('model').brier)
    if len(sizing):
        st.caption('Hypothetical $100 bankroll replay, not live results.')
        st.dataframe(sizing,use_container_width=True,hide_index=True)
    st.download_button('Download saved board',board.to_csv(index=False),file_name=f'scout_{day}.csv',mime='text/csv')
