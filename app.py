# """
# Created on: see version log.
# @author: RiGonz
# coding: utf-8
# This script reads input from the user and plots the estimated probability of
# survival from life tables applicable to Spain.
# The input data is:
#     - sex,
#     - age,
#     - year of calculation,
#     - province (if detailed data is available for the year, otherwise for ESP).
# The plot includes two parts:
#     - the survival function until the input age,
#     - the conditional probability of reaching an older age.
# The script is the core of a dynamic webpage (Shiny).
# Based on script #260 from CENSOS, adapted to an HTML output.
#
# Version log.
# R0 20241002
# - first trials, seems to work well (local python).
# R1 20241005
# - input files are json instead of pkl
# - moved to web (via bottle)
# R2 20241201
# - moved to web (via Shiny)
# - input file is npy instead of json
# R3 20241210
# - input file is a single csv dataframe instead of npy, with age as columns and a combined index YYYY-GG-S.
# TODO:
# -
# """
# %% Import libraries.
from shiny import App, render, ui
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# %% Local functions.
def f_create_chart(dat_df, sex, age, yea, geo):
    """
    Generates a two vertical axes chart with survival probabilities.
    The first part plots an absolute survival rate: the probability of
    exceeding a given age. The second shows a conditional probability: if a
    given age is reached, the probability of dying at any greater age.
    Receives:
    - dat_df, a df with national and provincial survival data (with index a YYYY-GG-S code
    and columns 0-100 years of age; before 1975 only YYYY-00-S is available),
    - sex, str [M, F, T],
    - age, int [0-99],
    - yea, int [1900-2022],
    - geo, str (the 2-digit code of the provinces, acc. to INE, plus a 3-char code,
           or 00-ESP for Spain)
    Returns:
    - the chart.
    Uses:
    - matplotlib.pyplot as plt
    - math.ceil
    """
    fig, ax1 = plt.subplots()
    plt.figure(dpi=500, figsize=(10, 8), layout='constrained')

    # Absolute probability of exceedance:
    sur0_s = dat_df.loc[str(yea) + '-' + geo[0:2] + '-' + sex] / 100000
    ax1.plot(range(age+1), sur0_s[0: age+1], c='r', lw=1)
    ax1.plot(range(age, 100+1), sur0_s.iloc[age:], c='r', lw=0.5, ls='--')
    ax1.plot([age, age], [0, sur0_s.iloc[age]], c='k', lw=0.5, ls='--')

    # Conditional probability of death:
    sur1_s = -sur0_s.diff()
    sur2_s = sur1_s / sur1_s[age+1:].sum()
    ax2 = ax1.twinx()
    for idx in range(age+1, 100+1):
        ax2.plot([idx, idx], [0, sur2_s.iloc[idx-1]], c='b', lw=1)

    # Commons:
    # fig.tight_layout()
    ax1.set_title(f'año: {yea}, sexo: {sex}, edad: {age}, geo: {geo}', loc='right')
    ax1.set_xlabel('Edad')
    ax1.set_ylabel('Probabilidad de exceder', color='r')
    ax2.set_ylabel('Probabilidad condicional', color='b')
    ax1.tick_params(axis='y', labelcolor='r')
    ax2.tick_params(axis='y', labelcolor='b')
    ax1.set_ylim(0, 1)
    ax2.set_ylim(0, 0.05*np.ceil(sur2_s[age+1:].max() / 0.05))
    ax1.set_xticks(range(0, 100+1, 10))
    ax1.set_yticks([x/100 for x in range(0, 100+1, 10)])
    ax1.grid(which='both', alpha=0.5, linewidth=0.2, color='grey')

    return fig


# %% Common auxiliaries.
cod2pro_d = {
    '01': 'ALA', '02': 'ALB', '03': 'ALI', '04': 'ALM', '05': 'AVI',
    '06': 'BAD', '07': 'BAL', '08': 'BAR', '09': 'BUR', '10': 'CAC',
    '11': 'CAD', '12': 'CAS', '13': 'CIU', '14': 'COR', '15': 'LAC',
    '16': 'CUE', '17': 'GER', '18': 'GRA', '19': 'GUA', '20': 'GUI',
    '21': 'HUL', '22': 'HUE', '23': 'JAE', '24': 'LEO', '25': 'LER',
    '26': 'RIO', '27': 'LUG', '28': 'MAD', '29': 'MAL', '30': 'MUR',
    '31': 'NAV', '32': 'ORE', '33': 'AST', '34': 'PAL', '35': 'PLM',
    '36': 'PON', '37': 'SAL', '38': 'TEN', '39': 'CAN', '40': 'SEG',
    '41': 'SEV', '42': 'SOR', '43': 'TAR', '44': 'TER', '45': 'TOL',
    '46': 'VLC', '47': 'VLL', '48': 'VIZ', '49': 'ZAM', '50': 'ZAR',
    '00': 'ESP'}

# %% Read survival data, from script #252.
# Get data:
# RootDir = 'E:/0 DOWN/00 PY RG/HTML/SHINY/CENSOS/'
# fname = RootDir + '252_Survival_data_ESP.csv'
fname = '252_Survival_data_ESP.csv'
dat_df = pd.read_csv(fname, index_col=0)
# del RootDir
del fname

# %% UI definition.
ui.head_content(
    ui.tags.meta(name="robots", content="noindex"))

app_ui = ui.page_fluid(
    ui.panel_title(ui.h2("TABLAS DE MORTALIDAD EN ESPAÑA, 1900-2022")),
    ui.row(
        ui.card(
            ui.h3("""Presentación"""),
            ui.HTML("""
                <p>Las tablas de mortalidad (o supervivencia, <i>life tables</i>) ofrecen una visión estadística de las tasas de deceso en función de la edad. Es a partir de ellas que se calculan las esperanzas de vida al nacer, o a cualquier otra edad.</p>
                <p>En España disponemos de tablas detalladas que cubren el período 1900-2022 a nivel nacional, y desde 1975 para las provincias.</p>
                <p>Además del interés personal, quizás morboso, de ver la duración esperada de vida que le queda a uno, esta serie de tablas permite multiples comparaciones a varios niveles: temporal, vital, biológico y geográfico. A un igualitarista racionalista y riguroso hasta le podrían servir para deducir que quizás convenga ralentizar el estudio de enfermedades severas exclusivas de mujeres, o de mayor prevalencia en ese sexo, hasta igualar, a la baja, su esperanza de vida con la del hombre.</p>
                <p>Esta aplicación permite visualizar dos grupos de resultados:</p>
                <ul>
                    <li>la probabilidad de exceder una edad determinada, y,</li>
                    <li>bajo la condición de haber alcanzado esa edad, la probabilidad de deceso a edades superiores.</li>
                </ul>
                <p>Los resultados dependen de cuatro parámetros:</p>
                <ol>
                    <li>sexo,</li>
                    <li>edad de cálculo,</li>
                    <li>año de cómputo, y</li>
                    <li>ámbito geográfico.</li>
                </ol>
                <p>Para los datos 1-3 el formulario de entrada guía al usuario; con respecto al ámbito geográfico debe introducirse un código numérico: 0 para España o, a partir de 1975, el código de dos dígitos asignado por el INE para las provincias (<a href="https://www.ine.es/daco/daco42/codmun/cod_provincia_estandar.htm">INE</a>).</p>
                <p>Los datos originales son del INE (<a href="https://www.ine.es/inebaseweb/libros.do?tntp=206842">ESP 1900-1970</a>, <a href="https://www.ine.es/jaxiT3/Tabla.htm?t=27150">ESP 1975-90</a>, <a href="https://www.ine.es/jaxiT3/Tabla.htm?t=27153">ESP 1991-2022</a>, <a href="https://www.ine.es/jaxiT3/Tabla.htm?t=27152">PRO 1975-90</a>, <a href="https://www.ine.es/jaxiT3/Tabla.htm?t=27155">PRO 1991-2022</a>). Con los anteriores a 1990 he tenido que interpolar y extrapolar por diferentes motivos para conseguir mallas de 1 año tanto en edades como en fechas. Algunas extrapolaciones, especialmente en el período 1975-90 para edades superiores a 85 años, no parecen demasiado buenas, pero tampoco creo que esto sea algo gravísimo para los propósitos de esta página.</p>
                <p>Una asunción subyacente quizás merezca un comentario adicional. Las tablas de supervivencia se interpretan naturalmente como el seguimiento longitudinal de cohortes hasta su extinción. Naturalmente también, esto no es viable porque no conviene esperar unos 100 años para poder construir cada tabla. La alternativa es el uso de cohortes sintéticas bajo la hipótesis de estabilidad demográfica; es decir, la tabla del año, digamos, 2022 está construida bajo la asunción de que las condiciones prevalentes en 2022 persisten hasta la extinción de la cohorte correspondiente a ese año.</p>
                <p>La idea original viene de <a href="https://flowingdata.com/2015/09/23/years-you-have-left-to-live-probably/">flowingdata</a>, aunque estaba buscando una excusa para hacer ¡mi primera! página web dinámica. Una primera versión apareció en <a href="https://rigonz.pythonanywhere.com/">pythonanywhere</a>; esta en Shiny es algo más pintona, pero el núcleo no ha cambiado.</p>
                <p>Mantengo el <i>caveat</i> principal: la página no está pensada para dispositivos <i>móviles</i>.</p>"""
            )
        )
    ),
    ui.row(
        ui.column(3,
            ui.h3("""Datos de entrada"""),
            ui.input_select("sex", "Sexo:", choices={'M': 'hombre', 'F': 'mujer', 'T': 'todos'}, width='150px'),
            ui.input_numeric("age", "Edad (0-99):", value=50, min=0, max=99, step=1, width='150px'),
            ui.input_numeric("yea", "Año (1900-2022):", value=2022, min=1900, max=2022, step=1, width='150px'),
            ui.input_numeric("geo", "Geografía:", value=50, min=0, max=50, step=1, width='150px'),
        ),
        ui.column(9,
            ui.h3("""Resultados"""),
            ui.output_plot("plot")
        ),
    )
)


# %% Serder definition.
def server(input, output, session):
    @render.plot(width=800)
    def plot():
        sex = input.sex()
        age = int(input.age())
        yea = int(input.yea())
        geo = int(input.geo())
        if yea < 1975:
            geo = 0
        geo_s = str(geo).zfill(2)
        geo_s += '-' + cod2pro_d[geo_s]
        fig = f_create_chart(dat_df, sex, age, yea, geo_s)
        return fig


app = App(app_ui, server)
