from __future__ import absolute_import
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

import time
import tensorflow as tf
from tensorflow.keras.models import Sequential,model_from_json
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten
from tensorflow.keras.layers import Conv2D, MaxPooling2D
from tensorflow.keras import models

import numpy as np
import matplotlib.pyplot as plt
from  . import networks 

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import seaborn as sns
from sklearn.metrics import accuracy_score

def timeit(func):
    def ntimes(*args, **kw):
        start = time.time()
        value = func(*args, **kw)
        end = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', func.__name__.upper())
            kw['log_time'][name] = int((end - start) * 1000)
        else:
            print('%r  %2.2f ms' % \
                  (func.__name__, (end - start) * 1000))
        return value
    return ntimes
	
	
def create_model_output_folder(outputName):
	if "\\" in outputName:
		outputName=outputName.replace('\\','/')
	folder= outputName.replace(outputName.split('/')[-1],'')
	if not os.path.exists(folder):
		os.makedirs(folder)	

def check_model_exists(outputName):
	if not os.path.exists(outputName+'.json'):
		print("\n\n\n \tModel Doesnt Exist \n\n\n")
		return False
	else:
		print("\n\n\n \tUsing Model: {:}.json \n\n\n".format(outputName))
		return True
		
def save_model_and_weights(model,outputName):
	create_model_output_folder(outputName)
	model.save_weights(outputName+'_wgts.h5')
	open(outputName+'_arch.json', 'w').write(model.to_json())


def load_model_and_weights(modelName, summary = False):
	model = model_from_json(open(modelName+'_arch.json', 'r').read())
	if summary == True:
		model.summary()		
	model.load_weights(modelName+'_wgts.h5')
	return model

def modelManager(modelName,x_train, OUTPUT_CLASSES, RETRAIN_MODEL, AI_NAME= 'tinyMedNet'):
	if RETRAIN_MODEL== True:
		if check_model_exists(modelName):
			model = load_model_and_weights(modelName = modelName)
		else:
			nw = networks.get(AI_NAME)
			model = nw(x_train.shape[1:],OUTPUT_CLASSES)
			
	else:
		nw = networks.get(AI_NAME)
		model = nw(x_train.shape[1:],OUTPUT_CLASSES)
	
	return model
	
def show_model_details(model):
	model.summary()	

def train(	model, x_train, y_train, 
			batch_size=1,epochs=1, 
			learning_rate=0.001, callbacks=None, validation_data = None
		  ):
	model.compile(optimizer=tf.keras.optimizers.Adam(lr=learning_rate),
				  loss='sparse_categorical_crossentropy',
				  metrics=['accuracy'])
	if callbacks is not None:
		if ('tensorboard'in callbacks):
			logdir=os.path.join('log')
			tensorboard_callback = tf.keras.callbacks.TensorBoard(logdir, histogram_freq=1)
			idx = callbacks.index("tensorboard")	
			callbacks[idx] = tensorboard_callback

	result = model.fit(x_train, y_train,
			  batch_size=batch_size,
			  epochs=epochs,
			  validation_data=validation_data,
			  callbacks=callbacks
			  )
	return result.history

def plot_training_metrics(result, theme= 'light'):
	result['Epoch'] = np.arange(0, len(result['accuracy']), 1)

	fig = make_subplots(
		rows=2, cols=1,
		shared_xaxes=True,
		x_title = "Epoch Num",
		vertical_spacing=0.1,
		subplot_titles = ('Train and Test Accuracy vs Epochs', 'Train and Test Loss vs Epochs' ),
		specs=[
				[{"type": "scatter"}],
				[{"type": "scatter"}],
			]
	)
	fig.add_trace(go.Scatter(x=result['Epoch'], y=result['accuracy'], mode='lines', name='Train Accuracy'),row=1, col=1)
	fig.add_trace(go.Scatter(x=result['Epoch'], y=result['val_accuracy'], mode='lines', name='Test Accuracy'),row=1, col=1)

	fig.add_trace(go.Scatter(x=result['Epoch'], y=result['loss'], mode='lines', name='Train loss',yaxis="y2"),row=2, col=1)
	fig.add_trace(go.Scatter(x=result['Epoch'], y=result['val_loss'], mode='lines', name='Test loss',),row=2, col=1)
	if theme.lower()=='dark':
		fig.update_layout( template="plotly_dark")
	fig.update_layout(
		yaxis=dict(title="ACCURACY"),
		yaxis2=dict(title="LOSS"),
	)
	fig.show()
	
def predict_labels(model , input, expected_output = None, labelNames=None,top_preds=4):
	"""
	predict(x, batch_size=None, verbose=0, steps=None, callbacks=None, max_queue_size=10, workers=1, use_multiprocessing=False)
	"""
	output = model.predict(input)
	inds = np.argsort(output)
	labelLength = expected_output.shape[1]-1
	for j in range(0, len(inds)):
		if expected_output is not None:
			print(20*'=')
			"""
			TODO : Need to fix label lookup when the expected output is not a single number 
			"""
			print('Expected :',labelNames[expected_output[j][labelLength]])
			print(20*'-')
		for i in range(top_preds):
			print(labelNames[inds[j][-1-i]],':',str(round(output[j][inds[j][-1-i]]*100,2)), '%')

def decode_predictions(out, labelNames=None,top_preds=4):
	predArr =[]
	for j in range(0, len(out)):
		indexes = np.argsort(out)
		for i in range(top_preds):
			predArr.append((i+1, labelNames[indexes[j][-1-i]],round(out[j][indexes[j][-1-i]]*100,2)))
	return predArr	

def get_accuracy(test_labels, test_predictions):
	return accuracy_score(test_labels, test_predictions)
	
def plot_confusion_matrix(model, test_data, test_labels, labelNames, title='Confusion Matrix'):
	test_predictions = model.predict_classes(test_data)
	con_mat = tf.math.confusion_matrix(labels=test_labels, predictions=test_predictions).numpy()
	con_mat_norm = np.around(con_mat.astype('float') / con_mat.sum(axis=1)[:, np.newaxis], decimals=2)
 
	con_mat_df = pd.DataFrame(con_mat_norm,
					 index = labelNames, 
					 columns = labelNames)

	figure = plt.figure(figsize=(8, 8))
	sns.heatmap(con_mat_df, annot=True, cmap=plt.get_cmap('PuRd') )
	plt.title("Easy-AI\n\n", loc='center', fontsize=18,color='grey')
	
	plt.title('{:}\nModel Accuracy:{:.2f}%'.format(title,float(get_accuracy(test_labels, test_predictions)*100)),loc='left', fontsize=13, )
	plt.ylabel('True label')
	plt.xlabel('Predicted label')
	plt.show()
		

