from __future__ import absolute_import
import os

def datasetFolderStructureValidate(folder):
	dirs = os.listdir(folder)
	test = train = val = False
	dirsDict = {}
	if ('test' in dirs):
		print("'test' Folder Present")
		test = True 
	if ('train' in dirs):
		print("'train' Folder Present")
		train = True
	if ('validate' in dirs):
		print("'validate' Folder Present")

	assert train == True, "NO 'train' Folder found"
	assert test == True, "NO 'test' Folder found"
	
	return dirs

def getLabelsFromFolder(folder):
	dirs  = datasetFolderStructureValidate(folder)
	labels = os.listdir(os.path.join(folder, 'train'))
	labels_test = labels_val = None
	if ('test' in dirs):
		labels_test = os.listdir(os.path.join(folder, 'test'))
	if ('validate' in dirs):
		labels_val = os.listdir(os.path.join(folder, 'validate'))
	if labels_test:
		assert labels ==  labels_test, "Train and Test Labels Dont Match"
	if labels_val:
		assert labels ==  labels_val, "Train and Validation Labels Dont Match"
	
	#dirs = [os.path.join(folder,x) for x in dirs]
	return dirs, labels

import numpy as np
from PIL import Image
import tqdm
from sklearn.preprocessing import LabelBinarizer,LabelEncoder

def _labelMapper(labelNames, labelMap):
	y_idx = []
	for sample in labelNames:
		y_idx.append(np.array([labelMap[sample]]))
	return y_idx
	
def _rgb_dataset_from_folder(Folder, labels, labelMap, inpPreProc):
	DataSet = []
	LabelSet =[]
	for label in labels:
		classFolder = os.path.join(Folder, label)
		SetItems = os.listdir(classFolder)
		for image in SetItems:
			img = Image.open(os.path.join(classFolder, image))
			if img.mode != 'RGB':
				img = img.convert('RGB')
			img = np.array(img)
			DataSet.append(img)
			LabelSet.append(label)
	DataSet = np.array(DataSet)
	y_train = _labelMapper(LabelSet, labelMap)
	y_train = np.array(y_train)
	DataSet = inpPreProc.resizeDataSet(DataSet)
	return (DataSet, y_train)

def _baseLabelMapper(labels):
	le = LabelEncoder()
	onehotCodeLabels = le.fit_transform(labels)
	labelDict = {}
	for k,v in zip(labels,onehotCodeLabels):
		labelDict[k] = v
	return labelDict



class INPUT_PROCESSOR:
	def __init__(self, targetDim=(31,31), samplingMethod=None,normalize=False):
			
		self.output_size		= targetDim
		self.normalize			= normalize
		if samplingMethod:
			if samplingMethod.lower()=='box':
				self.samplingMethod =Image.BOX
			elif samplingMethod.lower()=='nearest':
				self.samplingMethod =Image.NEAREST
			elif samplingMethod.lower()=='bilinear':
				self.samplingMethod =Image.BILINEAR
			elif samplingMethod.lower()=='hamming':
				self.samplingMethod =Image.HAMMING
			elif samplingMethod.lower()=='bicubic':
				self.samplingMethod =Image.BICUBIC
			elif samplingMethod.lower()=='lanczos':
				self.samplingMethod =Image.LANCZOS		
			else:
				self.samplingMethod =Image.NEAREST
		else:
			self.samplingMethod =Image.NEAREST

	def resizeDataSet(self,dataset):
		processedData = []
		for i in tqdm.tqdm(range(0,dataset.shape[0])):
			im = Image.fromarray(dataset[i])
			im_r = im.resize((self.output_size),self.samplingMethod)
			np_im = np.array(im_r)
				
			processedData.append(np_im)
		processedData = np.array(processedData)
		if self.normalize:
			processedData = processedData/255.0
		return processedData

class datasetManager(INPUT_PROCESSOR):
	def __init__(self,folder, targetDim=(31,31), normalize=False , name = 'Dataset', useCache=True , forceCleanCache = False):
		super().__init__(targetDim=targetDim, normalize=normalize)
		self.folder = folder
		self.name = name
		self.useCache = useCache
		self.dirs, self.labels = getLabelsFromFolder(folder)
		self.labelMap  = _baseLabelMapper(self.labels)
		self.cachefile = self.name+'_'+ str(self.output_size[0]) + '_' + str(self.output_size[1])+ '_'+str(self.samplingMethod)+'_N'+str(self.normalize)+'.npz'
		if self.useCache and not forceCleanCache and os.path.exists(self.cachefile):
			self.reload_data()
		else:
			self.process_dataset()
			
	def process_dataset(self):
			trainFolder = os.path.join(self.folder,'train')
			(self.x_train, self.y_train) = _rgb_dataset_from_folder(trainFolder, self.labels, self.labelMap, self)
			# Test Data Preparataio, if Present
			if ('test' in self.dirs):
				(self.x_test, self.y_test) = _rgb_dataset_from_folder(os.path.join(self.folder,'test'), self.labels, self.labelMap, self)
				print('Test Shape:', self.x_test.shape) 
				
			# Validation Data Preparataio, if Present
			if ('validate' in self.dirs):
				(self.x_val, self.y_val) = _rgb_dataset_from_folder(os.path.join(self.folder,'validate'), self.labels, self.labelMap, self)
				print('Validate Shape:', self.x_val.shape) 
				
			print('Train Shape:', self.x_train.shape)
			
			if self.useCache:
				self.cache_data()

	def reload_data(self):
		print('Reloading Dataset from Cache')
		cached = np.load(self.cachefile)
		(self.x_test, self.y_test) = (cached['x_test'], cached['y_test'])
		(self.x_train, self.y_train) = (cached['x_train'], cached['y_train'])
		print(self.x_train.shape)
		
	def cache_data(self):
		print('Caching Dataset')
		np.savez_compressed(self.cachefile, x_train=self.x_train, y_train=self.y_train,
									x_test = self.x_test, y_test = self.y_test)


	def load_data(self):
		return (self.x_train, self.y_train), (self.x_test, self.y_test)

def datasetManagerFunc(folder,targetDim=(31,31), normalize=False):
	dirs, labels = getLabelsFromFolder(folder)
	labelMap  = _baseLabelMapper(labels)
	print(labelMap)

	# Create Preprocessor
	inpPreProc = INPUT_PROCESSOR(targetDim=targetDim, normalize=normalize)

	# Train Data Preparataion
	trainFolder = os.path.join(folder,'train')
	(x_train, y_train) = _rgb_dataset_from_folder(trainFolder, labels, labelMap, inpPreProc)

	# Test Data Preparataio, if Present
	if ('test' in dirs):
		(x_test, y_test) = _rgb_dataset_from_folder(os.path.join(folder,'test'), labels, labelMap, inpPreProc)
		print('Test Shape:', x_test.shape) 
		
	# Validation Data Preparataio, if Present
	if ('validate' in dirs):
		(x_val, y_val) = _rgb_dataset_from_folder(os.path.join(folder,'validate'), labels, labelMap, inpPreProc)
		print('Validate Shape:', x_val.shape) 
		
	print('Train Shape:', x_train.shape) 
	return (x_train, y_train), (x_test, y_test)

if __name__ == "__main__":
	mainFolder = "chest-xray-pnumonia-covid19"
	v = datasetManager(mainFolder,targetDim=(96,96), normalize=False)	 

