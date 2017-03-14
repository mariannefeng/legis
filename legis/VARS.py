import datetime
import os

from pygal.style import Style

DEFAULT_FONT = 'Helvetica-Light'
CUSTOM_FONT = os.path.join('static', 'Helvetica-Light.ttf')
BULMA_COLORS = ['is-success', 'is-info', 'is-primary', 'is-danger']

BILL_CHART_STYLE = Style(background='transparent',
                    plot_background='transparent',
                    transition='400ms ease-in')

FINANCE_BAR_STYLE = Style(background='transparent',
                          plot_background='transparent',
                          transition='50ms ease-in',
                          opacity='.6',
                          title_font_size=30,
                          title_font_family=DEFAULT_FONT,
                          legend_font_size=20,
                          legend_font_family=DEFAULT_FONT,
                          label_font_size=15,
                          label_font_family=DEFAULT_FONT,
                          major_label_font_family=DEFAULT_FONT,
                          no_data_font_family=DEFAULT_FONT,
                          value_font_family=DEFAULT_FONT,
                          value_font_size=23)

PYGAL_COLORS = ['rgb(186,104,200)', 'rgb(247,123,114)', 'rgb(121,133,203)', 'rgb(77,181,172)', 'rgb(149,117,204)',
                'rgb(81,118,148)', 'rgb(224, 94, 85)', 'rgb(78, 150, 143)']

WHAT_WERE_DOING_MD = 'static/md/what_happen.md'
THANK_YOU_MD = 'static/md/thank_you.md'

DATA_US_REPS_PATH = 'us/my_reps'
DATA_STATE_REPS_PATH = 'state/my_reps'
