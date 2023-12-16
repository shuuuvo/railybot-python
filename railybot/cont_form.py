import pandas as pd

from stations_db import get_closest_city, get_db
import spacy
import datefinder
from Scrapper import TicketScrapper as ts

nlp = spacy.load('en_core_web_sm')


def scrapperPlace(text, db):
    type_pass = ['DET']
    input_words = []
    doc = nlp(text)
    stations_list = []
    for token in doc:
        input_word = token.text
        pos = token.pos_
        input_words.append(input_word)
        if pos in type_pass:
            continue
        closest_match = get_closest_city(input_word, db.stack().tolist())
        if closest_match is not None:
            if len(closest_match) != 0:
                matching_df = db[db.isin([closest_match])].stack()
                try:
                    df_match = \
                        matching_df[matching_df.index.get_level_values(1).isin(['Station Name'])].index[0][
                            0]
                    # print(db.loc[df_match, 'CRS Code'])
                    stations_list.append({'code': db.loc[df_match, 'CRS Code'],
                                          'index': df_match,
                                          'text': input_word,
                                          'index_txt': input_words.index(input_word),
                                          'prev': input_words[
                                              input_words.index(input_word) - 1]})
                except:
                    df_match = set(db[db.isin([closest_match])].stack().index.get_level_values(0))
                    stations_list.append({'code': closest_match,
                                          'index': df_match,
                                          'text': input_word,
                                          'index_txt': input_words.index(input_word),
                                          'prev': input_words[input_words.index(input_word) - 1]})

    return stations_list


def scrapperReturn(text):
    doc = nlp(text)
    listing_return = ['come', 'return', 'round', 'until']
    listing_one = ['one way', 'oneway', 'one-way', 'one_way']
    for token in doc:
        if token.lemma_.lower() in listing_return:
            return True, True

    if any(string in text.lower() for string in listing_one):
        return True, False
    else:
        return False, False


def scrapperDates(text):
    day_moments = {
        'early': '6am',
        'morning': '6am',
        'afternoon': '2pm',
        'evening': '6pm',
        'late': '6pm'
    }
    matches = list(datefinder.find_dates(text))
    if len(matches) == 1:
        for match in matches:
            time = match.strftime('%d%m%y/%H%M')
            return time

    else:
        return None


class TicketInfo:
    SEARCHTYPE = ['arr', 'dep', 'last', 'first']
    STATES_DB = pd.read_csv('_states/_ticket_states.csv', index_col='s')

    def __init__(self, *kwargs):
        self.db = get_db()
        self.stations = {
            'origin': '',
            'destination': '',
        }
        self.dates = {
            'one_way': '',
            'return': '',
        }
        self.search_type = {
            'one_way': TicketInfo.SEARCHTYPE[1],
            'return': TicketInfo.SEARCHTYPE[1],
        }
        self.return_tr = False
        self.checklist = {'origin': False,
                          'destination': False,
                          'tr_date': False,
                          're_date': False,
                          'return': False,
                          'search_type': True}
        self.text_request_type = ''

        if len(kwargs) > 0:
            self.first_text_(kwargs[0])

    def get_state(self):
        return int(''.join([str(int(x)) for x in self.checklist.values()])[:-1])

    def add_origin(self, city):
        self.stations['origin'] = city

    def add_trip_date(self, date):
        self.dates['one_way'] = date

    def add_return_date(self, date):
        self.dates['return'] = date

    def accept_status(self, argument):
        self.checklist[argument] = True

    def add_destination(self, city):
        self.stations['destination'] = city

    def return_trip(self, boolean):
        self.return_tr = boolean

    def update_request_type(self):

        self.text_request_type = TicketInfo.STATES_DB.loc[self.get_state(), 'v']

    def get_question(self):
        return TicketInfo.STATES_DB.loc[self.get_state(), 'fq']

    def get_summ(self):
        summary_list = [self.return_tr,
                        self.stations['origin'],
                        self.stations['destination'],
                        self.dates['one_way'],
                        self.search_type['one_way'],
                        self.dates['return'],
                        self.search_type['return']]
        return summary_list

    def conv_update(self, text):
        prev_state = self.get_state()
        if self.text_request_type == 'return':
            ret_f, ret_sol = scrapperReturn(text)
            if ret_f:
                self.return_trip(ret_sol)
                self.accept_status('return')
                if not ret_sol:
                    self.accept_status('re_date')
        elif self.text_request_type in ['origin', 'destination']:
            city_matching = scrapperPlace(text, self.db)
            if len(city_matching) == 1:
                if self.text_request_type == 'origin':
                    self.add_origin(city_matching[0]['code'])
                else:
                    self.add_destination(city_matching[0]['code'])
                self.accept_status(self.text_request_type)
            elif len(city_matching) == 2:
                if city_matching[0]['prev'] == 'from' or city_matching[1]['prev'] == 'to':
                    self.add_origin(city_matching[0]['code'])
                    self.add_destination(city_matching[1]['code'])
                    self.accept_status('origin')
                    self.accept_status('destination')
                elif city_matching[0]['prev'] == 'to' or city_matching[1]['prev'] == 'from':
                    self.add_origin(city_matching[1]['code'])
                    self.add_destination(city_matching[0]['code'])
                    self.accept_status('origin')
                    self.accept_status('destination')
                else:
                    if city_matching[0]['index_txt'] > city_matching[1]['index_txt']:
                        self.add_origin(city_matching[1]['code'])
                        self.add_destination(city_matching[0]['code'])
                        self.accept_status('origin')
                        self.accept_status('destination')
                    else:
                        self.add_origin(city_matching[0]['code'])
                        self.add_destination(city_matching[1]['code'])
                        self.accept_status('origin')
                        self.accept_status('destination')

        elif self.text_request_type in ['tr_date', 're_date']:
            date_matching = scrapperDates(text)
            if date_matching is not None:
                if self.text_request_type == 'tr_date':
                    self.add_trip_date(date_matching)
                else:
                    self.add_return_date(date_matching)
                self.accept_status(self.text_request_type)

        new_state = self.get_state()

        if new_state != prev_state:
            self.update_request_type()
            if self.text_request_type == 'cheapest ticket':
                return ts(self.get_summ()).get_chepeast_fare()
            return self.get_question()
        else:
            return 'Could not understand your request, could type it again'

    def first_text_(self, text):
        ret_f, ret_sol = scrapperReturn(text)
        if ret_f:
            self.return_trip(ret_sol)
            self.accept_status('return')
            if not ret_sol:
                self.accept_status('re_date')

        city_matching = scrapperPlace(text, self.db)
        if len(city_matching) == 1:
            if city_matching[0]['prev'] == 'from':
                self.add_origin(city_matching[0]['code'])
                self.accept_status('origin')
        elif len(city_matching) == 2:
            if city_matching[0]['prev'] == 'from' or city_matching[1]['prev'] == 'to':
                self.add_origin(city_matching[0]['code'])
                self.add_destination(city_matching[1]['code'])
                self.accept_status('origin')
                self.accept_status('destination')
            elif city_matching[0]['prev'] == 'to' or city_matching[1]['prev'] == 'from':
                self.add_origin(city_matching[1]['code'])
                self.add_destination(city_matching[0]['code'])
                self.accept_status('origin')
                self.accept_status('destination')
            else:
                if city_matching[0]['index_txt'] > city_matching[1]['index_txt']:
                    self.add_origin(city_matching[1]['code'])
                    self.add_destination(city_matching[0]['code'])
                    self.accept_status('origin')
                    self.accept_status('destination')
                else:
                    self.add_origin(city_matching[0]['code'])
                    self.add_destination(city_matching[1]['code'])
                    self.accept_status('origin')
                    self.accept_status('destination')

        self.update_request_type()


# text = 'I want to buy a ticket'
# a = TicketInfo(text)
# print(a.get_state())
# print(a.get_question())
# print(a.conv_update('one way ticket'))
# print(a.conv_update('bristol'))
# print(a.conv_update('plymouth'))
# print(a.conv_update('11 of january at 5pm'))
