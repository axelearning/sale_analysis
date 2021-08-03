import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash
import plotly.graph_objects as go
import plotly.io as pio
pio.templates.default = "plotly_white"


'''
   ------------------------------------------------------------------------------------------- 
   CONFIG
   ------------------------------------------------------------------------------------------- 
'''
load_dotenv()
MAPBOX_TOKEN = os.environ.get('MAPBOX_TOKEN')

DASH_CONFIG = {'displayModeBar': False, 'showAxisDragHandles': False,
               'responsive': True, "scrollZoom": False}
DEFAULT_MARGIN = dict(l=20, r=20, t=20, b=20)

COLOR_PALETTE = {
    'Ordinateur': '#264653',
    'Smartphone': '#2a9d8f',
    'Accessoire': '#e9c46a',
    'TV & Moniteur': '#f4a261',
    'Machine à laver': '#e76f51'
}
str_to_int = {key: i for i, key in enumerate(COLOR_PALETTE.keys())}
CUSTOM_BLUE = "rgba(33, 158, 188, 1)"
CUSTOM_ORANGE = "rgba(244, 140, 6, 1)"

STYLE_SHEET = [dbc.themes.BOOTSTRAP, "assets/main.css"]
app = dash.Dash(__name__, external_stylesheets=STYLE_SHEET)
server = app.server


def millify(n):
    if n > 999:
        if n > 1e6-1:
            return f'{round(n/1e6,1)}M'
        return f'{round(n/1e3,1)}K'
    return n


'''
   ------------------------------------------------------------------------------------------- 
                                            CREATE THE FIGURE
   ------------------------------------------------------------------------------------------- 

'''
# LOAD DATA
raw_data = pd.read_csv('data/raw_data.csv')
raw_data.sort_values(by="Date", inplace=True)
data = pd.read_csv('data/clean_data.csv')

# 1. ANALYSE DES PRODUITS
# -----------------------
product_report = data.groupby(['Cat', 'Product', 'Price Each']).sum()

product_list = product_report.index.get_level_values('Product')
categories_list = product_report.index.get_level_values('Cat')

# Figure 1 (parcast): 5 catégories de 19 produits
# create dim
df = product_report.reset_index().sort_values('Price Each', ascending=False)
cat_dim = go.parcats.Dimension(values=df['Cat'].values, categoryorder="trace")
product_dim = go.parcats.Dimension(
    values=df['Product'].values,
    categoryorder="array",
    categoryarray=df["Product"].values)
# color
colors = df['Cat'].apply(lambda x: str_to_int[x])
colorscale = [value for value in COLOR_PALETTE.values()]
# plot
parcats = go.Figure(
    go.Parcats(
        dimensions=[cat_dim, product_dim],
        line=dict(color=colors, colorscale=colorscale, shape='hspline'),
        hoverinfo='none'))
# update
parcats.update_layout(margin=dict(l=45, r=80, t=20, b=20))

# Figure 2 (horizontal bar): Classement des produits
df = product_report.sort_values(by="Sales").reset_index(["Cat", "Price Each"])
df["percent"] = df["Sales"]/df["Sales"].sum() * 100
# sales labels
df["text"] = [f"{int(np.round(p))}%" for p in df["percent"]]
text = [None] * len(df)
text[-4:] = df.text[-4:]
# color
colors = np.array(["rgba(142, 143, 144, 0.8)"]*len(df))
colors[-4:] = CUSTOM_BLUE
colors[:5] = CUSTOM_ORANGE
# plot
product_bar = go.Figure(
    go.Bar(
        y=df.index,
        x=df["percent"],
        marker_color=colors,
        customdata=df["Cat"]))
# update
product_bar.update_layout(
    height=600, margin={**DEFAULT_MARGIN, **{"pad": 10, "t": 50}})
product_bar.update_xaxes(showgrid=False, showticklabels=False,
                         zeroline=False, showline=False, fixedrange=True)
product_bar.update_yaxes(showgrid=False, showline=False, fixedrange=True)
product_bar.update_traces(showlegend=False, orientation='h')
product_bar.update_traces(text=text, textposition='auto',
                          hovertemplate="<b>%{y}</b> %{x:.2g}%<extra>%{customdata}</extra>")
# annotations
product_bar.add_annotation(
    text="% du chiffre d'affaires en 2019",
    xref='paper', x=0, xanchor="left",
    yref='paper', y=1.045,
    showarrow=False,
    font=dict(color="#8E8F90", size=13))
product_bar.add_annotation(
    text="""<b>3.1% du Chiffre d'affaires</b>
        <br><span style="color:#6c757d;">pour 5 des 19 produits</span>""",
    align="left",
    x=0.05, xref="paper",
    y=0.1, yref="paper",
    showarrow=False,
    font=dict(color=CUSTOM_ORANGE, size=15))
product_bar.add_annotation(
    text="""<b>58% du Chiffre d'affaires</b>
        <br><span style="color:#6c757d;">pour les 4 meilleurs produits</span>""",
    align="left",
    x=0.6, xref="paper", xanchor="left",
    y=0.93, yref="paper",
    showarrow=False,
    font=dict(color=CUSTOM_BLUE, size=15))

# Figure 3 (scatter): Volume de ventes des produits selon leurs prix
df = product_report[['Sales', 'Quantity Ordered']].reset_index()
size = df['Quantity Ordered']
# colors
df["colors"] = "grey"
df.loc[df["Sales"] > 2.9e6, "colors"] = CUSTOM_BLUE
df.loc[df["Price Each"] < 75, "colors"] = CUSTOM_ORANGE
# plot
scatter_plot_product = go.Figure(
    go.Scatter(
        x=df["Price Each"],
        y=df["Sales"],
        mode="markers",
        marker=dict(
            color=df["colors"],
            line=dict(width=0.5, color='black'),
            size=size,
            sizemode='area',
            sizeref=3.*max(size)/(30.**2)),
        text=df["Product"],
        hovertemplate="""<b>%{text}</b><br>prix unitaire, <b>%{x} $</b> <br>volume des ventes, <b>%{y:.2s} $</b> <extra></extra>"""))
# update
scatter_plot_product.update_layout(height=600, margin=DEFAULT_MARGIN)
scatter_plot_product.update_xaxes(
    title=dict(text='Prix des produits ($)', font=dict(color="grey", size=12)),
    range=[-50, 1800],
    nticks=5,
    tickfont_color='grey',
    showgrid=True,
    fixedrange=True,
    zeroline=True, zerolinewidth=1, zerolinecolor='grey')
scatter_plot_product.update_yaxes(
    title=dict(text='Volume de ventes ($)', font=dict(color="grey", size=12)),
    range=[-5e5, 8.5e6],
    nticks=5,
    tickfont_color='grey',
    showgrid=True,
    fixedrange=True,
    zeroline=True, zerolinewidth=1, zerolinecolor='grey')
# annotations
scatter_plot_product.add_annotation(
    text="<b>Macbook Pro</b>, produit haut de <br>gamme avec une rentabilité élevée",
    align="left",
    x=1700, y=8037600,
    ax=-200, ay=0),
scatter_plot_product.add_annotation(
    text='<b>Machine à laver</b>, produit volumineux<br> avec une rentabilité discutable',
    align="left",
    x=600, y=4e5,
    ay=-40, ax=60)
scatter_plot_product.add_annotation(
    text='<b>Produits low cost</b>, rentabilité faible<br>nombre de ventes élevées',
    align="left",
    x=10, y=3e5,
    ay=-225, ax=120)

# Figure 4 (horizontal bar): comparaison low cost high priced
df = product_report[['Sales', 'Quantity Ordered']].reset_index()
df["r_sales"] = df["Sales"] / df["Sales"].sum()
df["r_quantity"] = df["Quantity Ordered"] / df["Quantity Ordered"].sum()
# Figure 4.1 low cost product
low_cost = df[df["Price Each"] < 25].sum()
low_cost_viz = go.Figure([
    go.Bar(
        x=[1, 1],
        marker_color="lightgrey",
        width=0.5,
        hoverinfo='skip'),
    go.Bar(
        x=low_cost[["r_quantity", "r_sales"]],
        customdata=low_cost[["Sales", "Quantity Ordered"]],
        width=0.5,
        marker=dict(color=CUSTOM_ORANGE, line_color=CUSTOM_ORANGE),
        hovertemplate="%{customdata:.3s}<extra></extra>")
])
# update
low_cost_viz.update_layout(
    height=400,
    barmode='overlay',
    margin=DEFAULT_MARGIN,
    annotations=[
        dict(text="Chiffre d'affaires", xref='paper', x=-0.002, yref='paper',
             y=0.95, showarrow=False,  font=dict(color="#6c757d", size=14)),
        dict(text="Nombre de ventes", xref='paper', yref='paper', x=-0.002,
             y=0.42, showarrow=False, font=dict(color="#6c757d", size=14)),
    ])
low_cost_viz.update_xaxes(showgrid=False, showticklabels=False,
                          zeroline=False, showline=False, fixedrange=True)
low_cost_viz.update_yaxes(showgrid=False, showline=False,
                          showticklabels=False, fixedrange=True)
low_cost_viz.update_traces(
    orientation="h",
    showlegend=False,
    texttemplate="%{x:2%}", textposition='outside', textfont=dict(size=25, color="white"))

# Figure 4.2: high priced product
high_priced = df[df["Product"].isin(
    ['Macbook Pro', 'iPhone XR', 'Samsung Galaxy n10', 'Dell XPS 13'])].sum()
high_cost_viz = go.Figure([
    go.Bar(

        x=[1, 1],
        marker_color="lightgrey",
        width=0.5,
        hoverinfo='skip'),
    go.Bar(
        x=high_priced[["r_quantity", "r_sales"]],
        customdata=high_priced[["Sales", "Quantity Ordered"]],
        marker_color=CUSTOM_BLUE,
        width=0.5,
        marker_line_color=CUSTOM_BLUE,
        hovertemplate="%{customdata:.3s}<extra></extra>")
])
high_cost_viz.update_layout(
    height=400,
    barmode='overlay',
    margin=DEFAULT_MARGIN,
    annotations=[
        dict(text="Chiffre d'affaires", xref='paper', x=-0.002, yref='paper',
             y=0.95, showarrow=False,  font=dict(color="#6c757d", size=14)),
        dict(text="Nombre de ventes", xref='paper', yref='paper', x=-0.002,
             y=0.42, showarrow=False, font=dict(color="#6c757d", size=14)),
    ]
)
high_cost_viz.update_xaxes(showgrid=False, showticklabels=False,
                           zeroline=False, showline=False, fixedrange=True)
high_cost_viz.update_yaxes(
    showgrid=False, showline=False, showticklabels=False, fixedrange=True)
high_cost_viz.update_traces(
    orientation="h",
    showlegend=False,
    texttemplate="%{x:2%}", textposition='outside', textfont=dict(size=25, color="white"))

# 2. ANALYSE DES LIEUX DE VENTES
# -------------------------------
city_sales = data.groupby(['City', 'lat', 'long']).sum()['Sales'].reset_index()
city_sales['Sales_text'] = city_sales['Sales'].apply(lambda x: millify(x))
cities = city_sales['City']
city_sales['percents'] = city_sales['Sales']/city_sales['Sales'].sum()

# Figure 5 (map): Cartographie des lieux de ventes
# plot
map_plot = go.Figure(
    go.Scattermapbox(
        lat=city_sales['lat'],
        lon=city_sales['long'],
        marker=dict(
            size=city_sales['Sales']/350000,
            opacity=0.5,
            allowoverlap=True,
            color=CUSTOM_BLUE),
        hoverinfo='none'
    )
)
# add border
map_plot.add_trace(
    go.Scattermapbox(
        lat=city_sales['lat'],
        lon=city_sales['long'],
        marker=dict(
            size=city_sales['Sales']/200000,
            opacity=0.3,
            allowoverlap=True,
            color=CUSTOM_BLUE),
        mode="markers+text",
        textposition="top center",
        textfont=dict(family="sans serif", size=16, color="black"),
        text=cities
    )
)
# update
map_plot.update_layout(
    hoverlabel=dict(
        bgcolor="white",
        font_size=12),
    margin=dict(l=0, r=0, t=0, b=0),
    mapbox=dict(
        accesstoken=MAPBOX_TOKEN,
        zoom=2.9,
        center=go.layout.mapbox.Center(lat=40, lon=-97),
        style="mapbox://styles/axelitorosalito/ckb2erv2q148d1jnp7959xpz0"),
    showlegend=False
)

# Figure 6 (horizontal bar): Classement des villes
df = city_sales.copy()
df.sort_values(by="Sales", inplace=True)
city_rank = go.Figure(
    go.Bar(
        y=df['City'],
        x=df['percents'],
        hovertemplate="<b>%{y}</b><br>%{x:.2%} du chiffre d'affaires<extra></extra>")
)
# updates
city_rank.update_layout(margin={**DEFAULT_MARGIN, **{"pad": 10, "t": 50}},
                        hoverlabel=dict(bgcolor="white", font_size=12))
city_rank.update_xaxes(showgrid=False, showticklabels=False,
                       zeroline=False, showline=False, fixedrange=True)
city_rank.update_yaxes(showgrid=False, showline=False, fixedrange=True)
city_rank.update_traces(marker_color=CUSTOM_BLUE, orientation='h',
                        textposition="auto", texttemplate='%{x:.0%}', textfont_color="white")

#  annotations
city_rank.add_annotation(
    text="% du chiffre d'affaires en 2019",
    xref="paper", yref="paper",
    x=0, y=1.06, xanchor="left",
    showarrow=False,
    font=dict(color="#8E8F90", size=13)
)

# Figure 7 (scatter): Salaire moyen en fonction des Ventes
df = pd.read_csv("data/city_info.csv")
# plot
sales_income = go.Figure(
    go.Scatter(
        x=df["income_2010"],
        y=df["Sales"],
        mode="markers+text",
        text=df["City"],
        hovertemplate="<b>%{text}</b><br><b>%{y:.2s} $</b> de chiffres d'affaires<br><b>%{x:.2s} $</b> de salaire moyen<extra></extra>")
)
# update
sales_income.update_layout(height=600, hoverlabel=dict(
    bgcolor="white", font_size=14), margin=DEFAULT_MARGIN)
sales_income.update_traces(textposition='top center',
                           marker=dict(size=10, color="grey"))
sales_income.update_xaxes(
    title=dict(text="Salaire moyen annuel net ($)", font_color="grey"),
    nticks=5,
    tickfont_color='grey',
    zeroline=True, zerolinewidth=1, zerolinecolor='grey', fixedrange=True
)
sales_income.update_yaxes(
    title=dict(text="Volume de ventes($)", font_color="grey"),
    nticks=5,
    tickfont_color='grey',
    zeroline=True, zerolinewidth=1, zerolinecolor='grey', fixedrange=True
)

# Figure 8 (scatter): Budget pub en fonction des Ventes
city_color = (df['City'] == "San Francisco").map(
    lambda x: CUSTOM_BLUE if x else "grey")
# plot
sales_ads = go.Figure(
    go.Scatter(
        x=df["ads_budget"],
        y=df["Sales"],
        mode="markers",
        text=df['City'],
        hovertemplate="<b>%{text}</b><br><b>%{y:.2s} $</b> de chiffres d'affaires<br><b>%{x:.2s} $</b>de budget publicitaire<extra></extra>"
    ))
# update
sales_ads.update_traces(marker=dict(size=10, color=city_color))
sales_ads.update_xaxes(
    title=dict(text="Budget publicitaire ($)", font_color="grey"),
    nticks=5,
    tickfont_color='grey',
    zeroline=False,
    fixedrange=True
)
sales_ads.update_yaxes(
    title=dict(text="Volume de ventes ($)", font_color="grey"),
    nticks=5,
    tickfont_color='grey',
    zeroline=False,
    fixedrange=True
)
sales_ads.update_layout(
    height=600,
    hoverlabel=dict(bgcolor="white", font_size=14),
    margin=DEFAULT_MARGIN,
    annotations=[
        dict(x=27.3e3, y=8e6, text='San Francisco', showarrow=False),
        dict(x=11.8e3, y=5.7e6, text='Los Angeles', showarrow=False),
        dict(x=8.2e3, y=4.9e6, text='New York', showarrow=False),
        dict(x=5.6e3, y=3.9e6, text='Boston', showarrow=False),
        dict(x=3.625e3, y=2.79e6, text='Atlanta', ax=30, ay=-20),
        dict(x=3.064e3, y=2.76e6, text='Dallas', ax=0, ay=-40),
        dict(x=2.77e3, y=2.74e6, text='Seattle', ax=-30, ay=-20),
        dict(x=2.15e3, y=2.53e6, text='Portland', showarrow=False),
        dict(x=1.32e3, y=2e6, text='Austin', showarrow=False)
    ]
)

# 3. ANALYSE TEMPORELLE
# -----------------------
sales_per_month = data.groupby(['Month_num', 'Month'])[
    'Sales'].sum().reset_index()

# Figure 9 (line): chiffre d'affaires mensuel
# plot
ca_per_month = go.Figure(
    go.Scatter(
        x=sales_per_month["Month"],
        y=sales_per_month["Sales"],
        fill="tozeroy",
        hovertemplate="%{y:.2s} $ de CA<extra></extra>",
        marker=dict(size=10, color=CUSTOM_BLUE,
                    line=dict(width=0.5, color='black'))
    )
)
# update
ca_per_month.update_xaxes(showgrid=False, tickfont_color='grey', range=[
                          0, 11.1], fixedrange=True)
ca_per_month.update_yaxes(
    title=dict(
        text="Chiffre d'Affaires mensuelle ($)", font_color="grey"),
    nticks=3,
    tickfont_color='grey',
    fixedrange=True
)
ca_per_month.update_layout(
    height=600,
    margin=DEFAULT_MARGIN,
    hoverlabel=dict(bgcolor="white", font_size=14),
    hovermode='x unified',
    shapes=[
        dict(type="rect", xref="x", x0=5, x1=8, yref="paper", y0=0, y1=1,
             fillcolor="grey", opacity=0.2, layer="below", line_width=0),
        dict(type="rect", xref="x", x0=0, x1=2, yref="paper", y0=0, y1=1,
             fillcolor="grey", opacity=0.2, layer="below", line_width=0)
    ],
    annotations=[
        dict(text='<b>Vacances Scolaires</b><br>Période creuse',
             align="left", x=6.5, y=3.5e6, font=dict(size=14), showarrow=False),
        dict(text='<b>Après Fêtes</b><br>Période creuse', align="left",
             x=1, y=3.5e6, font=dict(size=14), showarrow=False),
        dict(x=11, y=4.62e6, ay=0, ax=-50,
             font=dict(size=14), text="<b>Fêtes<b>")
    ])


# Figure 10 (line): heures d'achats des produits
buying_hours = data.groupby('Hour').sum()['Quantity Ordered']
# plot
sales_per_hour = go.Figure(
    go.Scatter(
        x=buying_hours.index,
        y=buying_hours,
        fill="tozeroy",
        hovertemplate='<b>%{x}</b><br>%{y:.0f} commandes<extra></extra>',
        mode='markers+lines',
        marker_color=CUSTOM_BLUE,
    )
)
# update
sales_per_hour.update_yaxes(title=dict(text="Nombre de commande", font_color="grey"),
                            showticklabels=False, showgrid=False, fixedrange=True)
sales_per_hour.update_xaxes(tickfont_color="grey", ticksuffix="h",
                            showgrid=False, zeroline=False, fixedrange=True)
sales_per_hour.update_layout(
    height=600,
    margin=DEFAULT_MARGIN,
    hoverlabel=dict(bgcolor="white", font_size=14),
    hovermode='x',
    shapes=[
        dict(type="rect", xref="x", x0=0, x1=7, yref="paper", y0=0, y1=1,
             fillcolor="grey", opacity=0.2, layer="below", line_width=0),
        dict(type="rect", xref="x", x0=21, x1=23, yref="paper", y0=0, y1=1,
             fillcolor="grey", opacity=0.2, layer="below", line_width=0)
    ],
    annotations=[
        dict(x=3, y=7.5e3, text='<b>Nuit,</b><br> période creuse',
             font=dict(size=14), showarrow=False),
        dict(x=12, y=14202, ax=0,
             text='<b>12h</b> pause déjeuner ', font=dict(size=14)),
        dict(x=19, y=14470, ax=0, text='<b>19h</b> temps libre', font=dict(size=14)),

    ]
)

'''------------------------------------------------------------------------------------------- 
                                            DASH LAYOUT
   ------------------------------------------------------------------------------------------- 
'''


def title(title, subtitle, color=None, subsize=None):
    color = color if color else {}
    subsize if subsize else {}
    title = html.Div(
        [
            html.H3(title, className=" mb-0", style=color),
            html.H5(subtitle, className="text-muted", style=subsize)
        ], className="my-0"
    ),
    return title[0]


app.layout = dbc.Container([
    html.Div(children=[

        dcc.Markdown('''
            # Analyse stratégique d'une entreprise en ligne d'électronique 
            ---
            Dans le présent rapport, nous allons démontrer que la transformation de données brutes en informations 
            exploitables facilite la prise de décisions stratégiques.''', className="mt-5 mb-3"),
        dcc.Markdown('''
            ## Introduction et présentation des données
            Les données utilisées représentent les ventes de produits électroniques réalisées par un commerce en ligne 
            fictif durant l’année 2019. (Voir le tableau 1)'''),
        dbc.Table.from_dataframe(raw_data[:4], striped=True, bordered=False,
                                 borderless=True, hover=True, responsive=True, className="mt-3"),
        dcc.Markdown("**Tableau 1**: présentation du jeu de données",
                     className="text-muted mb-3"),
        dcc.Markdown('''
            Pour chaque commande un ensemble d'informations est collecté sur le client. Par exemple, la première ligne du tableau 
            N° 1 nous indique que le client répertorié par l'ID **295667** a acheté un **Chargeur USB-C** à **11.95$** le **12 décembre 
            2019 à 18:21**, et son adresse de livraison était le **277 Main St, New York City, NY 10001**. 
            La liste ci-dessous résume les données collectées lors d'une commande.'''),
        dbc.Alert(
            dcc.Markdown('''
                ##### Descriptif des informations récoltées lors d'une commandes
                ---
                - **ID**, numéro de commande unique
                - **Produit**, nom du matériel informatique acheté 
                - **Quantité**, nombre d’exemplaires vendus
                - **Prix**, prix unitaire de chaque produit en $
                - **Date**, date et heure de l'achat
                - **Adresse**, adresse de livraison'''),
            color='secondary'),
        dcc.Markdown('''
            Dans les sections suivantes, nous allons transformer cette masse de données en un ensemble d’informations pertinentes. 
            Elles seront ensuite couplées à des éléments provenant de l'écosystème de l'entreprise afin d’élaborer des choix stratégiques 
            réfléchis. La suite du présent rapport se divise en trois parties :  
            
            1. **Positionnement de l'entreprise**, nous analyserons les ventes de produits afin d'améliorer le positionnement de l'entreprise  
            2. **Ciblage marketing**, nous analyserons les lieux de ventes afin d'améliorer la stratégie marketing de l'entreprise  
            3. **Saisonnalité et horaires**, nous analyserons les tendances d'achat des clients afin d'y déterminer les périodes creuses et les 
            périodes de forte affluence'''),

        # 1. POSITIONNEMENT DE L'ENTREPRISE
        dcc.Markdown('''
            ## 1. POSITIONNEMENT DE L'ENTREPRISE
            ---
            Après une rapide présentation des produits vendus et du secteur d’activité, nous découvrirons que les produits *low cost* ont un faible intérêt 
            par rapport aux produits aux prix élevés: (nommés produits *high priced*). Ainsi, nous en déduirons qu’il faut changer de positionnement afin 
            d’améliorer les performances de l’entreprise. Une ébauche d’un nouveau positionnement plus adapté sera proposée à la fin de cet axe.

            **Cette entreprise se situe dans le domaine du e-commerce** et plus spécifiquement dans **la vente en ligne au détail d’appareils et accessoires 
            électroniques**. Il s’agit d’un secteur d’activité dynamique. Ce facteur est important pour la croissance future de l’entreprise car cela 
            lui permet de se développer sans recourir à une baisse des prix. 

            Cette société vend 19 produits différents regroupés en 5 catégories. On compte dans les produits vendus 2 modèles d’ordinateurs, 7 types 
            d’accessoires, 3 modèles de téléphones, 4 modèles d’écrans et 2 modèles de machines à laver. (Voir la figure 1)''', className="my-5"),

        # Figure 1 (parcast): 5 catégories de 19 produits
        title("5 catégories de 19 produits",
              "avec les produits classés par prix décroissant"),
        dcc.Graph(figure=parcats, config=DASH_CONFIG),
        dcc.Markdown("**Figure 1**: découverte des produits",
                     className="text-muted mb-5"),
        dcc.Markdown('''
            **Elle se positionne comme un vendeur généraliste** proposant des produits allant du low cost (vente d’accessoires) au haut de gamme 
            (produits tels que le MacBook Pro)

            Il est important de faire la distinction entre les produits haut de gamme, ciblant les consommateurs aux revenus élevés et 
            les produits *high priced*, une sous catégorie créée par nos soins afin de distinguer les produits du catalogue avec un prix élevé.'''),
        dcc.Markdown('''
            ### Analyse des ventes
            En analysant les ventes de l’année 2019, nous observons que les produits n’ont pas tous la même influence sur le chiffre d’affaires : 
            59% des bénéfices sont réalisés par seulement 4 de nos 19 produits. De l’autre côté du classement, les 5 produits les moins profitables 
            représentent moins de 3.1% des bénéfices. (Voir la figure 2)''',
                     className='my-5'),

        # Figure 2 (horizontal plot): classement des produits
        title("Classement des produits",
              "selon leur importance pour le chiffre d'affaire"),
        dcc.Graph(figure=product_bar, config=DASH_CONFIG),
        dcc.Markdown("**Figure 2**: Classement des produits",
                     className="text-muted"),
        dcc.Markdown("""
            On remarque une forte variation de l’importance de certaines marchandises sur le chiffre d’affaires. En effet, les produits *high priced*
            occupent une part plus importante que les produits d’entrée de gamme qui n’ont que très peu d’impact sur le CA.

            Continuons notre analyse en examinant la corrélation entre le prix de vente d'un produit et son chiffre d’affaires en 2019. (Voir la figure 3)""",
                     className="my-5"),

        # Figure 3 (scatter): relation prix volume de ventes
        title("Volume de ventes des produits selon leur prix",
              "la superficie des bulles correspond au nombre de ventes"),
        dcc.Graph(figure=scatter_plot_product, config=DASH_CONFIG),
        dcc.Markdown("**Figure 3**: relation entre le prix et le volume des ventes",
                     className="text-muted mb-5"),
        dcc.Markdown('''
            Des tendances intéressantes ressortent de ce graphique :
            - **Les produits avec un prix élevé ont tendance à avoir un volume de ventes important**. La bulle bleue en haut à droite de la figure 3 correspond 
            au Macbook Pro, un ordinateur haut de gamme dont la profitabilité est la plus élevée parmi tous les produits du catalogue. De l’autre côté de la 
            figure, le groupe de bulles orange correspond aux accessoires low cost dont le prix est bas et dont les bénéfices sont réduits. 

            - **La catégorie des machines à laver ramène peu de bénéfices**. S'agissant de produits lourds et volumineux, leur livraison est délicate. Ainsi, 
            leur intérêt pour le catalogue 2020 est discutable. 

            - **Les produits hauts de gamme sont en minorité**. On ne compte qu’un seul produit haut de gamme dans la catégorie des ordinateurs et aucun dans 
            la catégorie des téléphones, deux catégories qui sont pourtant extrêmement importantes pour le chiffre d’affaires. Il serait intéressant 
            de diversifier ce genre de produits. Nous aborderons cet aspect de notre rapport dans l’une des sections suivantes.

            - **L’aspect des bulles varie en fonction du nombre de ventes**. Les accessoires low cost sont des produits au nombre de ventes élevé, leurs 
            bulles sont étendues, tandis que les produits  ont une superficie de bulles moindre, leur nombre de ventes étant plus bas. Le nombre de ventes est 
            un paramètre intéressant parce qu’il nous permet d'évaluer le temps alloué à la préparation des commandes de chaque produit.

            Comparons le nombre de ventes et l’influence sur le chiffre d’affaires pour les produits low cost et *high priced*. 
            (Voir la figure 4)''',
                     className="my-5"),

        # Figure 4 : Comparaison high priced low cost
        dbc.Row([
            dbc.Col(title("Accessoires low cost", "Casque sans file, Chargeur USB-C, Chargeur lumineux, Piles AA & AAA",
                color={"color": CUSTOM_ORANGE}, subsize={"font-size": "0.8rem"}
            )),
            dbc.Col(title("Produits high priced", "Macbook Pro, iPhone XR, Samsung Galaxy n10, Dell XPS 13",
                          color={"color": CUSTOM_BLUE}, subsize={"font-size": "0.8rem"}
                          )),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=low_cost_viz, config=DASH_CONFIG)),
            dbc.Col(dcc.Graph(figure=high_cost_viz, config=DASH_CONFIG))
        ]),
        dcc.Markdown("**Figure 4**: Comparaison du chiffre d'affaire et du nombre de ventes des produits high priced et low cost",
                     className="text-muted mb-5"),
        dcc.Markdown("""
            Deux informations sont à retenir de cette figure :
            - **Les produits *high priced* sont très intéressants**. Très importants pour le chiffre d’affaires (58%), le temps alloué à la préparation des 
            commandes de ces produits reste relativement bas, environ 10%. Il s’agit de produits nécessitant peu de main d’œuvre et dont la profitabilité 
            est élevée. Diversifier le catalogue des produits *high priced* en 2020 semblerait intéressant.

            - **Les accessoires low-cost ont peu d'intérêt**. Les chiffres parlent d’eux-mêmes, 60% des ventes ne représentent que 3% du chiffre d’affaires. Ces 
            produits représentent un temps de travail considérable en termes de préparation de commandes, mais ne génèrent que peu de bénéfices. Leur 
            renouvellement dans le catalogue de 2020 est discutable. 

            Néanmoins, il est important de vérifier la proportion de commandes composées de plus de deux produits. En effet, 
            si le nombre de produits achetés par commande est élevé, il est probable qu’une partie des clients venus acheter un accessoire finissent 
            par repartir avec d’autres produits. Dans ce cas, arrêter la vente d'accessoires low-cost en 2020 pourrait impacter les ventes des autres 
            catégories. **Pour cette étude seulement 2.7% des commandes sont composées de plusieurs produits dont au moins un acccessoire. Ainsi
            la vente d'accessoires low-cost impacte légèrement les ventes des autres catégories**."""),
        dcc.Markdown("""
            ### Analyse de l'environnement
            L’analyse de l’environnement confirme la validité de notre proposition de réorienter l’offre. **Le secteur du commerce en ligne d’accessoires fait face 
            à une forte concurrence** avec le développement du dropshipping, non négligeable dans le segment des accessoires, et l’arrivée d’acteurs comme Alibaba 
            qui proposent les accessoires à des prix extrêmement bas. Le marché des accessoires est donc arrivé à saturation, il n’est plus viable à court terme 
            pour les entreprises de taille moyenne, sachant qu’il devient très difficile de conserver la rentabilité ou d’acquérir de nouvelles parts de marché.

            **Concernant le segment haut de gamme, la compétition est moins importante pour les entreprises de taille moyenne**. Les barrières à l’entrée sur ce 
            segment sont plus fortes à cause de l’investissement de départ qui est plus élevé que sur le segment des accessoires. L’expertise requise pour la 
            vente de ces appareils empêche une arrivée massive de nouveaux acteurs recherchant une rentabilité rapide à très court terme. Ainsi, un avantage 
            concurrentiel est défendable sur ce secteur à long terme.

            Concernant la vente de machine à laver, il peut être intéressant de considérer une stratégie de sortie progressive, compte tenu de la 
            faible dynamique de ce secteur sur le moyen et long terme.""",
                     className="mt-5"),
        dbc.Alert(
            dcc.Markdown('''
                ### Recommandation stratégique
                ---
                En analysant les ventes de 2019 ainsi que l’environnement macroéconomique on voit qu’il est beaucoup plus rentable de s’orienter vers des produits 
                haut de gamme et d’abandonner les produits low cost. Voici nos trois recommandations afin de changer de positionnement :
                
                - **Arrêter la vente de produits low-cost**. Soumis à une forte concurrence, ces produits représentent un temps de travail considérable en termes de 
                préparation de commandes pour une profitabilité faible (60% des ventes pour seulement 3.1% du chiffre d’affaires en 2019). Leur suppression du 
                catalogue permettrait également de réduire les coûts logistiques. 
                
                - **Diversifier la vente des produits haut de gamme**. Avec des marges plus importantes et une concurrence moindre, ces produits nécessitent peu de 
                temps de travail pour une rentabilité élevée (seulement 10% des ventes pour un total de 58% du chiffre d’affaires en 2019).

                - **Arrêter la vente de machines à laver**. Ce sont des produits avec une faible influence sur le chiffre d’affaires. Leur livraison est en outre 
                complexe en raison du poids et de la taille des produits.

                L’objectif visé par la recomposition de l’offre est de changer de groupe stratégique en passant du statut de vendeur généraliste au statut 
                de vendeur de produits électroniques haut de gamme.'''),
            color='secondary', className="my-5"),
        # 2. CIBLAGE MARKETING
        dcc.Markdown('''
            ## 2. CIBLAGE MARKETING
            ---
            Le service de livraison de ce commerce en ligne est disponible dans 9 villes américaines, dont New York, Los Angeles ou encore San Francisco... 
            A l'aide des figures ci-dessous, on observe que San Francisco est la ville qui a réalisé le plus important volume de ventes en 2019.'''),
        # Figure 5 (map): carte des lieux de ventes
        dcc.Graph(figure=map_plot, config={
                  **DASH_CONFIG, **{'staticPlot': True}}),
        dcc.Markdown("**Figure 5**: cartographie des lieux de vente",
                     className="text-muted mb-5"),
        # Figure 6 (horizontal bar): classement des lieux de ventes
        title("Classement des villes",
              "selon leur importance pour le chiffre d'affaire en 2019"),
        dcc.Graph(figure=city_rank, config=DASH_CONFIG),
        dcc.Markdown(
            "**Figure 6**: classement des villes selon leur volume de ventes", className="text-muted"),
        dcc.Markdown('''
            Maintenant que nous savons que San Francisco constitue le marché le plus lucratif, il nous faut en comprendre les raisons, afin d'améliorer notre 
            stratégie marketing. 

            De manière générale, **comprendre les facteurs de réussite d'un lieu est un élément essentiel pour développer le chiffre d'affaires 
            sur le long terme.** Cette compréhension est nécessaire pour cibler de nouveaux marchés ou pour adapter notre stratégie à des lieux avec 
            un faible volume des ventes.''',
                     className="my-5"),
        dcc.Markdown('''
            #### **Qu’est ce qui fait de San Francisco une ville aussi performante ?**

            Nous pouvons nous faire une idée des facteurs de réussite d’une ville en nous appuyant sur la corrélation entre notre indicateur de performance 
            (le chiffre d’affaires annuel par ville) et des facteurs externes tels que le nombre d’habitants ou le taux de travailleurs dans le secteur 
            de la technologie. 

            **Le vrai défi consiste à identifier les facteurs extérieurs qui influencent les performances**. Une bonne connaissance du domaine est 
            indispensable pour déterminer ces facteurs de réussite. Dans le présent rapport, nous nous sommes focalisés sur la corrélation entre :
            - **Le volume des ventes et le salaire moyen**
            - **Le volume des ventes et le budget publicitaire**

            L'analyse des corrélations nous permettra de vérifier certaines hypothèses concernant notre clientèle. Les appareils électroniques ne sont 
            pas des produits de première nécessité, de ce fait nous supposons que ce sont des biens recherchés par des personnes ayant un niveau de vie 
            moyen ou élevé. Puisque le salaire moyen est un bon indicateur du niveau de vie, nous supposons qu’il existe une forte corrélation entre le 
            salaire moyen au sein d’une ville et le volume de ventes qui y est réalisé. Cependant la figure 7 nous montre le contraire :''',
                     className="mb-5"),
        # Figure 7 (scatter): relation volume de ventes salaire moyen
        title("Aucune corrélation avec le salaire moyen",
              "relation entre le volume des ventes et le salaire moyen"),
        dcc.Graph(figure=sales_income, config=DASH_CONFIG),
        dcc.Markdown("**Figure 7**: relation entre le salaire moyen et le volume de ventes",
                     className="text-muted mt-4"),
        dcc.Markdown('''
            Par exemple, la ville de Seattle avec le salaire moyen le plus élevé de 39.3k $ compte parmi les villes avec le volume de ventes le plus bas, 
            2.7 M $. Nous pouvons en tirer la conclusion que le salaire moyen constitue un mauvais indicateur pour évaluer le volume des ventes de cette 
            entreprise.

            En s'appuyant sur la figure 8, nous constatons que le budget alloué à la publicité en 2019 par ville est étroitement lié au volume des ventes. 
            Il semblerait que le volume des ventes augmente au fur et à mesure que les produits gagnent en visibilité. Nous remarquons cependant que les 
            chiffres commencent à stagner lorsque le budget devient trop élevé.''',
                     className="mt-5 mb-5"),
        # Figure 8 (scatter): relation volume des ventes budget pub
        title("Forte corrélation avec le budget publicitaire",
              "relation entre le volume des ventes et le budget publicitaire"),
        dcc.Graph(figure=sales_ads, config=DASH_CONFIG),
        dcc.Markdown("**Figure 8**: relation entre le volume de ventes et le budget publicitaire",
                     className="text-muted mb-5 mt-3"),
        dcc.Markdown('''
            Augmenter la visibilité de nos produits à l'aide de campagnes publicitaires paraît comme une solution intéressante pour augmenter les ventes. 
            En effet, une augmentation des dépenses de quelques milliers de dollars permettrait d’amener plusieurs millions supplémentaires en chiffre d’affaires. 
            Il est donc extrêmement intéressant d’augmenter les charges publicitaires en ciblant les villes se trouvant sous un certain seuil de profitabilité. 
            A travers ce ciblage publicitaire, l’enjeu va être de se développer au niveau régional afin de devenir un acteur plus important et d’installer 
            progressivement une image de marque attrayante, de consolider la clientèle.

            Pour mesurer l’efficacité de notre stratégie publicitaire, il est important de déterminer nos objectifs. Pour cela, nous allons utiliser San Francisco 
            comme ville de référence afin de mesurer l’évolution des ventes dans les villes cibles. L’utilisation d’une ville de référence pour définir un objectif 
            de développement permet de mesurer efficacement le retour sur investissement qu’apporte la publicité dans nos villes cibles.'''),
        dbc.Alert(
            dcc.Markdown('''
                ### Recommandation stratégique
                ---
                **Augmenter les dépenses publicitaires dans les zones ayant un faible volume de ventes** afin d’amener plus de rentabilité 
                et de se positionner comme un acteur régional dans le secteur d'activité'''),
            color='secondary', className="my-5"),
        # 3. SAISONNALITÉ ET HORAIRES
        dcc.Markdown('''
            ## 3. SAISONNALITÉ ET HORAIRES
            ---
            **Une meilleure compréhension de l'évolution mensuelle du chiffre d'affaire durant l'année 2019 nous serait utile pour une meilleure gestion 
            du stock**. La figure 9 souligne la présence d'un pic des ventes en décembre. Durant cette période de fêtes, le chiffre d'affaires atteint un 
            maximum parce que beaucoup de produits électroniques sont achetés en guise de cadeau. Nous remarquons aussi deux périodes creuses durant l'année. 
            La première est située après les fêtes de fin d'année. En effet, les gens ont tendance à économiser pendant les premiers mois de l'année afin de 
            pallier les dépenses de fin d'années. La deuxième a lieu pendant la période des vacances scolaires. Durant cet intervalle, la plupart des dépenses 
            sont utilisées pour les vacances et les frais dans les autres secteurs sont réduits.''',
                     className="mb-5"),
        # Figure 9 (line): evolution du ca mensuelle
        title("Evolution temporelle du volume des ventes",
              "regroupement mensuel pour l’année 2019"),
        dcc.Graph(figure=ca_per_month, config=DASH_CONFIG),
        dcc.Markdown("**Figure 9**: évolution du chiffre d'affaires durant l'année 2019",
                     className="text-muted mt-3"),
        dcc.Markdown('''
            Afin d'avoir du stock disponible toute l'année, il faut prévoir un nombre de produits plus important pour la période de Noël.
            
            En étudiant l'heure d'achat de nos produits à l'aide de la figure 11, nous constatons que nos clients ont tendance à passer une 
            commande pendant la pause déjeuner et leur temps libre avant le dîner. On en déduit que le meilleur moment pour afficher de la publicité est 
            à 12h et à 19h.''',
                     className="my-5"),
        # Figure 10 (line): Ventes par heure
        title("Heures d'achat des produits",
              "regroupement horraire pour l’année 2019"),
        dcc.Graph(figure=sales_per_hour, config=DASH_CONFIG),
        dcc.Markdown("**Figure 10**: nombre de ventes par heures",
                     className="text-muted"),
        dbc.Alert(
            dcc.Markdown('''
                ### Recommandation stratégique
                ---
                - **Augmenter les stocks pour Noël**, afin d'éviter l'indisponibilité de certains produits.
                - **Favoriser l’affichage de la publicité pour midi et 19h**, un affichage personnalisé peut être réalisé pour chaque ville et 
                nécessite une investigation au cas par cas.'''),
            color='secondary', className="my-5"),
    ])
], fluid=True, className='container', style={"background-color": "white"})

if __name__ == '__main__':
    app.run_server(debug=False)
