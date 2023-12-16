import nltk
import numpy as np

nltk.download('punkt')
from nltk.stem.lancaster import LancasterStemmer
import tflearn
import pickle
import json
from ticket_form import TicketInfo as t_f
from delay_form import DelayInfo as d_f

stemmer = LancasterStemmer()


def load_intents():
    with open('model/intents.json') as file:
        data = json.load(file)
    return data


def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]
    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(w.lower()) for w in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return np.array(bag)


class ChatBot:
    def __init__(self):
        self.data = load_intents()
        self.words, self.labels, self.training, self.output = self.load_trained_model()
        self.model = self.get_model()
        self.conv_type = ''
        self.conv_classes = {
            'shop': '',
            'delay': '',
            'cont': '',
        }

    def load_trained_model(self):
        try:
            with open('model/data.pickle', 'rb') as f:
                words, labels, training, output = pickle.load(f)
        except:
            words = []
            labels = []
            docs_x = []
            docs_y = []

            for intent in self.data['intents']:
                for pattern in intent['patterns']:
                    wrds = nltk.word_tokenize(pattern)
                    words.extend(wrds)
                    docs_x.append(wrds)
                    docs_y.append(intent['tag'])

                if intent['tag'] not in labels:
                    labels.append(intent['tag'])

            words = [stemmer.stem(w.lower()) for w in words if w not in '?']
            words = sorted(list(set(words)))

            labels = sorted(labels)

            training = []
            output = []

            out_empty = [0 for _ in range(len(labels))]

            for x, doc in enumerate(docs_x):
                bag = []
                wrds = [stemmer.stem(w.lower()) for w in doc]

                for w in words:
                    if w in wrds:
                        bag.append(1)
                    else:
                        bag.append(0)

                output_row = out_empty[:]
                output_row[labels.index(docs_y[x])] = 1

                training.append(bag)
                output.append(output_row)

            training = np.array(training)
            output = np.array(output)

            with open('model/data.pickle', 'wb') as f:
                pickle.dump((words, labels, training, output), f)

        return words, labels, training, output

    def get_model(self):
        net = tflearn.input_data(shape=[None, len(self.training[0])])
        net = tflearn.fully_connected(net, 8)
        net = tflearn.fully_connected(net, 8)
        net = tflearn.fully_connected(net, len(self.output[0]), activation='softmax')
        net = tflearn.regression(net)

        model = tflearn.DNN(net)

        try:
            model.load('model/model.tflearn')
        except:
            model = tflearn.DNN(net)
            model.fit(self.training, self.output, n_epoch=1000, batch_size=8, show_metric=True)
            model.save('model/model.tflearn')

        return model

    def get_label(self, inp):

        results = self.model.predict([bag_of_words(inp, self.words)])
        print(results)
        if max(results[0]) > 0.68:
            results_index = np.argmax(results)
            tag = self.labels[results_index]
            print(tag)
            self.conv_type = tag
            if tag == 'shop':
                self.conv_classes[tag] = t_f(inp)
                return self.conv_classes[tag].get_question()
            elif tag == 'delay':
                self.conv_classes[tag] = d_f(inp)
                return self.conv_classes[tag].get_question()
            elif tag == 'cont':
                return 'This fixture will be available soon'

        else:
            return 'Can you tell me more'
