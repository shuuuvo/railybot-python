from stations_db import get_delay_db
import spacy
import pandas as pd
import os
import datetime
import numpy as np
import sklearn
from sklearn import linear_model
import pickle
from ticket_form import scrapperPlace
from IDDFS import get_time

nlp = spacy.load('en_core_web_sm')


def scrapperDelay(text):
    minutes = {
        'hour': 60,
        'minute': 1,
    }
    scrapper = {
        'NOUN': 0,
        'NUM': 0
    }
    doc = nlp(text)
    total_time = 1
    for ent in doc.ents:
        if ent.label_ == 'TIME':
            for token in nlp(ent.text):
                if token.pos_ in ['NOUN']:
                    try:
                        total_time *= minutes[token.lemma_]
                    except:
                        raise Exception('No compatible')
                elif token.pos_ in ['NUM']:
                    total_time *= float(token.text)
        break

    return total_time


def load_model():
    try:
        pickle_in = open('model/_delay/finalized_model.sav', 'rb')
        prediction_model = pickle.load(pickle_in)

    except:
        os.system('python delaymodel.py')
        pickle_in = open('model/_delay/finalized_model.sav', 'rb')
        prediction_model = pickle.load(pickle_in)

    return prediction_model


class DelayInfo:
    STATES_DB = pd.read_csv('_states/_delay_states.csv', index_col='s')

    def __init__(self, *kwargs):
        self.models = load_model()
        self.db = get_delay_db().dropna()
        self.stations = {
            'origin': '',
            'destination': '',
        }
        self.delay = {
            'time': '',
        }
        self.checklist = {'origin': False,
                          'destination': False,
                          'delay_time': False,
                          }
        self.text_request_type = ''

        if len(kwargs) > 0:
            self.first_text_(kwargs[0])
        else:
            self.update_request_type()

    def get_state(self):
        return int(''.join([str(int(x)) for x in self.checklist.values()]))

    def add_origin(self, city):
        self.stations['origin'] = city

    def add_destination(self, city):
        self.stations['destination'] = city

    def add_time_delay(self, city):
        self.delay['time'] = city

    def accept_status(self, argument):
        self.checklist[argument] = True

    def update_request_type(self):
        self.text_request_type = DelayInfo.STATES_DB.loc[self.get_state(), 'v']

    def get_question(self):
        return DelayInfo.STATES_DB.loc[self.get_state(), 'fq']

    def get_summ(self):
        summary_list = [self.stations['origin'],
                        self.stations['destination'],
                        self.delay['time']
                        ]
        return summary_list

    def conv_update(self, text):
        prev_state = self.get_state()
        if self.text_request_type in ['origin', 'destination']:
            city_matching = scrapperPlace(text, self.db)
            if len(city_matching) == 1:
                if self.text_request_type == 'origin':
                    self.add_origin(city_matching[0]['code'])
                elif self.text_request_type == 'destination':
                    self.add_destination(city_matching[0]['code'])
                else:
                    self.add_station_delay(city_matching[0]['code'])
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

        elif self.text_request_type in ['delay_time']:
            delay_matching = scrapperDelay(text)
            if isinstance(delay_matching,float):
                self.add_time_delay(delay_matching)
                self.accept_status(self.text_request_type)

        new_state = self.get_state()

        if new_state != prev_state:
            self.update_request_type()
            if self.text_request_type == 'estimated':
                return True, get_time(self.stations['origin'], self.stations['destination'], self.models,self.delay['time'])
            return False, self.get_question()
        else:
            return False, 'Could not understand your request! Could you please type it again?'

    def first_text_(self, text):
        city_matching = scrapperPlace(text, self.db)
        if len(city_matching) == 1:
            if city_matching[0]['prev'] == 'from':
                self.add_origin(city_matching[0]['code'])
                self.accept_status('origin')
            elif city_matching[0]['prev'] == 'in':
                self.add_station_delay(city_matching[0]['code'])
                self.accept_status('delay_st')
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

# text = 'Hi theres a delay in my train journey in staines'
# a = DelayInfo(text)
# print(a.get_question())
# print(a.conv_update('30 minutes'))
# print(a.conv_update('moreton'))
# print(a.conv_update('Weymath'))