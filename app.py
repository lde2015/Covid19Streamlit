# Import des librairies
from ipywidgets import interact, interact_manual
import Covid19_utils as ut
from datetime import datetime, timedelta
import numpy as np
import streamlit as st

@st.cache(show_spinner=False)
def get_metadata(local, nb_jours):
    df_type_data, df_new, df_new_agg_reg, dict_labels, geo, df_dept, df_pop_dept = ut.charge_meta(local, nb_jours)
    return df_type_data, df_new, df_new_agg_reg, dict_labels, geo, df_dept, df_pop_dept

@st.cache(show_spinner=False)
def get_data(dte_deb, df_dept, df_pop_dept):
    date_deb = dte_deb.strftime('%d/%m/%Y')
    df_agg_reg, df, df_hors_paris, df_paris = ut.charge_data(date_deb, df_dept, df_pop_dept)
    return df_agg_reg, df, df_hors_paris, df_paris


#############################################################################################################

st.set_page_config(page_title="Covid19", page_icon=None, layout='wide', initial_sidebar_state='auto')

st.image('img_titre.jpg')
#st.markdown("<h1 style='text-align: center; color: black;'>Dashboard Evolution Covid19 en France</h1><br> </br>", unsafe_allow_html=True)


# Chargement des données
local = "."
df_type_data, df_new, df_new_agg_reg, dict_labels, geo, df_dept, df_pop_dept = get_metadata(local, 14)

dte_def = datetime.strptime('20032020', "%d%m%Y")
dte_deb_sel = st.date_input('Date de début : ', value=dte_def)
df_agg_reg, df, df_hors_paris, df_paris = get_data(dte_deb_sel, df_dept, df_pop_dept)

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
                    color:rgb(253,83,0);
                    }
                </style>
                <div class="title">
                    <h2><b>Evolution des hospitalisations, réanimations, décés</b></h2>
                </div>
                """
st.markdown(title_evol, unsafe_allow_html=True)

#---------------------------------------------------------------------------------------------------------------

with st.beta_expander("Evolution des hospitalisations, réanimations, décés"):
    col1, col2, col3 = st.beta_columns(3)

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
                                color:rgb(253,83,0);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Evolution par régions</b></h4>
                            </div>
                            """
            st.markdown(title_1, unsafe_allow_html=True)

            Donnée = st.selectbox('Donnée', list(df_type_data['type_data'].values))
            Type = st.selectbox('Type', ['En nombre','En ratio'])
            submitted1 = st.form_submit_button('Submit')
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
                                color:rgb(253,83,0);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Evolution par région et départements</b></h4>
                            </div>
                            """
            st.markdown(title_2, unsafe_allow_html=True)

            Donnée = st.selectbox('Donnée', list(df_type_data['type_data'].values))
            Type = st.selectbox('Type', ['En nombre','En ratio'])
            submitted2 = st.form_submit_button('Submit')
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
                                color:rgb(253,83,0);
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
            submitted3 = st.form_submit_button('Submit')
            if submitted3:
                if Type == 'En nombre':
                    fig, colonne = ut.plot_courbes_departements(df_type_data, Donnée, df[df.nom_region == Région], Région, dict_labels, local, 'N')
                else:
                    fig, colonne = ut.plot_courbes_departements_ratio(df_type_data, Donnée, df[df.nom_region == Région], Région, dict_labels, local, ratio, 'N')
                st.plotly_chart(fig, use_container_width=True)


#---------------------------------------------------------------------------------------------------------------


title_new = """
                <style>
                    .title h2{
                    user-select: none;
                    font-size: 25px;
                    color:rgb(253,83,0);
                    }
                </style>
                <div class="title">
                    <h2><b>Evolution des nouveaux cas</b></h2>
                </div>
                """
st.markdown(title_new, unsafe_allow_html=True)

with st.beta_expander("Evolution des nouveaux cas"):
    col1, col2 = st.beta_columns(2)

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
                                color:rgb(253,83,0);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Par région</b></h4>
                            </div>
                            """
            st.markdown(title_1, unsafe_allow_html=True)

            zone = st.selectbox('Zone', ['Tout', 'Hors Paris', 'Paris'])
            submitted1 = st.form_submit_button('Submit')
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
                                color:rgb(253,83,0);
                                }
                            </style>

                            <div class="title">
                                <h4><b>Pour 1 région</b></h4>
                            </div>
                            """
            st.markdown(title_2, unsafe_allow_html=True)

            Région = st.selectbox('Région', list(np.sort(df['nom_region'].unique())))
            submitted2 = st.form_submit_button('Submit')
            if submitted2:
                fig = ut.plot_heatmap_1region(df_new[df_new.nom_region == Région], Région, local, 'N')
                st.plotly_chart(fig, use_container_width=True)



#---------------------------------------------------------------------------------------------------------------


title_geo = """
                <style>
                    .title h2{
                    user-select: none;
                    font-size: 25px;
                    color:rgb(253,83,0);
                    }
                </style>
                <div class="title">
                    <h2><b>Vue géographique de l'évolution</b></h2>
                </div>
                """
st.markdown(title_new, unsafe_allow_html=True)

with st.beta_expander("Vue géographique de l'évolution"):
    ################################################################################################################
    # Vue géographique
    ################################################################################################################

        with st.form('Form6'):
            title_1 = """
                            <style>
                                .title h4{
                                user-select: none;
                                font-size: 20px;
                                color:rgb(253,83,0);
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

            submitted1 = st.form_submit_button('Submit')
            if submitted1:
                if Type == 'En nombre':
                    fig, colonne = ut.plot_carte(df_type_data, dte_deb, Donnée, Zone, df_hors_paris, df_paris, geo, local, 'N')
                else:
                    fig, colonne = ut.plot_carte_ratio(df_type_data, dte_deb, Donnée, Zone, df_hors_paris, df_paris, geo, local, ratio, 'N')
                st.plotly_chart(fig, use_container_width=True)

st.image('img_source.png')