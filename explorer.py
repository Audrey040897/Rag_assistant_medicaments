import pandas as pd

# Lire seulement les 100 premières lignes pour comprendre la structure
print("Lecture des 100 premières lignes...")
df = pd.read_csv(
    "data/CIS_RCP.csv",
    sep="\t",
    encoding="latin-1",
    header=None,
    nrows=100
)

print(f"\nNombre de colonnes : {df.shape[1]}")
print(f"Nombre de lignes lues : {df.shape[0]}")
print("\n--- Aperçu des premières lignes ---")
print(df.head(10).to_string())

print("\n--- Types de données ---")
print(df.dtypes)

print("\n--- Valeurs uniques colonne 0 (premiers 20) ---")
print(df[0].unique()[:20])