import numpy as np
import matplotlib.pyplot as plt
import random
import time
from tensorflow import keras
from sklearn.model_selection import train_test_split

class SpinProbeResolution:  #sonde pour la simulation des mesures

    def __init__(self,g,tau,c,tlist,f1,f2):
        self.g = g #amplitude
        self.tau = tau
        self.c = c
        self.tlist = tlist
        self.OU_list_A1 = self.Ornstein_Uhlenbeck()
        self.OU_list_A2 = self.Ornstein_Uhlenbeck()
        self.OU_list_B1 = self.Ornstein_Uhlenbeck()
        self.OU_list_B2 = self.Ornstein_Uhlenbeck()
        self.f1 = f1
        self.f2 = f2


    def Ornstein_Uhlenbeck(self):
        OU_list = []
        delta_t = self.tlist[1] - self.tlist[0]
        for idx, t in enumerate(self.tlist):
            dW = np.random.normal(0,np.sqrt(delta_t))
            if idx == 0:
                OU_list.append(self.g)
            else:
                OU_list.append(OU_list[-1] - (1/self.tau)*OU_list[-1]*delta_t + np.sqrt(self.c)*dW)
        return OU_list


    def hamiltonian(self,t):
        delta_t = self.tlist[1] - self.tlist[0]
        idx = (t // delta_t) - 1
        return self.OU_list_A1[idx] * np.cos(f1*t) + self.OU_list_A2[idx] * np.cos(f2*t) - self.OU_list_B1[idx] * np.sin(f1*t) - self.OU_list_B2[idx] * np.sin(f2*t)


    def get_measures(self):
        measure_list = []
        for idx,t in enumerate(self.tlist):
            measure = self.hamiltonian(t)
            if measure > 0:
                measure_list.append(1)
            else:
                measure_list.append(0)
        return measure_list

class FullBayesianResolution:
    def __init__(self,f,hyp_delta,delta,tau,c,tlist,O_SPACE_SIZE):
        self.f = f
        self.hyp_delta = hyp_delta
        self.delta = delta
        self.f1 = f - delta/2
        self.f2 = f + delta/2
        self.g = 5/np.pi
        self.tau = tau
        self.c = c
        self.tlist = tlist
        self.Probe = SpinProbeResolution(self.g,self.tau,self.c,self.tlist,self.f1,self.f2)
        self.measure_list = self.Probe.get_measures()
        self.O_SPACE_SIZE = O_SPACE_SIZE

    def success_proba(self,t,Probe,delta):
        delta_t = self.tlist[1] - self.tlist[0]
        if delta == 0:
            f1 = f2 = self.f
        else:
            f1 = self.f - (delta / 2)
            f2 = self.f + (delta/2)
        idx = (t // delta_t) - 1
        a1 = (Probe.OU_list_A1[idx]/f1) * (np.sin(f1*t) - np.sin(f1(t-delta_t)))
        a2 = (Probe.OU_list_A2[idx]/f2) * (np.sin(f2*t) - np.sin(f2(t-delta_t)))
        b1 = (Probe.OU_list_B1[idx]/f1) * (np.cos(f1*t) - np.cos(f1(t-delta_t)))
        b2 = (Probe.OU_list_B2[idx]/f2) * (np.cos(f2*t) - np.cos(f2(t-delta_t)))
        return (np.sin(a1+a2+b1+b2+np.pi))**2

    def likelihood_ratio(self,Probe,delta):
        sum = 0
        for idx,t in enumerate(self.tlist):
            sum += self.measure_list[idx]*np.log10(self.success_proba(t,Probe,delta)) + (1-self.measure_list[idx])*np.log10(1 - self.success_proba(t,Probe,delta))
        return sum

    def bayesian_discrimination(self):
        max_likelihood_1 = -np.inf
        max_likelihood_2 = -np.inf
        for _ in range(self.O_SPACE_SIZE)
            Probe = SpinProbeResolution(self.g,self.delta_f,self.tau,self.c,self.tlist,self.f1,self.f2)
            likelihood1 = self.likelihood_ratio(Probe,0)
            if likelihood1 > max_likelihood_1:
                max_likelihood_1 = likelihood1
            likelihood2 = self.likelihood_ratio(Probe,self.hyp_delta)
            if likelihood2 > max_likelihood_2:
                max_likelihood_2 = likelihood2
        if max_likelihood_1 > max_likelihood_2:
            return self.delta == 0
        else:
            return self.delta != 0

