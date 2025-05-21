import pandas as pd

# Cargar el archivo
df = pd.read_parquet('train-00000-of-00001.parquet')

# Ver las primeras filas
print(df.head())
