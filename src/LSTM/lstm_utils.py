import pandas as pd
import numpy as np
import keras.backend as K


def minutizer(data, split: int = 5, ground_features: int = 5):
    n, d = data.shape
    new_data = pd.DataFrame(np.zeros((int(n/split) - 1, d)), columns=list(data))
    for i in range(int(n/split) - 1):
        for j in range(int(d/ground_features)):
            # Close
            new_data.iloc[i, j * ground_features] = data.iloc[split * (i + 1), j * ground_features]
            # High
            new_data.iloc[i, j * ground_features + 1] = max([data.iloc[split*i+k, j * ground_features + 1]
                                                             for k in range(split)])
            # Low
            new_data.iloc[i, j * ground_features + 2] = min([data.iloc[split * i + k, j * ground_features + 2]
                                                             for k in range(split)])
            # Open
            new_data.iloc[i, j * ground_features + 3] = data.iloc[split*i, j * ground_features + 3]
            # Volume
            new_data.iloc[i, j * ground_features + 4] = np.sum(data.iloc[i*split:(i+1)*split, j * ground_features + 4])
    return new_data


def preprocess_2_multi(data, tickers: list, ground_features: int = 5, new_features: int = 4):
    n, d = data.shape
    new_d = int(d/ground_features)
    new_data = np.zeros((n, new_d * new_features))
    open_prices = np.zeros((n, new_d))
    for i in range(new_d):
        new_data[:, new_features * i] = \
            data.iloc[:, ground_features * i]/data.iloc[:, ground_features * i + 3] - 1  # Returns
        new_data[:, new_features * i + 1] = \
            data.iloc[:, ground_features * i + 1] - data.iloc[:, ground_features * i + 2]  # Spread
        new_data[:, new_features * i + 2] = \
            (data.iloc[:, ground_features * i + 4] - np.min(data.iloc[:, ground_features * i + 4]))/ \
            (np.max(data.iloc[:, ground_features * i + 4]) - np.min(data.iloc[:, ground_features * i + 4]))  # Volume
        new_data[:, new_features * i + 3] = \
            (data.iloc[:, ground_features * i + 3] - np.min(data.iloc[:, ground_features * i + 3]))/ \
            (np.max(data.iloc[:, ground_features * i + 3]) - np.min(data.iloc[:, ground_features * i + 3]))  # open prize
        #new_data[:, new_features * i + 4] = \
        #    np.sin(2 * np.pi * new_data[:, new_features * i + 3]/np.max(new_data[:, new_features * i + 3]))  # Sin
        open_prices[:, i] = data.iloc[:, ground_features * i + 3]
    header_data = []
    header_open = []
    for ticker in tickers:
        header_data.append(ticker + '_returns')
        header_data.append(ticker + '_spread')
        header_data.append(ticker + '_volume')  # Normalized
        header_data.append(ticker + '_normalized_open')
        #header_data.append(ticker + '_sin_returns')
        header_open.append(ticker + '_open')
    return pd.DataFrame(new_data, columns=header_data), pd.DataFrame(open_prices, columns=header_open)

def preprocess_2_single(data, ticker: str, ground_features: int = 5, new_features: int = 5):
    n, d = data.shape
    new_d = int(d/ground_features)
    new_data = np.zeros((n, new_d * new_features))
    open_prices = np.zeros((n, new_d))
    for i in range(new_d):
        new_data[:, new_features * i] = \
            data.iloc[:, ground_features * i]/data.iloc[:, ground_features * i + 3] - 1  # Returns
        new_data[:, new_features * i + 1] = \
            data.iloc[:, ground_features * i + 1] - data.iloc[:, ground_features * i + 2]  # Spread
        new_data[:, new_features * i + 2] = \
            data.iloc[:, ground_features * i + 4]  # Volume
        new_data[:, new_features * i + 3] = \
            data.iloc[:, ground_features * i + 3]  # Open price
        new_data[:, new_features * i + 4] = \
            np.sin(2 * np.pi * new_data[:, new_features * i + 3]/np.max(new_data[:, new_features * i + 3]))  # Sin

        open_prices[:, i] = data.iloc[:, ground_features * i + 3]
    header_data = []
    header_open = []
    header_data.append(ticker + '_returns')
    header_data.append(ticker + '_spread')
    header_data.append(ticker + '_volume')  # Normalized
    header_data.append(ticker + '_normalized_open')
    header_data.append(ticker + '_sin_returns')
    header_open.append(ticker + '_open')
    return pd.DataFrame(new_data, columns=header_data), pd.DataFrame(open_prices, columns=header_open)

def combine_ts(tickers: list):
    stock0 = tickers[0]
    path = '../data/sectors/Information Technology/'+stock0+'.csv'
    data = pd.read_csv(path, index_col="timestamp", parse_dates=True)
    renamer = {'close': stock0+'_close', 'high': stock0+'_high', 'low': stock0+'_low',
               'open': stock0+'_open', 'volume': stock0+'_volume', }
    data = data.rename(columns=renamer)
    tickers.remove(tickers[0])
    for str in tickers:
        path = '../data/sectors/Information Technology/'+str+'.csv'
        new_data = pd.read_csv(path, index_col="timestamp", parse_dates=True)
        renamer = {'close': str+'_close', 'high': str+'_high', 'low': str+'_low',
                   'open': str+'_open', 'volume': str+'_volume', }
        new_data = new_data.rename(columns=renamer)

        data = pd.concat([data, new_data], axis=1, sort=True)
    tickers.insert(0, stock0)
    return data.interpolate()[1:data.shape[0]]

def customized_loss(y_pred, y_true):
    num = K.sum(K.square(y_pred - y_true), axis=-1)
    y_true_sign = y_true > 0
    y_pred_sign = y_pred > 0
    logicals = K.equal(y_true_sign, y_pred_sign)
    logicals_0_1 = K.cast(logicals, 'float32')
    den = K.sum(logicals_0_1, axis=-1)
    return num/(1 + den)



