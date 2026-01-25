# python -m scripts.check_data.check_column_excel

import pandas as pd
import re
from pathlib import Path

# === CONFIGURACIÓN DINÁMICA ===
COLUMN_TO_AUDIT = "Compositores"  # Cambia esto por "Género", "Artistas invitados", etc.
# ==============================

def audit_excel_column(column_name):
    # 1. Configurar ruta del archivo
    current_dir = Path(__file__).parent
    file_path = current_dir.parent / "data_sources" / "santana_master_v2.xlsx"
    
    if not file_path.exists():
        print(f"❌ No se encontró el archivo en: {file_path}")
        return

    try:
        # 2. Leer Excel (leemos solo la columna de interés para optimizar)
        # Usamos None primero para validar columnas existentes
        df_headers = pd.read_excel(file_path, nrows=0)
        
        if column_name not in df_headers.columns:
            print(f"❌ Error: La columna '{column_name}' no existe en el Excel.")
            print(f"Columnas disponibles: {', '.join(df_headers.columns)}")
            return

        df = pd.read_excel(file_path, usecols=[column_name])
        
        # 3. Extraer valores únicos
        unique_values = set()
        raw_data = df[column_name].dropna()
        
        for entry in raw_data:
            # Dividir por ',' o '/' usando regex y limpiar espacios
            items = [item.strip() for item in re.split(r'[/,]', str(entry)) if item.strip()]
            
            for item in items:
                unique_values.add(item)
        
        # 4. Ordenar alfabéticamente
        sorted_list = sorted(list(unique_values))
        
        # 5. Mostrar resultados
        print(f"\n📊 AUDITORÍA DE COLUMNA: '{column_name}'")
        print(f"🔍 Se encontraron {len(sorted_list)} valores únicos:")
        print("—" * 50)
        
        for i, value in enumerate(sorted_list, 1):
            print(f"{i:03d}. {value}")
            
        return sorted_list

    except Exception as e:
        print(f"❌ Error crítico durante la auditoría: {e}")

if __name__ == "__main__":
    audit_excel_column(COLUMN_TO_AUDIT)