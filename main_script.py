from pre_processing import Pre_processing
from Dataset import loop_register_users, get_data
import training
import os
import numpy as np
import feat_analysis


def main():

    if not os.path.exists('./data/database.xlsx'):
        loop_register_users('./data/')

    perform_preprocessing()
    build_model()

def perform_preprocessing():

    feature_space = './data/feats/'
    data_path = './data/database.xlsx'

    # If haven't calculated features, do it
    if not len(os.listdir(feature_space)):
        num_mel_coeffs = 10
        fs = 8000
        df = get_data(data_path)
        audio_model = Pre_processing(fs, num_mel_coeffs)

        for key, val in df.items():
            signals = df[key]

            for col in range(1, signals.shape[1]): 
                S = signals.iloc[1:,col].to_numpy()

                spect = audio_model.mel_spect(S, power_2_db = True)
                dSdT = audio_model.mel_spec_deriv(spect)
                dS2dT2 = audio_model.mel_spec_deriv(dSdT)
                feat, stats = audio_model.stats(S)

                features = np.array([spect, dSdT, dS2dT2, stats], dtype=object)

                path_to_feat = feature_space + key + '_' + str(col) + '.npy'
                np.save(path_to_feat, features)

def build_model():
    feat_space = './data/feats/'

    X = {}
    Y = {}

    data = {}

    class_no = 0

    for spect_path in os.listdir(feat_space):
        label, ind = spect_path.split('_')

        obj = np.load(feat_space+spect_path, allow_pickle=True)
        data['Spect'] = obj[0]
        data['dSdT'] = obj[1]
        data['dS2dT2'] = obj[2]
        data['stats'] = obj[3]

        if label not in Y.keys():
            Y[label] = class_no
            X[class_no] = []
            class_no += 1

        this_class = Y[label]
        X[this_class].append(data)

    feat_analysis.analyze_corr(X,Y)

    X_train = []
    Y_train = []
    for i in range(class_no):
        X_train.extend(X[i])
        Y_train.extend([l for l in range(len(X[i]))])

    X_train = np.array(X_train)
    Y_train = np.array(Y_train)
    model = training.get_model(inp_shape=X_train.shape, num_class=class_no)
    
    model.fit(X_train, Y_train, batch_size=16, epochs=3)



if __name__ == "__main__":
    main()