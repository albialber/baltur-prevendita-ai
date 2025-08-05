import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
import faiss

# Carica il file Excel (modifica il nome se serve)
df = pd.read_excel("listino_prodotti.xlsx")

# Controllo colonne obbligatorie
colonne_attese = {"Codice", "Prodotto", "Prezzo di listino", "Descrizione"}
if not colonne_attese.issubset(df.columns):
    raise ValueError(f"Il file Excel deve contenere le colonne: {colonne_attese}")

# Prepara i testi da embeddare
testi = (
    df["Codice"].fillna('').astype(str) + " " +
    df["Prodotto"].fillna('').astype(str) + " " +
    df["Descrizione"].fillna('').astype(str)
).str.lower().tolist()

# Embedding
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(testi)

# Costruisci l’indice FAISS
dimensione = embeddings[0].shape[0]
index = faiss.IndexFlatL2(dimensione)
index.add(np.array(embeddings))

# Salva tutto in un file
with open("embeddings.pkl", "wb") as f:
    pickle.dump({
        "df": df,
        "embeddings": embeddings,
        "index": index
    }, f)

print("✅ Embedding salvato in 'embeddings.pkl'")
