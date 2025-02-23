from typing import Optional, Iterable
import torch
import numpy as np
import pandas as pd
from torch.utils.data import Dataset,dataloader
from scipy.signal import filtfilt, iirnotch, butter
from einops import rearrange
import os
import scipy
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from mne.decoding import CSP
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.metrics import accuracy_score, confusion_matrix, cohen_kappa_score
import matplotlib.pyplot as plt

def load_files(folder):
	d = {}
	subjects = []
	files = os.listdir(folder)
	for f in files:
		df = pd.read_csv(os.path.join(folder,f))
		subject = str.split(f,"_")[-1]
		if subject not in d.keys():
			d[subject] = [df]
			subjects.append(subject)
		else:
			d[subject].append(df)
	for s in subjects:
		d[s] = {"train":d[s][:-1],"test":[d[s][-1]]}
	return d

def _get_epochs(df,
				indices,
				n_samples_baseline,
				n_samples,
				epochs = [],
				subject_channels=["ch1","ch2","ch3","ch4"]):
		for i in indices:
			# length x n_channels
			epoch = df.loc[i-n_samples_baseline:i+n_samples][subject_channels]
			epochs.append(epoch)
		return epochs

def get_epochs(dfs,
			   fs,
			   t_epoch,
			   t_baseline=0,
			   subject_channels=["ch1","ch2","ch3","ch4"]):

	left_epochs = []
	right_epochs = []

	n_samples = int(fs*t_epoch)
	n_samples_baseline = int(fs*t_baseline)
	
	for df in dfs:
		t = df["timestamp"]
		# print((max(t) - min(t))/60)
		indices = np.arange(len(df))

		left_indices = indices[df["left"] == 1]
		right_indices = indices[df["right"] == 1]

		left_epochs = _get_epochs(df,left_indices,n_samples_baseline,
							n_samples,left_epochs,subject_channels)
		
		right_epochs = _get_epochs(df,right_indices,n_samples_baseline,
							n_samples,right_epochs,subject_channels)
		
	left_epochs = np.stack(left_epochs,0)
	right_epochs = np.stack(right_epochs,0)
	return left_epochs,right_epochs

def sliding_window_view(arr, window_size, step, axis):
	shape = arr.shape[:axis] + ((arr.shape[axis] - window_size) // step + 1, window_size) + arr.shape[axis+1:]
	strides = arr.strides[:axis] + (arr.strides[axis] * step, arr.strides[axis]) + arr.strides[axis+1:]
	strided = np.lib.stride_tricks.as_strided(arr, shape=shape, strides=strides)
	return rearrange(strided,"n e ... -> (n e) ...")

def subject_epochs(dfs,
				   subject_channels=["ch2","ch3","ch4","ch5"],
				   stride=25,
				   epoch_length=512):
	left,right = get_epochs(dfs,256,8,0,subject_channels=subject_channels)
	n,l,d = left.shape
	left_epochs = sliding_window_view(left,epoch_length,stride,1)
	right_epochs = sliding_window_view(right,epoch_length,stride,1)
	left_y = np.zeros(len(left_epochs))
	right_y = np.ones(len(right_epochs))
	xs = np.concatenate((left_epochs,right_epochs))
	ys = np.concatenate((left_y,right_y))
	return xs,ys

class subject_dataset:

	def __init__(self,
			  mat,
			  fs = 250,
			  t_baseline = 0.3,
			  t_epoch = 4):

		self.fs = fs
		self.t_baseline = t_baseline
		self.t_epoch = t_epoch

		self.epochs = []
		self.cues = []
		self.dfs = []
		self.timestamps = []

		for i in range(mat.shape[-1]):
			epochs,cues,df = self.load_data(mat,i)
			self.epochs.append(epochs)
			self.cues.append(cues)
			self.dfs.append(df)

		self.epochs = np.concatenate(self.epochs,axis=0)
		# removing 1 to get 0,1 instead of 1,2
		self.cues = np.concatenate(self.cues,0)	- 1	

	def  load_data(self,
				   mat,
				   index=0):

		"""
		Loading the epochs,cues, and dataframe for one trial
		For now, we are not removing samples with artifacts
		since it can't be done on the fly.

		Args:
			mat: array
			index: trial index

		Returns:
			epochs: array of epoch electrode data
			cues: array of cues (labels) for each epoch
			df: dataframe of trial data
		"""
		
		electrodes = mat[0][index][0][0][0].squeeze()
		timestamps = mat[0][index][0][0][1].squeeze()
		cues = mat[0][index][0][0][2].squeeze()
		artifacts = mat[0][index][0][0][5]

		epochs,cues = self.create_epochs(electrodes,timestamps,artifacts,cues,
							  self.t_baseline,self.t_epoch,self.fs)
		
		epochs,cues = self.epoch_preprocess(epochs,cues)
		
		df = self.load_df(timestamps,electrodes,cues)
		return epochs,cues,df

	def create_epochs(self,
				   electrodes,
				   timestamps,
				   artifacts,
				   cues,
				   t_baseline,
				   t_epoch,
				   fs):
		
		"""
		creating an array with all epochs from a trial

		Args:
			electrode: electrode data
			timestamps: cue indices
			artifacts: artifact presence array
			cues: labels for cues
			t_baseline: additional time for baseline
			t_epoch: time of epoch
		"""
		
		n_samples = int(fs*t_epoch)
		n_samples_baseline = int(fs*t_baseline)
		epochs = []
		cues_left = []
		for i,j,c in zip(timestamps,artifacts,cues):
			if j==0:
				epochs.append(electrodes[i-n_samples_baseline:i+n_samples,:])
				cues_left.append(c)
		epochs = np.stack(epochs)
		cues_left = np.asarray(cues_left)
		return epochs,cues_left

	def load_df(self,
			 timestamps,
			 electrodes,
			 cues):

		"""
		Loading the channel values and adding a timestamp column.
		Useful for visualizing an entire trial

		Args:
			None
		Returns:
			None
		"""

		timeline = np.zeros_like(electrodes[:,0])

		for t,c in zip(timestamps,cues):
			timeline[t] = c

		df = pd.DataFrame(electrodes)

		df["timestamps"] = timeline

		return df
	
	def trial_preprocess(x,*args,**kwargs):
		"""
		Pre-processing step to be applied to entire trial.
		"""
		return x
	
	def epoch_preprocess(self,x,y,notch_freq=50):
		"""
		Apply pre-processing before concatenating everything in a single array.
		Easier to manage multiple splits
		By default, it only applies a notch filter at 50 Hz
		"""

		n,d,t = x.shape
		x = rearrange(x,"n t d -> (n d) t")
		b,a = iirnotch(notch_freq,30,self.fs)
		x = filtfilt(b,a,x)
		x = rearrange(x,"(n d) t -> n t d",n=n)
		return x,y
	
class CSP_subject_dataset(subject_dataset):

	def __init__(self, mat, fs=250, t_baseline=0.3, t_epoch=4):
		super().__init__(mat, fs, t_baseline, t_epoch)

	def epoch_preprocess(self, x, y):

		print("preprocessing")

		x,y = super().epoch_preprocess(x, y)
	
		ax = []

		for i in range(1,10):
			ax.append(self.bandpass(x,self.fs,4*i,4*i+4))
		x = np.concatenate(ax,-1)
		print(x.shape)
		mu = np.mean(x,axis=-1)
		sigma = np.std(x,axis=-1)
		x = (x-rearrange(mu,"n d -> n d 1"))/rearrange(sigma,"n d -> n d 1")
		print(x.shape)
		return x,y
	
	def bandpass(self,
			  x,
			  fs,
			  low,
			  high,):
		
		nyquist = fs/2
		b,a = butter(4,[low/nyquist,high/nyquist],"bandpass",analog=False)
		n,d,t = x.shape
		x = rearrange(x,"n t d -> (n d) t")
		x = filtfilt(b,a,x)
		x = rearrange(x,"(n d) t -> n t d",n=n)
		return x


class EEGDataset(Dataset):
	def __init__(self,
			     subject_splits:list[list[str]],
				 dataset:Optional[dict] = None,
				 save_paths:Optional[list[str]] = None,
				 fake_data=None,
				 subject_dataset_type: Optional[subject_dataset] = None,
				 fake_percentage:float = 0.5,
				 fs:float = 250, 
				 t_baseline:float = 0, 
				 t_epoch:float = 9,
				 start:float = 3.5,
				 length:float = 2,
				 channels:Iterable = np.array([0,1,2]),
				 sanity_check:bool=False,
				 **kwargs):
		
		"""
		Args:
			subject_splits: splits to use for train and test
			save_path: path(s) to save/load pre-processed data
			dataset: dictionnary of train and test splits for all subjects
			subject_dataset_type: type of subject dataset for pre-processing
			pickled: load pickled dataset instead of saving
			fs: sampling frequency
			t_baseline: start of motor imagery trial
			t_epoch: length of motor imagery trial
			start: start of data
			length: duration of data
			channels: chanel indices to include
			sanity_check: test classification score with CSP
		"""
		
		self.fs = fs
		self.t_baseline = t_baseline
		self.t_epoch = t_epoch
		self.fake_percentage = fake_percentage

		self.set_epoch(start,length)

		if dataset is None:
			self.data = self.load_data(save_paths,subject_splits,channels)
		else:
			self.save_dataset(dataset,save_paths[0],subject_dataset_type)
			self.data = self.load_data(save_paths,subject_splits,channels)

		if fake_data is not None:
			print("we have fake data")
			self.data = self.load_fake(*fake_data)

		if sanity_check:
			self.sanity_check()

		print(f"final data shape: {self.data[0].shape}")

	def __len__(self):
		return self.data[0].shape[0]

	def __getitem__(self, idx):
		try:
			return self.data[0][idx], self.data[1][idx]
		except:
			print(idx)
			print(len(idx))
			print(idx[0].shape)
			raise ValueError("Invalid type")

	def sanity_check(self):

		x,y = self.data[0], self.data[1]
		x = np.float64(x)
		print(x.shape)
		csp = CSP(n_components=x.shape[1],reg=None,log=True,norm_trace=False)
		svm = SVC(C=1)

		clf = Pipeline(steps=[("csp",csp),
							("classification",svm)])
		
		clf.fit(x,y)

		y_pred = clf.predict(x)
		acc = accuracy_score(y,y_pred)
		confusion = confusion_matrix(y,y_pred,normalize="true")
		print(acc)
		print(confusion)

	def save_dataset(self,
				  dataset:dict,
				  path:str,
				  subject_dataset_type:subject_dataset):
		
		"""
		Function for pre-processing a dataset and saving it
		It will save all trial, not just the ones used in this dataset

		Args:
			dataset: dictionnary of train and test splits for all subjects
			path: path to save the pre-processed data
			subject_dataset_type: type of subject dataset for pre-processing

		Return:
			None
		"""
		
		if not os.path.isdir(path):
			os.makedirs(path)
		
		for idx,(k,subject) in enumerate(dataset.items()):
			for split in ["train","test"]:
				set = subject_dataset_type(subject[split],self.fs,self.t_baseline,self.t_epoch)
				epochs = np.float32(set.epochs)
				cues = set.cues
				np.save(os.path.join(path,f"subject_{idx}_{split}_epochs.npy"),epochs)
				np.save(os.path.join(path,f"subject_{idx}_{split}_cues.npy"),cues)

	def load_data(self,
			   paths,
			   subject_splits,
			   channels):
		
		epochs = []
		cues = []

		for path in paths:

			for idx,splits in enumerate(subject_splits):
				for split in splits:
					epochs.append(np.load(os.path.join(path,f"subject_{idx}_{split}_epochs.npy")))
					cues.append(np.load(os.path.join(path,f"subject_{idx}_{split}_cues.npy")))

		epochs = rearrange(np.concatenate(epochs,0),"n t d -> n d t")[:,channels,:]
		epochs = epochs[:,:,int(self.input_start*250):int(self.input_end*250)]
		cues = np.concatenate(cues,0)

		print(epochs.shape)
		print(cues.shape)

		epochs, cues = self.preprocess(epochs,cues)
		return ((np.float32(epochs).copy()),cues.copy())
	
	def load_fake(self,ones,zeros):
		epochs,cues = self.data
		n = int(self.fake_percentage*len(epochs)/2)
		ones = np.load(ones)[0:n]
		zeros = np.load(zeros)[0:n]
		epochs = np.concatenate([epochs,ones,zeros],0)
		cues = np.concatenate([cues,np.ones(len(ones)),np.zeros(len(zeros))])
		return ((np.float32(epochs).copy()),cues.copy())
	
	def set_epoch(self,start,length):
		self.input_start = start + self.t_baseline
		self.input_end = self.input_start + length
	
	
	def filter(self,
			x,
			notch_freq=50):
		
		nyquist = self.fs/2
		b,a = iirnotch(notch_freq,30,self.fs)
		x = filtfilt(b,a,x)
		return x


	def filter(self,
			x,
			notch_freq=50):
		
		nyquist = self.fs/2
		b,a = iirnotch(notch_freq,30,self.fs)
		x = filtfilt(b,a,x)
		return x

	def preprocess(self,x,y):
		"""
		Apply filters and additional preprocessing
		"""

		return x,y
	
class OpenBCISubject(subject_dataset):

	def __init__(self, 
			  dfs,
			  subject_channels,
			  fs=256,
			  t_baseline=0,
			  t_epoch=8,
			  stride=25,
			  epoch_length=512):
		
		self.fs = fs
		self.t_baseline = t_baseline
		self.t_epoch = t_epoch

		self.dfs = dfs

		self.epochs,self.cues = subject_epochs(dfs,subject_channels,stride=stride,
										 epoch_length=epoch_length)
		self.epochs,self.cues = self.epoch_preprocess(self.epochs,self.cues)

	def epoch_preprocess(self, x, y, notch_freq=60,low=4,high=50):

		n,t,d = x.shape
		x = rearrange(x,"n t d -> (n d) t")
		b,a = iirnotch(notch_freq,30,self.fs)
		x = filtfilt(b,a,x)
		nyquist = self.fs/2
		b,a = butter(4,[low/nyquist,high/nyquist],"bandpass",analog=False)
		x = filtfilt(b,a,x)
		x = rearrange(x,"(n d) t -> n t d",d=d)
		return x,y

class OpenBCIDataset(EEGDataset):

	def __init__(self,
		subject_splits:list[list[str]],
		dataset:Optional[dict] = None,
		save_paths:Optional[list[str]] = None,
		fake_data=None,
		dataset_type: Optional[subject_dataset] = None,
		fake_percentage:float = 0.5,
		fs:float = 256, 
		t_baseline:float = 0, 
		t_epoch:float = 8,
		channels:Iterable = np.array([0,1,2]),
		sanity_check:bool=False,
		**kwargs,):

		self.fs = fs
		self.t_baseline = t_baseline
		self.t_epoch = t_epoch
		self.fake_percentage = fake_percentage
		self.save_paths = save_paths

		if dataset is None:
			print("Loading saved data")
			self.data = self.load_data(save_paths,subject_splits,channels)
		else:
			print("Saving new data")
			self.save_dataset(dataset,save_paths[0],dataset_type,**kwargs)
			self.data = self.load_data(save_paths,subject_splits,channels)

		if fake_data is not None:
			print("we have fake data")
			self.data = self.load_fake(*fake_data)

		if sanity_check:
			self.sanity_check()

		print(f"final data shape: {self.data[0].shape}")

	def save_dataset(self, 
			dataset: dict, 
			path: str, 
			dataset_type: OpenBCISubject,
			**kwargs,):
		
		if not os.path.isdir(path):
			os.makedirs(path)

		for idx,(k,subject) in enumerate(dataset.items()):
			for split in ["train","test"]:
				set = dataset_type(subject[split],fs=self.fs,t_baseline=self.t_baseline,
								   t_epoch=self.t_epoch,**kwargs)
				epochs = np.float32(set.epochs)
				cues = set.cues
				np.save(os.path.join(path,f"subject_{idx}_{split}_epochs.npy"),epochs)
				np.save(os.path.join(path,f"subject_{idx}_{split}_cues.npy"),cues)

	def load_data(self,
			   paths,
			   subject_splits,
			   channels):
		
		epochs = []
		cues = []

		for path in paths:

			for idx,splits in enumerate(subject_splits):
				for split in splits:
					epochs.append(np.load(os.path.join(path,f"subject_{idx}_{split}_epochs.npy")))
					cues.append(np.load(os.path.join(path,f"subject_{idx}_{split}_cues.npy")))

		epochs = rearrange(np.concatenate(epochs,0),"n t d -> n d t")[:,channels,:]
		cues = np.concatenate(cues,0)

		print(epochs.shape)
		print(cues.shape)

		epochs, cues = self.preprocess(epochs,cues)
		return ((np.float32(epochs).copy()),cues.copy())
	
	def plot_sample(self):

		x = self.data[0][0]
		d,t = x.shape

		plt.figure(figsize=(10,d*2))

		for i in range(d):

			plt.subplot(d,1,i+1)
			plt.plot(x[i])
			plt.title(f"Channel {i+1}")
			plt.xlabel("")
			plt.ylabel("Amplitude ($\mu V$)")

			if i < d - 1:
				plt.xticks([])

		plt.tight_layout()
		plt.show()

class CSPOpenBCISubject(OpenBCISubject):

	def __init__(self, 
			  dfs,
			  subject_channels,
			  fs=256,
			  t_baseline=0,
			  t_epoch=8,
			  **kwargs):
		super().__init__(dfs,subject_channels, fs, t_baseline, t_epoch,**kwargs)

	def epoch_preprocess(self, x, y, notch_freq=60, low=4, high=50):
		x,y = super().epoch_preprocess(x, y, notch_freq, low, high)

		ax = []

		for i in range(1,10):
			ax.append(self.bandpass(x,self.fs,4*i,4*i+4))
		x = np.concatenate(ax,-1)
		mu = np.mean(x,axis=-1)
		sigma = np.std(x,axis=-1)
		x = (x-rearrange(mu,"n d -> n d 1"))/rearrange(sigma,"n d -> n d 1")
		return x,y

	def bandpass(self,
			  x,
			  fs,
			  low,
			  high,):
		
		nyquist = fs/2
		b,a = butter(4,[low/nyquist,high/nyquist],"bandpass",analog=False)
		n,t,d = x.shape
		x = rearrange(x,"n t d -> (n d) t")
		x = filtfilt(b,a,x)
		x = rearrange(x,"(n d) t -> n t d",n=n)
		return x