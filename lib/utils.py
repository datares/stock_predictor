
import os
import time
# import ta
import tqdm
from tqdm import tqdm_notebook

## Data Processing
import pandas as pd
import numpy as np
import matplotlib as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.externals import joblib 

#### DATA CREATION FUNCTIONS ####
def create_data(file_list):
    """
    Utility function to create a dataset from a filelist.
    """
    counter = 1
    df_list = pd.DataFrame()
    for file in file_list:
        if (os.stat(file).st_size != 0):
            df = pd.read_csv(file, sep = ",")
            df['symbol'] = file
            df_list = df_list.append(df)
            print (counter, " out of ", len(file_list))
            counter += 1
    return pd.DataFrame(df_list)

def fetch_data():
    """
    Get the files from the data folder. 
    """
    main_dir = os.getcwd()
    # STOCKS
    os.chdir(main_dir)
    os.chdir("./data/Stocks")
    stock_list = os.listdir()
    stocks = create_data(stock_list)
    #ETFs
    os.chdir(main_dir)
    os.chdir("./data/ETFs")
    etf_list = os.listdir()
    etf = create_data(etf_list)

    return stocks, etf


#### DATA PROCESSING FUNCTIONS ####
def scale_df(data, model_name):
    """
    This class takes in a pandas dataframe and generates 
    the normalized version of it
    """
    # scales the data
    scaler = MinMaxScaler()
    df = scaler.fit_transform(data)
    
    # saves the scaler to file
    joblib.dump(scaler, "./saved_models/{}.pkl".format(model_name))
    return df, scaler

def generate_ta(data):
    """
    Runs ta on a dataset and saves to csv.
    """
    # converts data into ta dataframe
    df = add_all_ta_features(data, "Open", "High", "Low", "Close", "Volume", fillna=True)
    df.to_csv("../data/df_ta.csv")
    
def build_window(df, look_back, n_features):
    """
    Builds sliding windows to shift the batch by 1 step at a time
    """
    x_train = [] # This list contain the sequences to predict when training
    y_train = [] # This list contain the next value of the sequences when training

    for i in range(look_back, df.shape[0]):
        x_train.append(df[i-look_back:i,0:n_features].tolist()) # ,0 used in order to return the values only
        y_train.append(df[i,0].tolist()) # tolist() converts np array to simple array
   
    # Converting arrays from lists to np arrays. 
    x_train = np.array(x_train)
    y_train = np.array(y_train)

    # Rounding numbers to speed up training.
    x_train = np.round(x_train, 5)
    y_train = np.round(y_train, 5)

    return x_train, y_train

def trim_dataset(mat, batch_size):
    """
    trims dataset to a size that's divisible by the batch size
    """

    no_of_rows_drop = mat.shape[0] % batch_size
    if(no_of_rows_drop > 0):
        return mat[:-no_of_rows_drop]
    else:
        return mat

#### FINAL PIPELINE FUNCTION ####
def preproc_pipeline(data, name):
    """
    The preprocessing pipeline takes in a csv of processed data and creates
    the training, validation, and test sets
    """
    # Scale values
    data, scaler = scale_df(data, name)
    # Split
    train_set, testval_set = train_test_split(data, train_size=0.75, test_size=0.25, shuffle=False)
    validation_set, test_set = train_test_split(testval_set, train_size=0.75, test_size=0.25, shuffle=False)
    
    return train_set, validation_set, test_set, scaler
def model_preproc_pipeline(data, look_back, batch_size, n_features):
    """
    preprocesses data for LSTM input
    """
    x_train, y_train = build_window(data, look_back, n_features)

    x_train = trim_dataset(x_train, batch_size)
    y_train = trim_dataset(y_train, batch_size)

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], n_features))
    return x_train, y_train
def generate_dataset():
        stocks, etf = create_data(".")
        data = pd.concat([stocks, etf])
        generate_ta(data)
        # we have to read file
        data = pd.read_csv("./df_ta.csv")