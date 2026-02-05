# python -m scripts.check_data.check_concert_consistency
import pandas as pd
import os

def check_concert_consistency(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: No se encontró el archivo en {file_path}")
        return

    print(f"Leyendo archivo: {file_path}...")
    # Leemos todo el Excel
    df = pd.read_excel(file_path)

    # Agrupamos por la llave primaria del concierto
    grouped = df.groupby(['Fecha', 'Venue'])

    # Columnas que deben ser 100% idénticas en todas las filas del grupo
    columns_to_check = [
        "Tipo de Concierto", 
        "Tipo de Lugar", 
        "Tour", 
        "Ciudad", 
        "Código Estado", 
        "Nombre Estado", 
        "País", 
        "Continente"
    ]

    inconsistencies_found = 0

    print("\n--- REPORTE DE INCONSISTENCIAS ENCONTRADAS ---\n")

    for (fecha, venue), group in grouped:
        log_entry = []
        
        for col in columns_to_check:
            # Obtenemos todos los valores incluyendo nulos
            # fillna("VACÍO") nos ayuda a comparar celdas en blanco como un valor real
            values_with_nulls = group[col].fillna("VACÍO").unique()
            
            # Si hay más de un valor único (ej: ['Tour X', 'VACÍO'] o ['Tour X', 'Tour Y'])
            if len(values_with_nulls) > 1:
                log_entry.append(f"  - {col}: Conflicto de datos -> {list(values_with_nulls)}")

        if log_entry:
            inconsistencies_found += 1
            print(f"⚠️ ERROR en Concierto: {fecha} | {venue}")
            for error in log_entry:
                print(error)
            print("-" * 60)

    if inconsistencies_found == 0:
        print("✅ ¡Excelente! No se detectaron inconsistencias en las 47,000 filas.")
    else:
        print(f"\nSe encontraron {inconsistencies_found} conciertos con datos inconsistentes.")

if __name__ == "__main__":
    # Asegúrate de poner la ruta correcta aquí
    FILE_PATH = "D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\Conciertos-Consolidado.xlsx"
    check_concert_consistency(FILE_PATH)