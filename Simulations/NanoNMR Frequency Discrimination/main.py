import os
import numpy as np
import matplotlib.pyplot as plt
import random
import time
import seaborn as sbn
import pandas as pd
from tensorflow import keras
from sklearn.model_selection import train_test_split
from obj.discri_struct import *
from obj.resolution_struct import *

NOISE = "amplitude"
delta_w_list = np.linspace(0.8e-3,2.5e-3,10)
tlist = np.linspace(0.5,500,1000)
delta_w_no_noise = [0.2e-3,0.3e-3,0.4e-3,0.5e-3,0.75e-3,1e-3,1.25e-3,1.75e-3,2.25e-3]
delta_w_noise = [0.2e-3,0.4e-3,0.6e-3,0.8e-3,1e-3,1.2e-3,1.4e-3,1.6e-3]
delta_w_all_noise = np.linspace(0.3e-3,3e-3,10)
NB_ITER = 500
g = 10/(2*np.pi)
w1 = 10/(2*np.pi)
PHI_SPACE_SIZE = 15
DATASET_SIZE = 5000

delta_w_dict = {
'none':delta_w_no_noise,
'phase':delta_w_noise,
'magnetic':delta_w_noise,
'amplitude':delta_w_noise,
'all':delta_w_all_noise
}

title_dict = {
'none':'Discrimination Error Probability - No Noise',
'phase':'Discrimination Error Probability - Phase Noise',
'magnetic':'Discrimination Error Probability - Magnetic Noise',
'amplitude':'Discrimination Error Probability - Amplitude Noise',
'all':'Discrimination Error Probability - All Noises'
}

def bayesian_error_rate(delta_w):
    global NOISE
    success = 0
    w2 = w1 + delta_w
    for i in range(NB_ITER):
        w = random.choice([w1,w2])
        phi = random.uniform(0,2*np.pi)
        NewProbe = SpinProbe(g,w,phi)
        measure_list = NewProbe.get_measures(tlist,NOISE)
        Experiment = FullBayesianMethod(w1,delta_w,w,measure_list,tlist,PHI_SPACE_SIZE)
        if Experiment.bayesian_discrimination():
            success += 1
    return (1 - (success/NB_ITER))



def BayesianGraph():
    error_proba = []
    for delta_w in delta_w_list:
        a = bayesian_error_rate(delta_w)
        print(a)
        error_proba.append(a)
    print(error_proba)
    new_delta_w_list = [delta_w*1000 for delta_w in delta_w_list]
    plt.plot(new_delta_w_list,error_proba)
    plt.ylim(ymin=0)
    plt.show()


def correlation_error_rate(delta_w):
    global NOISE
    success = 0
    w2 = w1 + delta_w
    for i in range(NB_ITER):
        w = random.choice([w1,w2])
        phi = random.uniform(0,2*np.pi)
        NewProbe_w = SpinProbe(g,w,phi)
        measure_list_w = NewProbe_w.get_measures(tlist,NOISE)
        Experiment = CorrelationMethod(w1,delta_w,w,measure_list_w,tlist,PHI_SPACE_SIZE,NOISE)
        if Experiment.correlation_discrimination():
            success += 1
    return (1 - (success/NB_ITER))

def CorrelationGraph():
    error_proba = []
    for delta_w in delta_w_list:
        error_proba.append(correlation_error_rate(delta_w))
    print(error_proba)
    new_delta_w_list = [delta_w*1000 for delta_w in delta_w_list]
    plt.plot(new_delta_w_list,error_proba)
    plt.ylim(ymin=0)
    plt.show()

def DL_error_rate(delta_w):
    global NOISE
    Experiment = DeepLearningMethod(w1,delta_w,DATASET_SIZE,tlist)
    X,y = Experiment.create_data_set(NOISE,tlist)
    return Experiment.train_and_get_results(X,y)

def DLGraph():
    error_proba = []
    for delta_w in delta_w_list:
        error_proba.append(DL_error_rate(delta_w))
    print(error_proba)
    new_delta_w_list = [delta_w*1000 for delta_w in delta_w_list]
    plt.plot(new_delta_w_list,error_proba)
    plt.ylim(ymin=0)
    plt.show()

def graph(noise):
    global NOISE
    NOISE = noise
    delta_w_list = delta_w_dict[noise]
    title = title_dict[noise]
    error_proba_bayes = []
    error_proba_corr = []
    error_proba_dl = []
    for delta_w in delta_w_list:
        error_proba_bayes.append(bayesian_error_rate(delta_w))
        error_proba_corr.append(correlation_error_rate(delta_w))
        error_proba_dl.append(DL_error_rate(delta_w))
    new_delta_w_list = [delta_w * 1000 for delta_w in delta_w_list]
    df = pd.DataFrame({'Δω (mrad/s)' : new_delta_w_list,
    'Full Bayesian':error_proba_bayes,
    'Correlation':error_proba_corr,
    'Deep Learning':error_proba_dl})
    sbn.lineplot(x='Δω (mrad/s)', y='Full Bayesian', label = 'Full Bayesian', data=df,marker = 'o',color='g')
    sbn.lineplot(x='Δω (mrad/s)', y='Correlation', label = 'Correlation', data=df,marker = 's',color='b')
    sbn.lineplot(x='Δω (mrad/s)', y='Deep Learning', label = 'Deep Learning', data=df,marker = 'h',color='r')
    plt.title(title)
    plt.ylabel('Error Rate')
    plt.xlabel('Δω (mrad/s)')
    plt.legend()
    plt.show()


def bayesian_reso_error_rate(delta):
    success = 0
    for i in range(NB_ITER):
        real_delta = random.choice([0,delta])
        Experiment = FullBayesianResolution(w1,delta,real_delta,measure_list,tlist,PHI_SPACE_SIZE)
        if Experiment.bayesian_discrimination():
            success += 1
    return (1 - (success/NB_ITER))

#graph('phase')
