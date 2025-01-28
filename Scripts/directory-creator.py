import os
from pathlib import Path

def create_directory_structure(base_path='.'):
    # Konvertera relativ sökväg till absolut
    base_path = os.path.abspath(base_path)
    
    # Definiera strukturen för både desktop och android
    structure = {
        'Pages': {
            'desktop': {
                'Layout': {
                    'Page1': {
                        'Components': {
                            'Widgets': {
                                'Header': {},
                                'Content': {},
                                'Footer': {}
                            },
                            'Core': {},
                            'QFrames': {
                                'Header': {},
                                'Content': {},
                                'Footer': {}
                            },
                            'Controllers': {}
                        }
                    },
                    'State': {}
                }
            },
            'android': {}
        }
    }

    def create_directories(current_path, structure):
        for dir_name, substructure in structure.items():
            # Skapa fullständig sökväg för aktuell mapp
            dir_path = os.path.join(current_path, dir_name)
            
            try:
                # Skapa mappen om den inte redan finns
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                print(f"Skapade/Verifierade mapp: {dir_path}")
                
                # Fortsätt rekursivt med undermappar
                if substructure:
                    create_directories(dir_path, substructure)
                    
            except Exception as e:
                print(f"Fel vid skapande av {dir_path}: {str(e)}")

    try:
        create_directories(base_path, structure)
        print("\nKlart! Mappstrukturen har skapats/verifierats.")
    except Exception as e:
        print(f"Ett oväntat fel uppstod: {str(e)}")

if __name__ == "__main__":
    # Använd aktuell mapp som bas
    create_directory_structure()
