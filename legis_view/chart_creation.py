import os
import random

from wordcloud import WordCloud
import pygal

import VARS as vars


def create_contribution_chart(contributions_list, election_year):
    contrib_bar = pygal.HorizontalBar(style=vars.FINANCE_BAR_STYLE,
                                      max_scale=4,
                                      js=[],
                                      print_values=True,
                                      print_values_position='center',
                                      value_formatter=lambda x: '${:20,.2f}'.format(x))
    contrib_bar.title = 'Total Contributions By Size - ' + str(election_year)
    for contribution in contributions_list:
        for i, contrib in enumerate(contribution['results']):
            if i == 0:
                contrib_bar.add(str(contrib['size']) + '-' + str(contribution['results'][i + 1]['size']),
                                contrib['total'])
            elif i == len(contribution['results']) - 1:
                contrib_bar.add(str(contrib['size']) + '+', contrib['total'])
            else:
                contrib_bar.add(str(contrib['size']) + '-' + str(contribution['results'][i + 1]['size']),
                                contrib['total'])
    return contrib_bar.render_data_uri()


def create_word_cloud(words, id):
    cloud = WordCloud(font_path=vars.CUSTOM_FONT, height=400,
                      width=400, background_color="#f5f5f5").generate(' '.join(words))
    filename = '{}.png'.format(id)
    cloud.recolor(color_func=turq_color_func, random_state=3).to_file(os.path.join('clouds', filename))


def turq_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return random.choice(vars.PYGAL_COLORS)
