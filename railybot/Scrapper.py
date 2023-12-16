import pandas as pd
from bs4 import BeautifulSoup
import requests

'''
dict_format
'''


def get_complete_url(form: list):
    if form[0]:

        return '{}/{}/{}/{}/{}/{}'.format(form[1],
                                          form[2],
                                          form[3],
                                          form[4],
                                          form[5],
                                          form[6],
                                          )
    else:
        return '{}/{}/{}/{}'.format(form[1],
                                    form[2],
                                    form[3],
                                    form[4],
                                    )


class TicketScrapper:
    URL = 'https://ojp.nationalrail.co.uk/service/timesandfares/'

    def __init__(self, form: list):
        self.info = form
        self.url = TicketScrapper.URL + get_complete_url(self.info)
        print(self.url)
        self.web_scr = BeautifulSoup(requests.get(self.url).content, 'lxml')
        self.results_scr = self.web_scr.find(id='ctf-results')
        self.tables_scr = [self.results_scr.find(id='oft'), self.results_scr.find(id='ift')]
        self.schedule = self.get_timetables()

    def get_dates(self):
        dates = self.results_scr.find_all('h3')
        dates = [x.get_text(strip=True).split(' ')[1].replace('on', '') for x in dates]
        if dates.__len__() > 1:
            dates_dict = {
                'oft': dates[0],
                'ift': dates[1],
            }
        else:
            dates_dict = {
                'oft': dates[0],
            }

        return dates_dict

    def get_timetables(self):
        data = []
        dates_dict = self.get_dates()
        for table in self.tables_scr:
            if table is not None:
                rows = table.find_all('tr')
                for row in rows:
                    if row.attrs.__len__() == 0 or 'class' not in row.attrs.keys() or 'mtx' not in row.attrs['class']:
                        continue
                    train_info = [table.attrs['id'], dates_dict[table.attrs['id']]]
                    cols_count = 0
                    cols = row.find_all('td')
                    for col in cols:
                        cols_count += 1
                        col_text = col.get_text(strip=True).replace('\n', '').replace('\t', '')
                        if cols_count == 1 or cols_count == 3:

                            train_info.append(col_text[col_text.index('[') + 1:col_text.index(']')])
                            train_info.append(col_text[col_text.index(':') - 2:col_text.index(':') + 3])
                            try:
                                train_info.append(col_text[col_text.index('Platform') + 'Platform'.__len__()])
                            except:
                                train_info.append('NA')
                        elif cols_count == 2:
                            train_info.append(col_text[col_text.index(' ') - 1])
                            train_info.append(col_text[:col_text.index(' ') - 1])

                        elif cols_count == 5:
                            if 'single fare' in col_text.lower():
                                if 'cheapest fare' in col_text.lower():
                                    fare_index = col_text.lower().index('single fare')
                                    train_info.append('cheapest fare')
                                    train_info.append(col_text[fare_index + 'single fare'.__len__():][
                                                      1:col_text[fare_index + 'single fare'.__len__():].index('.') + 3])
                                else:
                                    fare_index = col_text.lower().index('single fare')
                                    train_info.append('single fare')
                                    try:
                                        train_info.append(col_text[fare_index + 'single fare'.__len__():][
                                                          1:col_text[fare_index + 'single fare'.__len__():].index(
                                                              '.') + 3])
                                    except:
                                        if self.info[0]:
                                            class_name = 'opreturn'
                                        else:
                                            class_name = 'opsingle'
                                        fare = col.find_all('label', {'class', class_name})[0].get_text().replace('\n',
                                                                                                                  '')
                                        train_info.append(fare[1:])

                            elif 'cheapest fare' in col_text.lower():
                                fare_index = col_text.lower().index('cheapest fare')
                                train_info.append('cheapest fare')
                                train_info.append(col_text[fare_index + 'cheapest fare'.__len__():][
                                                  1:col_text[fare_index + 'cheapest fare'.__len__():].index('.') + 3])
                            data.append(train_info)

        dataframe = pd.DataFrame(data,
                                 columns=['id', 'date', 'dep_station', 'dep', 'platform_dep', 'changes', 'duration',
                                          'arr_station', 'arr', 'platform_arr',
                                          'type', 'fare'])
        return dataframe

    def get_chepeast_fare(self):
        full_str = ''
        chepeast = self.schedule.loc[self.schedule['type'] == 'cheapest fare'].copy()
        chepeast['fare'] = chepeast['fare'].astype(float)
        for key, row in chepeast.iterrows():
            if row['id'] == 'oft':
                full_str += 'Outward Train\n' \
                            'Date: {}\n' \
                            'Stations:\n' \
                            'From {} to {}\n' \
                            'Departure Time: {}\n' \
                            'Arrival Time: {} ({})\n\n'.format(row['date'],
                                                               row['dep_station'],
                                                               row['arr_station'],
                                                               row['dep'],
                                                               row['arr'],
                                                               row['duration'])
            else:
                full_str += 'Return Train\n' \
                            'Date: {}\n' \
                            'Stations:\n' \
                            'From {} to {}\n' \
                            'Departure Time: {}\n' \
                            'Arrival Time: {} ({})\n\n'.format(row['date'],
                                                               row['dep_station'],
                                                               row['arr_station'],
                                                               row['dep'],
                                                               row['arr'],
                                                               row['duration'])

        full_str += 'PRICE: £{}\n\n'.format(chepeast.sum()['fare'])
        full_str += 'LINK:\n {}'.format(self.url)
        return full_str


# list_ = [False, 'London', 'Manchester', '120122/0700', 'dep', '', '']
# a = TicketScrapper(list_)
# print(a.get_chepeast_fare())
