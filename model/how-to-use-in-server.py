from tensorflow.keras.models import load_model
import joblib

# Завантаження
model = load_model("gesture_lstm_model.h5")
classes = np.load("gesture_labels.npy", allow_pickle=True)

def predict_gesture(csv_path):
    df = pd.read_csv(csv_path)
    data = df.values
    data_scaled = scaler.transform(data)  # той самий scaler, навчений на train
    data_scaled = np.expand_dims(data_scaled, axis=0)  # (1, 75, 39)
    pred = model.predict(data_scaled)
    label = classes[np.argmax(pred)]
    return label
