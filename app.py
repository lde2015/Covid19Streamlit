# Import des librairies
import Covid19_utils as ut
from datetime import datetime, timedelta, date
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

@st.cache(show_spinner=False)
def get_metadata(local, nb_jours):
    df_type_data, df_new, df_new_agg_reg, dict_labels, geo, df_dept, df_pop_dept = ut.charge_meta(local, nb_jours)
    return df_type_data, df_new, df_new_agg_reg, dict_labels, geo, df_dept, df_pop_dept

@st.cache(show_spinner=False)
def get_data(dte_deb, df_dept, df_pop_dept, df_type_data):
    date_deb = dte_deb.strftime('%d/%m/%Y')
    df_agg_reg, df, df_hors_paris, df_paris, df_age, df_age_nat = ut.charge_data(date_deb, df_dept, df_pop_dept, df_type_data)
    return df_agg_reg, df, df_hors_paris, df_paris, df_age, df_age_nat

def get_data_indic():
    j, tot_hosp_j, tot_rea_j, tot_dc_j, tot_hosp_j_1, tot_rea_j_1, tot_dc_j_1, evol_hosp, evol_rea, evol_dc = ut.charge_data_indic()
    return j, tot_hosp_j, tot_rea_j, tot_dc_j, tot_hosp_j_1, tot_rea_j_1, tot_dc_j_1, evol_hosp, evol_rea, evol_dc

def get_vaccin(df_dept):
    df = ut.charge_data_vaccin()
    taux_glob = np.round(df['n_tot_complet'].sum() * 100 / df['pop'].sum(), 2)
    df = pd.merge(df, df_dept, on='code_departement')
    df['infos'] = df['code_departement'] + " - " + df['nom_departement']

    return taux_glob, df

#############################################################################################################

st.set_page_config(page_title="Covid19", page_icon=None, layout='wide', initial_sidebar_state='auto')

col1, col2 = st.columns([1,4])
with col1:
    st.image('sars-cov-19.jpg')
with col2:
    st.markdown("<h1 style='text-align: center; color: rgb(93,105,177);'>Dashboard Evolution Covid19 en France</h1><br> </br>", unsafe_allow_html=True)


# Chargement des données méta
local = "."
df_type_data, df_new, df_new_agg_reg, dict_labels, geo, df_dept, df_pop_dept = get_metadata(local, 14)

#---------------------------------------------------------------------------------------------------------------

# Chargement des données indicateurs
j, tot_hosp_j, tot_rea_j, tot_dc_j, tot_hosp_j_1, tot_rea_j_1, tot_dc_j_1, evol_hosp, evol_rea, evol_dc = get_data_indic()

#---------------------------------------------------------------------------------------------------------------

lib = "Chiffres en date du "+datetime.strftime(j, '%d/%m/%Y')+" (avec delta par rapport à la veille)"
title_indic = """
                <style>
                    .title h2{
                    user-select: none
                    font-size: 25px;
                    color:rgb(228,26,28);
                    }
                </style>
                <div class="title">
                    <h2><b>"""+lib+"""</b></h2>
                </div>
                """
st.markdown(title_indic, unsafe_allow_html=True)

fig = go.Figure()

fig.add_trace(go.Indicator(
    mode = "number+delta",
    value = tot_hosp_j,
    title={'text': 'Personnes hospitalisées'},
    delta = {'reference': tot_hosp_j_1},
    domain = {'row': 0, 'column': 0}))

fig.add_trace(go.Indicator(
    mode = "number+delta",
    value = tot_rea_j,
    title={'text': 'Personnes en réanimation'},
    delta = {'reference': tot_rea_j_1},
    domain = {'row': 0, 'column': 1}))

fig.add_trace(go.Indicator(
    mode = "number+delta",
    value = tot_dc_j,
    title={'text': 'Personnes décédées'},
    delta = {'reference': tot_dc_j_1},
    domain = {'row': 0, 'column': 2}))

  
fig.update_layout(width=1000, height=170, margin={'l':0},
    grid = {'rows': 1, 'columns': 3, 'pattern': "independent"})

fig.update_traces(delta_decreasing_color='green', delta_increasing_color='red',
                 number_valueformat=",.", delta_valueformat=",.",
                 title_font_size=18, delta_font_size=23, number_font_size=30)


st.plotly_chart(fig)

taux_glob, df_vaccin = get_vaccin(df_dept)


#---------------------------------------------------------------------------------------------------------------

title_vaccin = """
                <style>
                    .title h2{
                    user-select: none;
                    font-size: 25px;
                    color:rgb(228,26,28);
                    }
                </style>
                <div class="title">
                    <h2><b>Taux de couverture vaccinale complète</b></h2>
                </div>
                """
st.markdown(title_vaccin, unsafe_allow_html=True)

#---------------------------------------------------------------------------------------------------------------

with st.expander("Couverture vaccinale complète", expanded=True):
    col1, col2 = st.columns((1, 2))
    with col1:
        fig = go.Figure()

        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = taux_glob,
            title = {'text': "Taux national"},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig.update_layout(width=450, height=400, 
        margin={'l':0})

        fig.update_traces(title_font_size=20,  number_font_size=30)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = ut.plot_vaccin(df_vaccin, geo, local, 'N')
        st.plotly_chart(fig, use_container_width=True)


#---------------------------------------------------------------------------------------------------------------

# Chargement des données
dte_def = datetime.strptime('20032020', "%d%m%Y")
dte_deb_sel = st.date_input('Date de début : ', value=dte_def)
df_agg_reg, df, df_hors_paris, df_paris, df_age, df_age_nat = get_data(dte_deb_sel, df_dept, df_pop_dept, df_type_data)

# Initialisations
list_data = list(df_type_data['type_data'].values)
list_regions = np.sort(df['nom_region'].unique())
now = datetime.now() 
dte_deb = now - timedelta(days=15)
ratio = 100000

#---------------------------------------------------------------------------------------------------------------

title_evol = """
                <style>
                    .title h2{
                    user-select: none;
                    font-size: 25px;
                    color:rgb(228,26,28);
                    }
                </style>
                <div class="title">
                    <h2><b>Evolution des hospitalisations, réanimations, décés</b></h2>
                </div>
                """
st.markdown(title_evol, unsafe_allow_html=True)

#---------------------------------------------------------------------------------------------------------------

with st.expander("Evolution des hospitalisations, réanimations, décés"):
    col1, col2, col3 = st.columns(3)

    with col1:
    ################################################################################################################
    # Evolution par régions
    ################################################################################################################

        with st.form('Form1'):
            title_1 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(228,26,28);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Evolution par régions</b></h4>
                            </div>
                            """
            st.markdown(title_1, unsafe_allow_html=True)

            Donnée = st.selectbox('Donnée', list(df_type_data['type_data'].values))
            Type = st.selectbox('Type', ['En nombre','En ratio'])
            submitted1 = st.form_submit_button('Rafraîchir')
            if submitted1:
                if Type == 'En nombre':
                    fig, colonne = ut.plot_courbes_regions(df_type_data, Donnée, df_agg_reg, dict_labels, local, 'N')
                else:
                    fig, colonne = ut.plot_courbes_regions_ratio(df_type_data, Donnée, df_agg_reg, dict_labels, local, ratio, 'N')
                st.plotly_chart(fig, use_container_width=True)        

    with col2:
    ################################################################################################################
    # Evolution par région et départements
    ################################################################################################################

        with st.form('Form2'):
            title_2 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(228,26,28);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Evolution par région et départements</b></h4>
                            </div>
                            """
            st.markdown(title_2, unsafe_allow_html=True)

            Donnée = st.selectbox('Donnée', list(df_type_data['type_data'].values))
            Type = st.selectbox('Type', ['En nombre','En ratio'])
            submitted2 = st.form_submit_button('Rafraîchir')
            if submitted2:
                if Type == 'En nombre':
                    fig, colonne = ut.plot_courbes_departements_grid(df_type_data, Donnée, df, dict_labels, local, 'N')
                else:
                    fig, colonne = ut.plot_courbes_departements_ratio_grid(df_type_data, Donnée, df, dict_labels, local, ratio, 'N')
                st.plotly_chart(fig, use_container_width=True)


    ################################################################################################################
    # Evolution pour 1 région 
    ################################################################################################################

    with col3:
        with st.form('Form3'):
            title_3 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(228,26,28);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Evolution pour 1 région</b></h4>
                            </div>
                            """
            st.markdown(title_3, unsafe_allow_html=True)

            Région = st.selectbox('Région', list(np.sort(df['nom_region'].unique())))
            Donnée = st.selectbox('Donnée', list(df_type_data['type_data'].values))
            Type = st.selectbox('Type', ['En nombre','En ratio'])
            submitted3 = st.form_submit_button('Rafraîchir')
            if submitted3:
                if Type == 'En nombre':
                    fig, colonne = ut.plot_courbes_departements(df_type_data, Donnée, df[df.nom_region == Région], Région, dict_labels, local, 'N')
                else:
                    fig, colonne = ut.plot_courbes_departements_ratio(df_type_data, Donnée, df[df.nom_region == Région], Région, dict_labels, local, ratio, 'N')
                st.plotly_chart(fig, use_container_width=True)


#---------------------------------------------------------------------------------------------------------------


title_age = """
                <style>
                    .title h2{
                    user-select: none;
                    font-size: 25px;
                    color:rgb(228,26,28);
                    }
                </style>
                <div class="title">
                    <h2><b>Evolution par classe d'âge</b></h2>
                </div>
                """
st.markdown(title_age, unsafe_allow_html=True)

with st.expander("Evolution par classe d'âge"):
    col1, col2 = st.columns(2)

    with col1:
    ################################################################################################################
    # Evolution pour un type de donnée
    ################################################################################################################

        with st.form('FormAge1'):
            title_1 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(228,26,28);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Pour un type de donnée</b></h4>
                            </div>
                            """
            st.markdown(title_1, unsafe_allow_html=True)

            Donnée = st.selectbox('Donnée', list(df_type_data['type_data'].values))
            submitted1 = st.form_submit_button('Rafraîchir')
            if submitted1:
                fig, colonne = ut.plot_donnee_age(df_type_data, Donnée, df_age_nat, dict_labels, local, 'N')
                st.plotly_chart(fig, use_container_width=True)


    ################################################################################################################
    # Evolution par classe d'âge pour 1 région 
    ################################################################################################################

    with col2:
        with st.form('ForAge25'):
            title_2 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(228,26,28);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Pour 1 région</b></h4>
                            </div>
                            """
            st.markdown(title_2, unsafe_allow_html=True)

            Région = st.selectbox('Région', list(np.sort(df['nom_region'].unique())))
            Donnée = st.selectbox('Donnée', list(df_type_data['type_data'].values))
            submitted2 = st.form_submit_button('Rafraîchir')
            if submitted2:
                fig, colonne = ut.plot_age_1region(df_type_data, Donnée, df_age[df_age.nom_region == Région], Région, dict_labels, local, 'N')
                st.plotly_chart(fig, use_container_width=True)




#---------------------------------------------------------------------------------------------------------------


title_new = """
                <style>
                    .title h2{
                    user-select: none;
                    font-size: 25px;
                    color:rgb(228,26,28);
                    }
                </style>
                <div class="title">
                    <h2><b>Evolution des nouveaux cas</b></h2>
                </div>
                """
st.markdown(title_new, unsafe_allow_html=True)

with st.expander("Evolution des nouveaux cas"):
    col1, col2 = st.columns(2)

    with col1:
    ################################################################################################################
    # Evolution des nouveaux cas par région
    ################################################################################################################

        with st.form('Form4'):
            title_1 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(228,26,28);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Par région</b></h4>
                            </div>
                            """
            st.markdown(title_1, unsafe_allow_html=True)

            zone = st.selectbox('Zone', ['Tout', 'Hors Paris', 'Paris'])
            submitted1 = st.form_submit_button('Rafraîchir')
            if submitted1:
                fig = ut.plot_heatmap_regions(df_new_agg_reg, local, zone, 'N')
                st.plotly_chart(fig, use_container_width=True)


    ################################################################################################################
    # Evolution des nouveaux cas pour 1 région 
    ################################################################################################################

    with col2:
        with st.form('Form5'):
            title_2 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(228,26,28);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Pour 1 région</b></h4>
                            </div>
                            """
            st.markdown(title_2, unsafe_allow_html=True)

            Région = st.selectbox('Région', list(np.sort(df['nom_region'].unique())))
            submitted2 = st.form_submit_button('Rafraîchir')
            if submitted2:
                fig = ut.plot_heatmap_1region(df_new[df_new.nom_region == Région], Région, local, 'N')
                st.plotly_chart(fig, use_container_width=True)



#---------------------------------------------------------------------------------------------------------------


title_geo = """
                <style>
                    .title h2{
                    user-select: none;
                    font-size: 25px;
                    color:rgb(228,26,28);
                    }
                </style>
                <div class="title">
                    <h2><b>Vue géographique de l'évolution</b></h2>
                </div>
                """
st.markdown(title_geo, unsafe_allow_html=True)

with st.expander("Vue géographique de l'évolution"):
    ################################################################################################################
    # Vue géographique
    ################################################################################################################

        with st.form('Form6'):
            title_1 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(228,26,28);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Vue géographique de l'évolution</b></h4>
                            </div>
                            """
            st.markdown(title_1, unsafe_allow_html=True)

            Donnée = st.selectbox('Donnée', list(df_type_data['type_data'].values))
            Zone = st.selectbox('Zone', ['Tout', 'Hors Paris', 'Paris'])
            Type = st.selectbox('Type', ['En nombre','En ratio'])

            submitted1 = st.form_submit_button('Rafraîchir')
            if submitted1:
                if Type == 'En nombre':
                    df_plot = pd.concat([df_hors_paris, df_paris], ignore_index=True)
                    fig, colonne = ut.plot_carte(df_type_data, dte_deb, Donnée, Zone, df_hors_paris, df_paris, geo, local, 'N')
                else:
                    fig, colonne = ut.plot_carte_ratio(df_type_data, dte_deb, Donnée, Zone, df_hors_paris, df_paris, geo, local, ratio, 'N')
                st.plotly_chart(fig, use_container_width=True)

st.image('img_source.png')
