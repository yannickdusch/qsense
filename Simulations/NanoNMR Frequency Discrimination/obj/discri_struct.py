import numpy as np
import matplotlib.pyplot as plt
import random
import time
from tensorflow import keras
from sklearn.model_selection import train_test_split


class SpinProbe:  #sonde pour la simulation des mesures

    def __init__(self,g,w,phi):
        self.g = g #amplitude
        self.w = w #fréquence
        self.phi = phi #phase
        self.mnoise = 0 #bruit magnétique

    def hamiltonian(self,t):
        return self.g*np.cos(self.w*t + self.phi) + self.mnoise

    def get_measures_no_noise(self,tlist): #cas idéal
        measure_list = []
        for idx,t in enumerate(tlist):
            measure = self.hamiltonian(t)
            if measure > 0:
                measure_list.append(1)
            else:
                measure_list.append(0)
        return measure_list

    def get_measures_phase_noise(self,tlist): #bruit de phase: la phase change une fois pour une valeur aléatoire, à un intervalle de temps aléatoire
        measure_list = []
        random_idx = random.randint(0,len(tlist) - 1) #intervalle de temps au hasard
        random_new_phase = random.uniform(0,2*np.pi) #nouvelle phase aléatoire
        for idx,t in enumerate(tlist):
            if idx == random_idx:
                self.phi = random_new_phase  #on modifie la phase
            measure = self.hamiltonian(t)
            if measure > 0:
                measure_list.append(1)
            else:
                measure_list.append(0)
        return measure_list

    def get_measures_magnetic_noise(self,tlist): #bruit magnétique: une constante aléatoire est ajoutée à l'hamiltonien. Elle change une fois à un intervalle de temps aléatoire
        measure_list = []
        random_idx = random.randint(0,len(tlist) - 1) #intervalle de temps au hasard
        self.mnoise = np.random.normal(loc=0,scale=2/(2*np.pi)) #bruit magnétique, choisi sur une distribution normale
        for idx,t in enumerate(tlist):
            if idx == random_idx:
                self.mnoise = np.random.normal(loc=0,scale=2/(2*np.pi)) #nouveau bruit magnétique
            measure = self.hamiltonian(t)
            if measure > 0:
                measure_list.append(1)
            else:
                measure_list.append(0)
        return measure_list

    def get_measures_amplitude_noise(self,tlist): #bruit d'amplitude: l'amplitude change aléatoirement ) chaque intervalle de temps
        measure_list = []
        for idx,t in enumerate(tlist):
            self.g = np.random.normal(loc=10/(2*np.pi),scale=10/(2*np.pi)) #nouvelle amplitude, choisie sur une distribution normale
            measure = self.hamiltonian(t)
            if measure > 0:
                measure_list.append(1)
            else:
                measure_list.append(0)
        return measure_list

    def get_measures_all_noise(self,tlist):
        measure_list = []
        random_idx_mnoise = random.randint(0,len(tlist) - 1) #intervalle de temps au hasard, pour le bruit magnétique
        random_idx_phase = random.randint(0,len(tlist) - 1) #intervalle de temps au hasard, pour le bruit de phase
        self.mnoise = np.random.normal(loc=0,scale=2/(2*np.pi)) #bruit magnétique
        random_new_phase = random.uniform(0,2*np.pi) #nouvelle phase
        for idx,t in enumerate(tlist):
            self.g = np.random.normal(loc=10/(2*np.pi),scale=10/(2*np.pi)) #nouvelle amplitude
            if idx == random_idx_mnoise:
                self.mnoise = np.random.normal(loc=0,scale=2/(2*np.pi)) #changement de bruit magnétique
            if idx == random_idx_phase:
                self.phi = random_new_phase #changement de phase
            measure = self.hamiltonian(t)
            if measure > 0:
                measure_list.append(1)
            else:
                measure_list.append(0)
        return measure_list

    def get_measures(self,tlist,MODE): #return a different measure depending on
        if MODE == "none":
            return self.get_measures_no_noise(tlist)
        if MODE == "phase":
            return self.get_measures_phase_noise(tlist)
        if MODE == "magnetic":
            return self.get_measures_magnetic_noise(tlist)
        if MODE == "amplitude":
            return self.get_measures_amplitude_noise(tlist)
        if MODE == "all":
            return self.get_measures_all_noise(tlist)
        else:
            raise Exception("Mode non supporté, veillez choisir parmis 'none','phase','magnetic','amplitude', et 'all'.")

class FullBayesianMethod:
    def __init__(self,w1,delta_w,w,measure_list,tlist,PHI_SPACE_SIZE):
        self.w1 = w1
        self.w2 = w1 + delta_w
        self.w = w
        self.g1 = self.g2 = 5/np.pi
        #self.phi = random.uniform(0,2*np.pi)
        self.measure_list = measure_list
        self.tlist = tlist
        self.phi_space = np.linspace(0,2*np.pi,num = PHI_SPACE_SIZE,endpoint=False)

    def success_proba(self,g,w,phi,t):
        delta_t = self.tlist[1] - self.tlist[0]
        return np.sin((g/(2*w))*(np.sin(w*t + phi) - np.sin(w*(t-delta_t)+phi))+np.pi/4)**2

    def likelihood_ratio(self,g,w,phi):
        sum = 0
        for idx,t in enumerate(self.tlist):
            sum += self.measure_list[idx]*np.log10(self.success_proba(g,w,phi,t)) + (1-self.measure_list[idx])*np.log10(1 - self.success_proba(g,w,phi,t))
        return sum

    def bayesian_discrimination(self):
        max_likelihood_1 = -np.inf
        max_likelihood_2 = -np.inf
        for phi_k in self.phi_space:
            likelihood1 = self.likelihood_ratio(self.g1,self.w1,phi_k)
            if likelihood1 > max_likelihood_1:
                max_likelihood_1 = likelihood1
                max_phi_1 = phi_k
            likelihood2 = self.likelihood_ratio(self.g2,self.w2,phi_k)
            if likelihood2 > max_likelihood_2:
                max_likelihood_2 = likelihood2
                max_phi_2 = phi_k
        if max_likelihood_1 > max_likelihood_2:
            return self.w1 == self.w
        else:
            return self.w2 == self.w


class CorrelationMethod:
    def __init__(self,w1,delta_w,w,measure_list_w,tlist,PHI_SPACE_SIZE,noise):
        self.w1 = w1
        self.w2 = w1 + delta_w
        self.w = random.choice([self.w1,self.w2])
        self.g1 = self.g2 = 5/np.pi
        self.phi = random.uniform(0,2*np.pi)
        self.measure_list_w = measure_list_w
        self.tlist = tlist
        self.phi_space = np.linspace(0,2*np.pi,num = PHI_SPACE_SIZE,endpoint=False)
        self.noise = noise
        self.k = 1

    def correlation_vectors(self,measure_list):
        for idx,element in enumerate(measure_list):
            if element == 0:
                measure_list[idx] = -1
        Ck = []
        size = len(measure_list)
        for idx, _ in enumerate(measure_list):
            Ck.append(measure_list[idx]*measure_list[(idx+self.k)%size])
        return Ck

    def correlation_discrimination(self):
        D1_min = np.inf
        D2_min = np.inf
        for phi_k in self.phi_space:
            measure_list_w1 = SpinProbe(self.g1,self.w1,phi_k).get_measures(self.tlist,self.noise)
            measure_list_w2 = SpinProbe(self.g2,self.w2,phi_k).get_measures(self.tlist,self.noise)
            correlation_vector_unk = self.correlation_vectors(self.measure_list_w)
            correlation_vector_1 = self.correlation_vectors(measure_list_w1)
            correlation_vector_2 = self.correlation_vectors(measure_list_w2)
            D1 = np.linalg.norm(np.subtract(correlation_vector_unk,correlation_vector_1))
            D2 = np.linalg.norm(np.subtract(correlation_vector_unk,correlation_vector_2))
            if D1 < D1_min:
                D1_min = D1
            if D2 < D2_min:
                D2_min = D2
        if D1_min < D2_min:
            return self.w == self.w1
        else:
            return self.w == self.w2


class DeepLearningMethod:
    def __init__(self,w1,delta_w,dataset_size,tlist):
        self.w1 = w1
        self.w2 = w1 + delta_w
        self.g1 = self.g2 = 5/np.pi
        model = keras.Sequential()
        model.add(keras.Input(shape=(len(tlist),)))
        model.add(keras.layers.Dense(20, activation='relu'))
        model.add(keras.layers.Dense(35, activation='relu'))
        model.add(keras.layers.Dense(1, activation='sigmoid'))
        model.compile(loss='mse')
        self.model = model
        self.dataset_size = dataset_size

    def train_and_get_results(self,X,y):
        X_train, X_test, y_train, y_test = train_test_split(X,y,test_size = 0.2)
        self.model.fit(X_train,y_train)
        y_results = self.model.predict(X_test)
        correct = 0
        for idx,result in enumerate(y_results):
            if result < 0.5:
                value = 0
            else:
                value = 1
            if value == y_test[idx]:
                correct += 1
        error = round(1 - (correct/len(y_results)),2)
        return error

    def create_data_set(self,MODE,tlist):
        X = []
        for _ in range(self.dataset_size):
            phi = random.uniform(0,2*np.pi)
            NewProbe = SpinProbe(self.g1,self.w1,phi)
            X.append(NewProbe.get_measures(tlist,MODE))
        for _ in range(self.dataset_size):
            phi = random.uniform(0,2*np.pi)
            NewProbe = SpinProbe(self.g2,self.w2,phi)
            X.append(NewProbe.get_measures(tlist,MODE))
        y = [0 for _ in range(self.dataset_size)] + [1 for _ in range(self.dataset_size)]
        return X , y
