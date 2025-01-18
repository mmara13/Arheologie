import os
import pandas as pd
from pathlib import Path

def strip_accents(text):
    text = text.replace("â", "i")
    text = text.replace("Â", "I")
    text = text.replace("ș", "s")
    text = text.replace("ş", "s")
    text = text.replace("Ș", "S")
    text = text.replace("Ş", "S")
    text = text.replace("ț", "t")
    text = text.replace("ţ", "t")
    text = text.replace("Ț", "T")
    text = text.replace("Ţ", "T")
    text = text.replace("î", "i")
    text = text.replace("Î", "I")
    text = text.replace("ă", "a")
    text = text.replace("Ă", "A")
    return text

def create_csv_files():
    # Directorul principal
    base_dir = os.path.join(os.getcwd(), "stiri_siteuri")
    
    # Mapare nume folder la URL ziar
    newspaper_urls = {
        'md_agora': 'www.agora.md',
        'md_anticoruptie': 'www.anticoruptie.md',
        'md_bani': 'www.bani.md',
        'md_digi': 'https://www.digi24.ro/stiri/externe/moldova',
        'md_ea': 'www.ea.md',
        'md_noi': 'www.noi.md',
        'md_zdg': 'www.zdg.md',
        'md_zugo': 'www.zugo.md',
        'ro_digi': 'www.digi24.ro',
        'ro_hotnews': 'www.hotnews.ro',
        'ro_life': 'www.life.ro',
        'ro_pressone': 'www.pressone.ro'
    }
    
    # Liste pentru stocarea datelor
    ro_data = []
    md_data = []
    
    # Parcurge toate directoarele
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        
        # Verifică dacă e director
        if not os.path.isdir(folder_path):
            continue
            
        # Determină țara bazată pe prefixul folderului
        is_moldova = folder.startswith('md_')
        
        # Obține URL-ul ziarului
        newspaper = newspaper_urls.get(folder, folder)
        
        # Parcurge toate fișierele din folder
        for file in os.listdir(folder_path):
            # Procesează doar fișierele cu conținut (nu și cele cu titluri)
            if not file.startswith('t') and file.endswith('.txt'):
                file_number = file.replace('.txt', '')  # elimină extensia
                content_path = os.path.join(folder_path, file)
                title_path = os.path.join(folder_path, f't{file}')
                
                # Verifică dacă există ambele fișiere
                if os.path.exists(title_path):
                    try:
                        # Citește titlul și data
                        with open(title_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            title = lines[0].strip() if lines else "No title"
                            date = lines[1].strip() if len(lines) > 1 else "No date"
                        
                        # Înlătură diacriticele din titlu
                        title = strip_accents(title)
                        
                        # Crează entry-ul pentru CSV
                        entry = {
                            'file': f'{file_number}.txt',  # adaugă extensia .txt
                            'newspaper': newspaper,
                            'title': title,
                            'date': date,
                            'category': 'Stiri'
                        }
                        
                        # Adaugă la lista corespunzătoare
                        if is_moldova:
                            md_data.append(entry)
                        else:
                            ro_data.append(entry)
                            
                    except Exception as e:
                        print(f"Eroare la procesarea fișierului {file}: {e}")
    
    # Crează DataFrames
    ro_df = pd.DataFrame(ro_data)
    md_df = pd.DataFrame(md_data)
    
    # Sortează după coloana 'file'
    ro_df = ro_df.sort_values('file')
    md_df = md_df.sort_values('file')
    
    # Salvează CSV-urile
    ro_df.to_csv('ro.csv', index=False)
    md_df.to_csv('md.csv', index=False)
    
    print(f"Fișiere generate cu succes!")
    print(f"Număr de articole RO: {len(ro_df)}")
    print(f"Număr de articole MD: {len(md_df)}")

# Rulează funcția
if __name__ == "__main__":
    create_csv_files()
