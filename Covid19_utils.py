import pandas as pd
import json
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests
import io


#----------------------------------------------------------------------------------------------------------------------------
# Chargement des meta données
def charge_meta(local, nb_jours, ratio=10000):
    # Source : # Source : https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/

    # Les méta données
    lib_ratio = s='{:,}'.format(ratio).replace(',', '.')

    df_type_data = pd.DataFrame({#'colonne': ['hosp','rea','rad','dc'], 
                                 'colonne': ['hosp','rea','dc'], 
                                'type_data': ['Nb actuellement hospitalisés',
                                            'Nb actuellement en réanimation',
                                          #  'Nb cumulé de retours à domicile',
                                            "Nb cumulé de décés à l'hôpital"]})
    dict_labels = {'legend':'Région - Département', 'nom_region':'Région', 'nom_departement': 'Département',
                'date':'Date', 'hosp':'Nb actuellement hospitalisés','rea':'Nb actuellement en réanimation',
                'rad':'Nb cumulé de retours à domicile','dc':"Nb cumulé de décés à l'hôpital",
                'hosp_ratio':"Ratio /"+lib_ratio+" hospitalisés", 'rea_ratio':"Ratio /"+lib_ratio+" en réanimation",
                'dc_ratio':"Ratio /"+lib_ratio+" décédés", 'cl_age90': "Classe d'âge", 
                'hosp_pct': "Part de la classe d'âge", 'rea_pct': "Part de la classe d'âge", 
                'dc_pct': "Part de la classe d'âge"}

    # Les nouveaux cas depuis 15 jours
    url = "https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c"
    content = requests.get(url).content
    df_new = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
    df_new['date'] = pd.to_datetime(df_new['jour'], format='%Y-%m-%d')

    #-------------------------------------------------------------------------------------------------------------------
    # Source : https://www.data.gouv.fr/fr/datasets/r/1c31f420-829e-489e-a19d-36cf3ef57e4a
    # Les données départements
    df_dept = pd.read_csv(local+'/Data/departements-france.csv')

    #-------------------------------------------------------------------------------------------------------------------
    # Source : https://www.insee.fr/fr/statistiques/1893198
    # La population, par département
    df_pop_dept = pd.read_csv(local+'/Data/population_dept.csv', sep=';')

    #-------------------------------------------------------------------------------------------------------------------
    # Source : https://github.com/gregoiredavid/france-geojson/blob/master/departements.geojson
    with open(local+'/Data/dept.json') as jsonfile:
        geo = json.load(jsonfile)

    # Incorporation des infos départements au dataframe de données
    df_new = pd.merge(df_new, df_dept, left_on='dep', right_on='code_departement', how='left')
    df_new['infos_dept'] = df_new['code_departement'] + " " + df_new['nom_departement']

    df_new_agg_reg = df_new[['nom_region','date','incid_hosp','incid_rea','incid_dc']].groupby(['nom_region','date']).aggregate('sum').reset_index()
    date_deb = df_new_agg_reg['date'].max() - timedelta(days=nb_jours)
    df_new = df_new[df_new.date >= date_deb]
    df_new_agg_reg = df_new_agg_reg[df_new_agg_reg.date >= date_deb]

    return df_type_data, df_new, df_new_agg_reg, dict_labels, geo, df_dept, df_pop_dept

#----------------------------------------------------------------------------------------------------------------------------
# Chargement des données indicateurs
def charge_data_indic():
    
    # Les données hospitalières
    url = "https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7"
    content = requests.get(url).content
    df = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
    df = df[df.sexe == 0] # On ne considère que le niveau global

    df.dropna(inplace=True)
    #df['test'] = df['jour'].apply(lambda x: np.where(x[:4] == '2020', True, False))
    #df1 = df[df.test]
    #df2 = df[~df.test]
    #df1['date'] = pd.to_datetime(df1['jour'], format='%Y-%m-%d')
    #df2['date'] = pd.to_datetime(df2['jour'], format='%d/%m/%Y')
    #df = pd.concat([df1, df2]).sort_index()

    df['date'] = pd.to_datetime(df['jour'], format='%Y-%m-%d')
    max_dte = df['date'].max()

    j = pd.Timestamp(date.today() - timedelta(days=1))
    j_1 = pd.Timestamp(date.today() - timedelta(days=2))

    tot_hosp_j = df[df.date == j]['hosp'].sum()
    tot_rea_j = df[df.date == j]['rea'].sum()
    tot_dc_j = df[df.date == j]['dc'].sum()
    tot_hosp_j_1 = df[df.date == j_1]['hosp'].sum()
    tot_rea_j_1 = df[df.date == j_1]['rea'].sum()
    tot_dc_j_1 = df[df.date == j_1]['dc'].sum()
    evol_hosp = tot_hosp_j - tot_hosp_j_1
    evol_rea = tot_rea_j - tot_rea_j_1
    evol_dc = tot_dc_j - tot_dc_j_1

    return max_dte, tot_hosp_j, tot_rea_j, tot_dc_j, tot_hosp_j_1, tot_rea_j_1, tot_dc_j_1, evol_hosp, evol_rea, evol_dc

#----------------------------------------------------------------------------------------------------------------------------
# Chargement des données sur la couverture vaccinale
def charge_data_vaccin():
    url = "https://www.data.gouv.fr/fr/datasets/r/7969c06d-848e-40cf-9c3c-21b5bd5a874b"
    content = requests.get(url).content
    df = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
    df.rename(columns={'dep' : 'code_departement'}, inplace=True)
    return df

#----------------------------------------------------------------------------------------------------------------------------
# Chargement des données
def charge_data(date_deb, df_dept, df_pop_dept, df_type_data, ratio=10000):
    dte_deb = pd.to_datetime(date_deb, format='%d/%m/%Y')
    
    # Les données hospitalières
    url = "https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7"
    content = requests.get(url).content
    df = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
    df = df[df.sexe == 0] # On ne considère que le niveau global

    df.dropna(inplace=True)
    #df['test'] = df['jour'].apply(lambda x: np.where(x[:4] == '2020', True, False))
    #df1 = df[df.test]
    #df2 = df[~df.test]
    #df1['date'] = pd.to_datetime(df1['jour'], format='%Y-%m-%d')
    #df2['date'] = pd.to_datetime(df2['jour'], format='%d/%m/%Y')
    #df = pd.concat([df1, df2]).sort_index()

    df['date'] = pd.to_datetime(df['jour'], format='%Y-%m-%d')
    df = df[df.date >= dte_deb]

    # Incorporation des infos départements au dataframe de données
    df = pd.merge(df, df_dept, left_on='dep', right_on='code_departement', how='left')
    df = pd.merge(df, df_pop_dept[['dept','population']], left_on='dep', right_on='dept', how='left')
    df.drop(columns=['dep','sexe','dept'], axis=1, inplace=True)
    df['infos'] = df['code_departement'] + " " + df['nom_departement'] + " (" + df['nom_region'] + ")"
    df['legend'] = df['nom_region'] + " - " + df['nom_departement']
    
    df.dropna(inplace=True)
    df['hosp_ratio'] = df.apply(lambda x: np.round(x['hosp']*ratio/x['population'], 2), axis=1)
    df['rea_ratio'] = df.apply(lambda x: np.round(x['rea']*ratio/x['population'], 2), axis=1)
    df['rad_ratio'] = df.apply(lambda x: np.round(x['rad']*ratio/x['population'], 2), axis=1)
    df['dc_ratio'] = df.apply(lambda x: np.round(x['dc']*ratio/x['population'], 2), axis=1)

    # Séparation Paris / hors Paris
    df_hors_paris = df[df['nom_region'] != "Ile-de-France"]
    df_paris = df[df['nom_region'] == "Ile-de-France"]

    # Aggrégation niveau régions
    df_agg_reg = df[['nom_region','date','hosp','rea','rad','dc','population']].groupby(['nom_region','date']).aggregate('sum').reset_index()
    #regions = list(df_agg_reg['nom_region'].unique())

    df_agg_reg['hosp_ratio'] = df_agg_reg.apply(lambda x: np.round(x['hosp']*ratio/x['population'], 2), axis=1)
    df_agg_reg['rea_ratio'] = df_agg_reg.apply(lambda x: np.round(x['rea']*ratio/x['population'], 2), axis=1)
    df_agg_reg['rad_ratio'] = df_agg_reg.apply(lambda x: np.round(x['rad']*ratio/x['population'], 2), axis=1)
    df_agg_reg['dc_ratio'] = df_agg_reg.apply(lambda x: np.round(x['dc']*ratio/x['population'], 2), axis=1)

    # Les données par régions et tranches d'âge
    url = "https://www.data.gouv.fr/fr/datasets/r/08c18e08-6780-452d-9b8c-ae244ad529b3"
    content = requests.get(url).content
    df_trav = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
    df_trav['date'] = pd.to_datetime(df_trav['jour'], format='%Y-%m-%d')
    df_trav = df_trav[df_trav.date >= dte_deb]

    # Constitution du dataframe des régions
    df_reg = df_dept[['code_region', 'nom_region']].drop_duplicates() \
                                            .rename(columns={'code_region': 'reg'}) \
                                            .reset_index(drop=True)

    df_age_glob = df_trav[df_trav.cl_age90 != 0][['reg', 'date', 'hosp', 'rea', 'dc']] \
                                .groupby(['reg', 'date']) \
                                .agg('sum') \
                                .rename(columns={'hosp': 'hosp_glob', 'rea': 'rea_glob', 'dc': 'dc_glob'}) \
                                .reset_index()

    df_age_glob_nat = df_trav[df_trav.cl_age90 != 0][['date', 'hosp', 'rea', 'dc']] \
                                .groupby(['date']) \
                                .agg('sum') \
                                .rename(columns={'hosp': 'hosp_glob', 'rea': 'rea_glob', 'dc': 'dc_glob'}) \
                            .reset_index()

    df_age = df_trav[df_trav.cl_age90 != 0][['reg', 'cl_age90', 'date', 'hosp', 'rea', 'dc']]
    df_age_nat = df_trav[df_trav.cl_age90 != 0][['date', 'cl_age90', 'hosp', 'rea', 'dc']] \
                                .groupby(['date', 'cl_age90']) \
                                .agg('sum') \
                                .reset_index()
    df_age = pd.merge(df_age, df_age_glob, on=['reg', 'date'], how='left')   
    df_age_nat = pd.merge(df_age_nat, df_age_glob_nat, on=['date'], how='left')   

    df_age['cl_age90'] = df_age['cl_age90'].astype('str')
    df_age['cl_age90'].replace('9', '0-9 ans', inplace=True)
    df_age['cl_age90'].replace('19', '10-19 ans', inplace=True)
    df_age['cl_age90'].replace('29', '20-29 ans', inplace=True)
    df_age['cl_age90'].replace('39', '30-39 ans', inplace=True)
    df_age['cl_age90'].replace('49', '40-49 ans', inplace=True)
    df_age['cl_age90'].replace('59', '50-59 ans', inplace=True)
    df_age['cl_age90'].replace('69', '60-69 ans', inplace=True)
    df_age['cl_age90'].replace('79', '70-79 ans', inplace=True)
    df_age['cl_age90'].replace('89', '80-89 ans', inplace=True)
    df_age['cl_age90'].replace('90', '90 ans et plus', inplace=True)    

    df_age_nat['cl_age90'] = df_age_nat['cl_age90'].astype('str')
    df_age_nat['cl_age90'].replace('9', '0-9 ans', inplace=True)
    df_age_nat['cl_age90'].replace('19', '10-19 ans', inplace=True)
    df_age_nat['cl_age90'].replace('29', '20-29 ans', inplace=True)
    df_age_nat['cl_age90'].replace('39', '30-39 ans', inplace=True)
    df_age_nat['cl_age90'].replace('49', '40-49 ans', inplace=True)
    df_age_nat['cl_age90'].replace('59', '50-59 ans', inplace=True)
    df_age_nat['cl_age90'].replace('69', '60-69 ans', inplace=True)
    df_age_nat['cl_age90'].replace('79', '70-79 ans', inplace=True)
    df_age_nat['cl_age90'].replace('89', '80-89 ans', inplace=True)
    df_age_nat['cl_age90'].replace('90', '90 ans et plus', inplace=True)

    for ind, colonne in df_type_data.iterrows():
        col = colonne['colonne']
        col_pct = col + '_pct'
        col_dsp = 'dsp_col_' + col_pct
        col_glob = col + '_glob'
        df_age[col_pct] = np.where(df_age[col_glob] > 0, np.round(100*df_age[col]/df_age[col_glob], 2), 0)
        
        df_age[col_dsp] = df_age[col_pct].astype('str')
        df_age[col_dsp] = " : " + df_age[col_dsp] + " %"
        df_age[col_dsp] = df_age['cl_age90'] + df_age[col_dsp]

        df_age_nat[col_pct] = np.where(df_age_nat[col_glob] > 0, np.round(100*df_age_nat[col]/df_age_nat[col_glob], 2), 0)

        df_age_nat[col_dsp] = df_age_nat[col_pct].astype('str')
        df_age_nat[col_dsp] = " : " + df_age_nat[col_dsp] + " %"
        df_age_nat[col_dsp] = df_age_nat['cl_age90'] + df_age_nat[col_dsp]
        
    df_age = pd.merge(df_age, df_reg, on='reg', how='left')

    return df_agg_reg, df, df_hors_paris, df_paris, df_age, df_age_nat

#----------------------------------------------------------------------------------------------------------------------------
# Chargement des meta données et des données
def charge(local, nb_jours, date_deb, ratio=10000):
    # Source : # Source : https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/

    # Les méta données
    lib_ratio = s='{:,}'.format(ratio).replace(',', '.')
    #df_meta = pd.read_csv(local+'/Data/metadonnees-donnees-hospitalieres-covid19.csv', sep=';')
    df_type_data = pd.DataFrame({#'colonne': ['hosp','rea','rad','dc'], 
                                 'colonne': ['hosp','rea','dc'], 
                                'type_data': ['Nb actuellement hospitalisés',
                                            'Nb actuellement en réanimation',
                                            #'Nb cumulé de retours à domicile',
                                            "Nb cumulé de décés à l'hôpital"]})
    dict_labels = {'legend':'Région - Département', 'nom_region':'Région', 'nom_departement': 'Département',
                'date':'Date', 'hosp':'Nb actuellement hospitalisés','rea':'Nb actuellement en réanimation',
                'rad':'Nb cumulé de retours à domicile','dc':"Nb cumulé de décés à l'hôpital",
                'hosp_ratio':"Ratio /"+lib_ratio+" hospitalisés", 'rea_ratio':"Ratio /"+lib_ratio+" en réanimation",
                'dc_ratio':"Ratio /"+lib_ratio+" décédés"}
    # Les données
    url = "https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7"
    content = requests.get(url).content
    df = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
    df = df[df.sexe == 0] # On ne considère que le niveau global

    dt_deb = pd.to_datetime(date_deb, format='%d/%m/%Y')
    df.dropna(inplace=True)
    df['test'] = df['jour'].apply(lambda x: np.where(x[:4] == '2020', True, False))
    df1 = df[df.test]
    df2 = df[~df.test]
    df1['date'] = pd.to_datetime(df1['jour'], format='%Y-%m-%d')
    df2['date'] = pd.to_datetime(df2['jour'], format='%d/%m/%Y')
    df = pd.concat([df1, df2]).sort_index()
    df = df[df.date >= dt_deb]

    # Les nouveaux cas depuis 15 jours
    url = "https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c"
    content = requests.get(url).content
    df_new = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
    df_new['date'] = pd.to_datetime(df_new['jour'], format='%Y-%m-%d')

    #-------------------------------------------------------------------------------------------------------------------
    # Source : https://www.data.gouv.fr/fr/datasets/r/1c31f420-829e-489e-a19d-36cf3ef57e4a
    # Les données départements
    df_dept = pd.read_csv(local+'/Data/departements-france.csv')

    #-------------------------------------------------------------------------------------------------------------------
    # Source : https://www.insee.fr/fr/statistiques/1893198
    # La population, par département
    df_pop_dept = pd.read_csv(local+'/Data/population_dept.csv', sep=';')

    #-------------------------------------------------------------------------------------------------------------------
    # Source : https://github.com/gregoiredavid/france-geojson/blob/master/departements.geojson
    with open(local+'/Data/dept.json') as jsonfile:
        geo = json.load(jsonfile)

    # Incorporation des infos départements au dataframe de données
    df = pd.merge(df, df_dept, left_on='dep', right_on='code_departement', how='left')
    df = pd.merge(df, df_pop_dept[['dept','population']], left_on='dep', right_on='dept', how='left')
    df.drop(columns=['dep','sexe','dept'], axis=1, inplace=True)
    df['infos'] = df['code_departement'] + " " + df['nom_departement'] + " (" + df['nom_region'] + ")"
    df['legend'] = df['nom_region'] + " - " + df['nom_departement']
    
    df.dropna(inplace=True)
    df['hosp_ratio'] = df.apply(lambda x: np.round(x['hosp']*ratio/x['population'], 2), axis=1)
    df['rea_ratio'] = df.apply(lambda x: np.round(x['rea']*ratio/x['population'], 2), axis=1)
    df['rad_ratio'] = df.apply(lambda x: np.round(x['rad']*ratio/x['population'], 2), axis=1)
    df['dc_ratio'] = df.apply(lambda x: np.round(x['dc']*ratio/x['population'], 2), axis=1)

    df_new = pd.merge(df_new, df_dept, left_on='dep', right_on='code_departement', how='left')
    df_new['infos_dept'] = df_new['code_departement'] + " " + df_new['nom_departement']

    # Séparation Paris / hors Paris
    df_hors_paris = df[df['nom_region'] != "Ile-de-France"]
    df_paris = df[df['nom_region'] == "Ile-de-France"]

    # Aggrégation niveau régions
    df_agg_reg = df[['nom_region','date','hosp','rea','rad','dc','population']].groupby(['nom_region','date']).aggregate('sum').reset_index()
    #regions = list(df_agg_reg['nom_region'].unique())

    df_new_agg_reg = df_new[['nom_region','date','incid_hosp','incid_rea','incid_dc']].groupby(['nom_region','date']).aggregate('sum').reset_index()
    date_deb = df_new_agg_reg['date'].max() - timedelta(days=nb_jours)
    df_new = df_new[df_new.date >= date_deb]
    df_new_agg_reg = df_new_agg_reg[df_new_agg_reg.date >= date_deb]

    df_agg_reg['hosp_ratio'] = df_agg_reg.apply(lambda x: np.round(x['hosp']*ratio/x['population'], 2), axis=1)
    df_agg_reg['rea_ratio'] = df_agg_reg.apply(lambda x: np.round(x['rea']*ratio/x['population'], 2), axis=1)
    df_agg_reg['rad_ratio'] = df_agg_reg.apply(lambda x: np.round(x['rad']*ratio/x['population'], 2), axis=1)
    df_agg_reg['dc_ratio'] = df_agg_reg.apply(lambda x: np.round(x['dc']*ratio/x['population'], 2), axis=1)

    return df_type_data, df_agg_reg, df, df_hors_paris, df_paris, df_new, df_new_agg_reg, dict_labels, geo

#----------------------------------------------------------------------------------------------------------------------------
def plot_courbes_regions(df_type_data, Donnée, df_agg_reg, dict_labels, local, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0]
    fig = px.line(df_agg_reg, x="date", y=colonne, color="nom_region", labels=(dict_labels),
                  hover_name="nom_region", width=1200, height=600,
                  title='<b>COVID-19 - Evolution par région - '+Donnée+'</b>',
                  category_orders=({'nom_region': list(np.sort(df_agg_reg['nom_region'].unique()))}))
    fig.update_layout(title_x = 0.5, legend_orientation='h',
    title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),)
    fig.update_yaxes(title_text='')
    fig.update_xaxes(title_text='')

    if show == 'O':
        fig.show()

    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_par_region.html', auto_open=False)
    return fig, colonne

#----------------------------------------------------------------------------------------------------------------------------
def plot_courbes_regions_ratio(df_type_data, Donnée, df_agg_reg, dict_labels, local, ratio=10000, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0] + "_ratio"
    lib_ratio = s='{:,}'.format(ratio).replace(',', '.')
    fig = px.line(df_agg_reg, x="date", y=colonne, color="nom_region", labels=(dict_labels),
                  hover_name="nom_region", width=1200, height=600,
                  title='<b>COVID-19 - Evolution par région - '+Donnée+ '<br> - ratio pour '+lib_ratio+' habitants -</br></b>',
                  category_orders=({'nom_region': list(np.sort(df_agg_reg['nom_region'].unique()))}))
    fig.update_layout(title_x = 0.5, legend_orientation='h',
                          title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),)
    fig.update_yaxes(title_text=Donnée + " pour " + lib_ratio)
    fig.update_xaxes(title_text='')

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_ratio_par_region.html', auto_open=False)
    return fig, colonne

#----------------------------------------------------------------------------------------------------------------------------
def plot_courbes_departements(df_type_data, Donnée, df_plot, reg, dict_labels, local, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0]    
    fig = px.line(df_plot, x="date", y=colonne, color="nom_departement",  
                      labels=(dict_labels), hover_name="nom_departement", 
                      title="<b>COVID-19 - Evolution pour la région " + reg + "<br> - "+ Donnée + " - </br><b>",
                      width=1200, height=600, 
                      category_orders=({'nom_departement': list(np.sort(df_plot['nom_departement'].unique()))})
                 )             
    fig.update_layout(title_x = 0.5, showlegend=True, title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),
                          margin=dict(b=0),
                          legend_orientation='h'
                     )
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text='')
    fig.update_xaxes(showticklabels=True)
    fig.update_yaxes(matches=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
            
    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_'+reg+'.html', auto_open=False)

    return fig, colonne

#----------------------------------------------------------------------------------------------------------------------------
def plot_courbes_departements_grid(df_type_data, Donnée, df, dict_labels, local, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0]
    fig = px.line(df, x="date", y=colonne, color="legend", facet_col='nom_region', facet_col_wrap=3,
                  labels=(dict_labels), hover_name="nom_departement", 
                  title="<b>COVID 19 - Evolution par région départements - "+Donnée+"</b>",
                #  width=1500, height=1500, 
                  category_orders=({'nom_region': list(np.sort(df['nom_region'].unique())),
                                    'legend': list(np.sort(df['legend'].unique()))}))             
    fig.update_layout(title_x = 0.5, showlegend=False, 
                          title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),)
    #fig.update_yaxes(title_text=Donnée)
    fig.update_yaxes(title_text='')
    fig.update_xaxes(title_text='')
    fig.update_xaxes(showticklabels=True)
    fig.update_yaxes(matches=None)
    fig.update_yaxes(showticklabels=True, col=2)
    fig.update_yaxes(showticklabels=True, col=3)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    #fig['layout']['yaxis2']['title']['text']=''
    #fig['layout']['yaxis3']['title']['text']=''
    #fig['layout']['yaxis5']['title']['text']=''
    #fig['layout']['yaxis6']['title']['text']=''
    #fig['layout']['yaxis8']['title']['text']=''
    #fig['layout']['yaxis9']['title']['text']=''
    #fig['layout']['yaxis11']['title']['text']=''
    #fig['layout']['yaxis12']['title']['text']=''
    #fig['layout']['yaxis14']['title']['text']=''
    #fig['layout']['yaxis15']['title']['text']=''
    #fig['layout']['yaxis17']['title']['text']=''
    #fig['layout']['yaxis18']['title']['text']=''

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_par_region_dept.html', auto_open=False)

    return fig, colonne

#----------------------------------------------------------------------------------------------------------------------------
def plot_courbes_departements_ratio(df_type_data, Donnée, df_plot, reg, dict_labels, local, ratio=10000, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0] + "_ratio"
    lib_ratio = s='{:,}'.format(ratio).replace(',', '.')

    fig = px.line(df_plot, x="date", y=colonne, color="nom_departement",  
                      labels=(dict_labels), hover_name="nom_departement", 
                      title="<b>COVID-19 - Evolution pour la région " + reg + "<br>- "+ Donnée+' : ratio pour '+lib_ratio+' habitants -</br> </b>',
                      width=1200, height=600, 
                      category_orders=({'nom_departement': list(np.sort(df_plot['nom_departement'].unique()))})
                 )             
    fig.update_layout(title_x = 0.5, showlegend=True,
                          title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),
                          margin=dict(b=0),
                          legend_orientation='h'
                     )
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text=Donnée + " pour " + lib_ratio)
    fig.update_xaxes(showticklabels=True)
    fig.update_yaxes(matches=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_ratio_'+reg+'.html', auto_open=False)

    return fig, colonne

#----------------------------------------------------------------------------------------------------------------------------
def plot_courbes_departements_ratio_grid(df_type_data, Donnée, df, dict_labels, local, ratio=10000, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0] + "_ratio"
    lib_ratio = s='{:,}'.format(ratio).replace(',', '.')
    fig = px.line(df, x="date", y=colonne, color="legend", facet_col='nom_region', facet_col_wrap=3,
                  labels=(dict_labels), hover_name="nom_departement", 
                  title="<b>COVID 19 - Evolution par région départements - "+Donnée+' : ratio pour '+lib_ratio+' habitants</b>',
                 # width=1500, height=1500, 
                  category_orders=({'nom_region': list(np.sort(df['nom_region'].unique())),
                                    'legend': list(np.sort(df['legend'].unique()))}))             
    fig.update_layout(title_x = 0.5, showlegend=False, title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)))
    #fig.update_yaxes(title_text=Donnée)
    fig.update_yaxes(title_text='')
    fig.update_xaxes(title_text='')
    fig.update_xaxes(showticklabels=True)
    fig.update_yaxes(matches=None)
    fig.update_yaxes(showticklabels=True, col=2)
    fig.update_yaxes(showticklabels=True, col=3)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    #fig['layout']['yaxis2']['title']['text']=''
    #fig['layout']['yaxis3']['title']['text']=''
    #fig['layout']['yaxis5']['title']['text']=''
    #fig['layout']['yaxis6']['title']['text']=''
    #fig['layout']['yaxis8']['title']['text']=''
    #fig['layout']['yaxis9']['title']['text']=''
    #fig['layout']['yaxis11']['title']['text']=''
    #fig['layout']['yaxis12']['title']['text']=''
    #fig['layout']['yaxis14']['title']['text']=''
    #fig['layout']['yaxis15']['title']['text']=''
    #fig['layout']['yaxis17']['title']['text']=''
    #fig['layout']['yaxis18']['title']['text']=''

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_ratio_par_region_dept.html', auto_open=False)

    return fig, colonne

#----------------------------------------------------------------------------------------------------------------------------
def plot_carte(df_type_data, dte_deb, Donnée, Zone, df_hors_paris, df_paris, geo, local, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0]
    
    if Zone == 'Hors Paris':
        df_plot = df_hors_paris
        lib_zone = "hors région Ile-de-France"
    elif Zone == 'Paris':
        df_plot = df_paris
        lib_zone = "en région Ile-de-France"
    else:
        df_plot = pd.concat([df_hors_paris, df_paris], ignore_index=True)
        lib_zone = 'en France'

    df_plot = df_plot[df_plot.date >= dte_deb][['jour','hosp','rea','dc', \
                                                'hosp_ratio','rea_ratio','dc_ratio', \
                                                'date','code_departement','infos']]
    min = df_plot[colonne].min()
    max = df_plot[colonne].max()

    fig = px.choropleth(df_plot,
                        geojson=geo,
                        locations="code_departement", 
                        featureidkey="properties.code",
                        color=colonne,
                        animation_frame="jour",
                        hover_name="infos",
                        hover_data={'code_departement':False},
                        color_continuous_scale=px.colors.sequential.RdBu_r,
                        range_color=[min, max],
                        labels={'hosp':'Nb personnes', 'rea':'Nb personnes', 'rad':'Nb personnes', \
                                'dc':'Nb personnes'}
                       )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(hoverlabel=dict(bgcolor="white"),
        title_text = "<br>COVID-19 - Evolution sur les 15 derniers jours "+lib_zone+"<br>- "+Donnée + " -<br></b>",
        title_x = 0.5, title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),
        geo=dict(
            showframe = False,
            showcoastlines = False,
            projection_type = 'mercator'),
        width=800,
        height=700,
        margin=dict(
            l= 0,
            r= 0,
            b= 0,
            #t= 0,
            pad= 4)
    )
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_carte_'+Zone.replace(' ','_')+'.html', auto_open=False)

    return fig, colonne

#----------------------------------------------------------------------------------------------------------------------------
def plot_carte_ratio(df_type_data, dte_deb, Donnée, Zone, df_hors_paris, df_paris, geo, local, ratio=10000, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0] + "_ratio"
    lib_ratio = s='{:,}'.format(ratio).replace(',', '.')
    
    if Zone == 'Hors Paris':
        df_plot = df_hors_paris
        lib_zone = "hors région Ile-de-France"
    elif Zone == 'Paris':
        df_plot = df_paris
        lib_zone = "en région Ile-de-France"
    else:
        df_plot = pd.concat([df_hors_paris, df_paris], ignore_index=True)
        lib_zone = 'en France'

    df_plot = df_plot[df_plot.date >= dte_deb][['jour','hosp','rea','dc', \
                                                'hosp_ratio','rea_ratio','dc_ratio', \
                                                'date','code_departement','infos']]
    min = df_plot[colonne].min()
    max = df_plot[colonne].max()

    fig = px.choropleth(df_plot,
                        geojson=geo,
                        locations="code_departement", 
                        featureidkey="properties.code",
                        color=colonne,
                        animation_frame="jour",
                        hover_name="infos",
                        hover_data={'code_departement':False},
                        color_continuous_scale=px.colors.sequential.RdBu_r,
                        range_color=[min, max],
                        labels={'hosp':'Nb personnes', 'rea':'Nb personnes', 'rad':'Nb personnes',
                                'dc':'Nb personnes'}
                       )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(hoverlabel=dict(bgcolor="white"),
        title_text = "<br>COVID-19 - Evolution sur les 15 derniers jours "+lib_zone+"<br>- "+Donnée+' : ratio pour '+lib_ratio+' habitants -</br></b> ',
        title_x = 0.5, title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),
        geo=dict(
            showframe = False,
            showcoastlines = False,
            projection_type = 'mercator'),
        width=800,
        height=700,
        margin=dict(
            l= 0,
            r= 0,
            b= 0,
            #t= 0,
            pad= 4)
    )
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_ratio_carte_'+Zone.replace(' ','_')+'.html', auto_open=False)

    return fig, colonne
#----------------------------------------------------------------------------------------------------------------------------
def plot_heatmap_regions(df_new_agg_reg, local, Zone, show='O'):
    if Zone == 'Tout':
        df_plot = df_new_agg_reg.copy()
        titre = '<b>COVID-19 - Evolution des nouveaux cas par région sur les 15 derniers jours</b>'
    if Zone == 'Hors Paris':
        df_plot = df_new_agg_reg[df_new_agg_reg['nom_region'] != "Ile-de-France"]
        titre = '<b>COVID-19 - Evolution des nouveaux cas par région sur les 15 derniers jours - Hors région Ile-de-France</b>'
    if Zone == 'Paris':
        df_plot = df_new_agg_reg[df_new_agg_reg['nom_region'] == "Ile-de-France"]
        titre = '<b>COVID-19 - Evolution des nouveaux cas en Ile-de-France sur les 15 derniers jours</b>'

    fig = make_subplots(rows=1, cols=6,
                        subplot_titles=("Nb quotidien de personnes : Hospitalisées", \
                                        "                               Admises en réanimation", \
                                        "               Décédées"),
                        specs=[[{}, None, {}, None, {}, None]],
                        shared_yaxes=True)

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_hosp'],
        x=df_plot['date'],
        y=df_plot['nom_region'],
        name="Hosp. +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.27, title='Nb pers.', thickness=15)), row=1, col=1
    )

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_rea'],
        x=df_plot['date'],
        y=df_plot['nom_region'],
        name="Réa. +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.62, title='Nb pers.', thickness=15)), row=1, col=3
    )

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_dc'],
        x=df_plot['date'],
        y=df_plot['nom_region'],
        name="Décès +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.97, title='Nb pers.', thickness=15)), row=1, col=5
    )
    fig.update_layout(title_text=titre, title_x=0.5, title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),
                    height=500, width=1200, margin=dict(l=0,r=0,b=50),#t=25),
                    xaxis=dict(
            domain=[0, 0.27]
        ),
        xaxis2=dict(
            domain=[0.35, 0.62]
        ),
        xaxis3=dict(
            domain=[0.7, 0.97]
        ))

    fig['layout']['yaxis']['autorange'] = "reversed"
    fig['layout']['yaxis2']['autorange'] = "reversed"
    fig['layout']['yaxis3']['autorange'] = "reversed"

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_Nouveaux_Cas_Régions_'+Zone.replace(' ','_')+'.html', auto_open=False)

    return fig
    
#----------------------------------------------------------------------------------------------------------------------------
def plot_heatmap_departements(df_new, local, Zone, show='O'):
    if Zone == 'Tout':
        df_plot = df_new.copy()
        titre = '<b>COVID-19 - Evolution des nouveaux cas par région et département sur les 15 derniers jours</b>'
    if Zone == 'Hors Paris':
        df_plot = df_new[df_new['nom_region'] != "Ile-de-France"]
        titre = '<b>COVID-19 - Evolution des nouveaux cas par région et département sur les 15 derniers jours - Hors Ile-de-France</b>'
    if Zone == 'Paris':
        df_plot = df_new[df_new['nom_region'] == "Ile-de-France"]    
        titre = '<b>COVID-19 - Evolution des nouveaux cas en Ile-de-France sur les 15 derniers jours</b>'
    
    fig = make_subplots(rows=1, cols=6,
                        subplot_titles=("Nb quotidien de personnes : Hospitalisées", \
                                        "                               Admises en réanimation", \
                                        "               Décédées"),
                        specs=[[{}, None, {}, None, {}, None]],
                        shared_yaxes=True)

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_hosp'],
        x=df_plot['date'],
        y=[df_plot['nom_region'], df_plot['infos_dept']],
        name="Hosp. +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.27, title='Nb pers.', thickness=15)), row=1, col=1
    )

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_rea'],
        x=df_plot['date'],
        y=[df_plot['nom_region'], df_plot['infos_dept']],
        name="Réa. +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.62, title='Nb pers.', thickness=15)), row=1, col=3
    )

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_dc'],
        x=df_plot['date'],
        y=[df_plot['nom_region'], df_plot['infos_dept']],
        name="Décès +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.97, title='Nb pers.', thickness=15)), row=1, col=5
    )
    fig.update_layout(title_text=titre, title_x=0.5, title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),
                    height=2200, width=1200, margin=dict(l=0,r=0,b=50),#t=25),
                    xaxis=dict(
            domain=[0, 0.27]
        ),
        xaxis2=dict(
            domain=[0.35, 0.62]
        ),
        xaxis3=dict(
            domain=[0.7, 0.97]
        ))

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_Nouveaux_Cas_Départements_'+Zone.replace(' ','_')+'.html', auto_open=False)

    return fig

#----------------------------------------------------------------------------------------------------------------------------
def plot_heatmap_1region(df_plot, reg, local, show='O'):
    titre = '<b>COVID-19 - Evolution des nouveaux cas sur les 15 derniers jours - région '+reg+'</b>'
    nb_depts = len(df_plot['code_departement'].unique())
    
    fig = make_subplots(rows=1, cols=6,
                        subplot_titles=("   Nb quotidien de personnes : Hospitalisées", \
                                        "                         Admises en réanimation", \
                                        "                Décédées"),
                        specs=[[{}, None, {}, None, {}, None]],
                        shared_yaxes=True)

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_hosp'],
        x=df_plot['date'],
        y=df_plot['nom_departement'],
        name="Hosp. +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.27, title='Nb pers.', thickness=15)), row=1, col=1
    )

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_rea'],
        x=df_plot['date'],
        y=df_plot['nom_departement'],
        name="Réa. +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.62, title='Nb pers.', thickness=15)), row=1, col=3
    )

    fig.add_trace(go.Heatmap(
        z=df_plot['incid_dc'],
        x=df_plot['date'],
        y=df_plot['nom_departement'],
        name="Décès +",
        colorscale='RdBu',
        reversescale=True,
        colorbar = dict(x=0.97, title='Nb pers.', thickness=15)), row=1, col=5
    )
    fig.update_layout(title_text=titre, title_x=0.5, title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=17)),
                    height=500, width=1200, margin=dict(l=0,r=0,b=50),#t=25),
                    xaxis=dict(
            domain=[0, 0.27]
        ),
        xaxis2=dict(
            domain=[0.35, 0.62]
        ),
        xaxis3=dict(
            domain=[0.7, 0.97]
        ))

    fig['layout']['yaxis']['autorange'] = "reversed"
    fig['layout']['yaxis2']['autorange'] = "reversed"
    fig['layout']['yaxis3']['autorange'] = "reversed"

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_Nouveaux_Cas_Région_'+reg.replace(' ','_')+'.html', auto_open=False)

    return fig


#----------------------------------------------------------------------------------------------------------------------------
def plot_donnee_age(df_type_data, Donnée, df, dict_labels, local, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0] + "_pct"

    fig = px.line(df, x="date", y=colonne, color="cl_age90", 
                  labels=(dict_labels), hover_name="dsp_col_"+colonne, hover_data=[colonne],
                  title="<b>COVID 19 - Evolution de la répartition par classe d'âge en % - "+Donnée+"</b>",
                  #width=1500, height=1500, 
                  category_orders=({'legend': list(np.sort(df['cl_age90'].unique()))}))             
    
    fig.update_layout(title_x = 0.5, showlegend=True, title_font_size=17, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=10), orientation='v'))

    #fig.update_yaxes(title_text=Donnée)
    fig.update_yaxes(title_text='Pourcentage')
    fig.update_xaxes(title_text='')
    fig.update_xaxes(showticklabels=True)
    fig.update_yaxes(matches=None)
    fig.update_yaxes(showticklabels=True, col=2)
    fig.update_yaxes(showticklabels=True, col=3)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_'+colonne+'_age.html', auto_open=False)

    return fig, colonne


#----------------------------------------------------------------------------------------------------------------------------
def plot_age_1region(df_type_data, Donnée, df_plot, reg, dict_labels, local, show='O'):
    colonne = df_type_data[df_type_data.type_data == Donnée]['colonne'].reset_index(drop=True)[0] + "_pct"
    fig = px.line(df_plot, x="date", y=colonne, color="cl_age90",  
                      labels=(dict_labels), hover_name="dsp_col_"+colonne, hover_data=[colonne],
                      title="<b>COVID-19 - Evolution pour la région " + reg + "<br> - "+ Donnée + " - </br><b>",
                      width=1200, height=600, 
                 )             
    fig.update_layout(title_x = 0.5, showlegend=True, title_font_size=20, title_font_color='rgb(217,95,2)',
                          legend=dict(font=dict(size=15)),
                          margin=dict(b=0),
                          legend_orientation='h'
                     )
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text='')
    fig.update_xaxes(showticklabels=True)
    fig.update_yaxes(matches=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
            
    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Evol_age_'+colonne+'_'+reg+'.html', auto_open=False)

    return fig, colonne



def plot_vaccin(df, geo, local, show='O'):

    list_om = ['971', '972', '973', '974', '976']
    annot = ""
    for d in list_om:
        dep = df[df.code_departement == d]['nom_departement'].reset_index(drop=True)[0]
        taux = df[df.code_departement == d]['couv_tot_complet'].reset_index(drop=True)[0]
        if (d == '973') or (d == '976'):
            annot += dep + "\t\t: " + str(taux) + "<br>"
        elif d == '971':
            annot += dep + "\t: " + str(taux) + "<br>"
        else:
            annot += dep + "\t: " + str(taux) + "<br>"

    min = 40 #df[~df.code_departement.isin(list_om)]['couv_tot_complet'].min()
    max = 100 #df[~df.code_departement.isin(list_om)]['couv_tot_complet'].max()

    fig = px.choropleth(df[~df.code_departement.isin(list_om)],
                        geojson=geo,
                        locations="code_departement", 
                        featureidkey="properties.code",
                        color='couv_tot_complet',
                        #animation_frame="jour",
                        hover_name="infos",
                        color_continuous_scale=px.colors.sequential.Greens,
                        range_color=[min, max],
                        labels={'couv_tot_complet':'Taux de population couverte'},
                        hover_data={'code_departement':False} 
                    )

    fig.update_geos(fitbounds="locations", visible=False)

    fig.add_annotation(text=annot, font_size=12, align='left',
                    xref="paper", yref="paper",
                    x=0, y=0.05, showarrow=False)

    fig.update_layout(hoverlabel=dict(bgcolor="white"),
        title_text = "<br>Taux de couverture par département</br>",
        title_x = 0.5, title_font_size=20, title_font_color='rgb(217,95,2)',
                        showlegend=False,
        geo=dict(
            showframe = False,
            showcoastlines = False,
            projection_type = 'mercator'),
        width=600,
        height=400,
        margin=dict(
            l= 0,
            r= 0,
            b= 0,
            #t= 0,
            pad= 4)
    )

    if show == 'O':
        fig.show()
    
    if local != ".":
        fig.write_html(local+'/Output/Vaccin_dept.html', auto_open=False)

    return fig
