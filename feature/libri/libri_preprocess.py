#-*- coding:utf-8 -*-
#!/usr/bin/python
''' Automatic Speech Recognition

author:
zzw922cn
hiteshpaul
date:2017-5-09
'''

from __future__ import print_function
from __future__ import unicode_literals

import sys
sys.path.append('../')

from core.sigprocess import *
from core.calcmfcc import calcMFCC_delta_delta
import scipy.io.wavfile as wav
import numpy as np
import os
import cPickle
import glob
import sklearn
import argparse
from sklearn import preprocessing
from subprocess import check_call, CalledProcessError

def preprocess(root_directory):
    """
    Function to walk through the directory and convert flac to wav files
    """
    try:
        check_call(['flac'])
    except OSError:
        raise OSError("""Flac not installed. Install using apt-get install flac""")
    for subdir, dirs, files in os.walk(root_directory):
        for f in files:
            filename = os.path.join(subdir, f)
            if f.endswith('.flac'):
                try:
                    check_call(['flac', '-d', filename])
                    os.remove(filename)
                except CalledProcessError as e:
                    print("Failed to convert file {}".format(filename))
            elif f.endswith('.TXT'):
                os.remove(filename)
            elif f.endswith('.txt'):
                with open(filename, 'r') as fp:
                    lines = fp.readlines()
                    for line in lines:
                        sub_n = line.split(' ')[0] + '.label'
                        subfile = os.path.join(subdir, sub_n)
                        sub_c = ' '.join(line.split(' ')[1:])
                        sub_c = sub_c.lower()
                        with open(subfile, 'w') as sp:
                            sp.write(sub_c)
            elif f.endswith('.wav'):
                if not os.path.isfile(os.path.splitext(filename)[0] +
                                      '.label'):
                    raise ValueError(".label file not found for {}".format(filename))
            else:
                pass


def wav2feature(root_directory, save_directory,  name, win_len=0.02, win_step=0.01, mode='mfcc', seq2seq=False, save=False):
    count = 0
    label_dir = save_directory + '/{}/label/'.format(name)
    mfcc_dir = save_directory + '/{}/mfcc/'.format(name)
    if not os.path.isdir(label_dir):
        os.makedirs(label_dir)
    if not os.path.isdir(mfcc_dir):
        os.makedirs(mfcc_dir)
    preprocess(root_directory+name)
    for subdir, dirs, files in os.walk(root_directory+name):
        for f in files:
            fullFilename = os.path.join(subdir, f)
            filenameNoSuffix =  os.path.splitext(fullFilename)[0]
            if f.endswith('.wav'):
                rate = None
                sig = None
                try:
                    (rate,sig)= wav.read(fullFilename)
                except ValueError as e:
                    if e.message == "File format 'NIST'... not understood.":
                        sf = Sndfile(fullFilename, 'r')
                    nframes = sf.nframes
                    sig = sf.read_frames(nframes)
                    rate = sf.samplerate
                mfcc = calcMFCC_delta_delta(sig,rate,win_length=win_len,win_step=win_step)
                mfcc = preprocessing.scale(mfcc)
                mfcc = np.transpose(mfcc)
                print(mfcc.shape)
                labelFilename = filenameNoSuffix + '.label'
                with open(labelFilename,'r') as f:
                    characters = f.readline().strip().lower()
                targets = []
                if seq2seq is True:
                    targets.append(28)
                for c in characters:
                    if c == ' ':
                        targets.append(0)
                    elif c == "'":
                        targets.append(27)
                    else:
                        targets.append(ord(c)-96)
                if seq2seq is True:
                    targets.append(29)
                print(targets)
                count+=1
                print('file index:',count)
                if save:
                    featureFilename = mfcc_dir + filenameNoSuffix.split('/')[-1] +'.npy'
                    np.save(featureFilename,mfcc)
                    t_f = label_dir + filenameNoSuffix.split('/')[-1] +'.npy'
                    print(t_f)
                    np.save(t_f,targets)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='libri_preprocess',
                                     description='Script to preprocess libri data')
    parser.add_argument("path", help="Directory where extracted LibriSpeech dataset is contained", type=str)
    parser.add_argument("save", help="Directory where preprocessed arrays are to be saved",
                        type=str)
    parser.add_argument("-n", "--name", help="Name of the dataset",
                        choices=['dev-clean', 'dev-other', 'test-clean',
                                 'test-other'], type=str, default='dev-clean')
    parser.add_argument("--seq2seq", help="set this flag to use seq2seq", action="store_true")
    args = parser.parse_args()
    root_directory = args.path
    save_directory = args.save
    seq2seq = args.seq2seq
    name = args.name
    if root_directory == '.':
        root_directory = os.getcwd()
    root_directory += "/LibriSpeech/"
    if save_directory == '.':
        save_directory = os.getcwd()
    if not os.path.isdir(root_directory) or not os.path.isdir(save_directory):
        raise ValueError("LibriSpeech Directory does not exist!")
    wav2feature(root_directory, save_directory, name=name, win_len=0.02, win_step=0.01,
                seq2seq=seq2seq, save=True)
