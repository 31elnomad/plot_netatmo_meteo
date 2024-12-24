import argparse
import configparser
import sys

# Add the path containing the required scripts. / Ajoutez le chemin contenant les scripts nécessaires.
sys.path.append('scripts')

# Import the "token" module from getdata_api. / Importer le module "token" depuis getdata_api.
from getdata_api import token

def main():
    """
    Main entry point of the program. / Point d'entrée principal du programme.
    Reads the configuration from a specified file and executes the 'getdata' method of the token object.
    Lit la configuration depuis un fichier spécifié et exécute la méthode 'getdata' de l'objet token.
    """
    # Initialize the command-line argument parser. / Initialiser l'analyseur d'arguments de la ligne de commande.
    parser = argparse.ArgumentParser(description="Script to fetch data using an API. / Script pour récupérer des données via une API.")
    parser.add_argument(
        "-cfg", 
        help="Path to the configuration file (.cfg). / Chemin vers le fichier de configuration (.cfg).", 
        required=True
    )
    args = parser.parse_args()

    # Load the configuration file. / Charger le fichier de configuration.
    config = configparser.ConfigParser()
    try:
        config.read(args.cfg)
    except Exception as e:
        print(f"Error reading the configuration file: {e} / Erreur lors de la lecture du fichier de configuration : {e}")
        sys.exit(1)

    # Create and use the `token` object to fetch data. / Créer et utiliser l'objet `token` pour récupérer des données.
    data_obj = token(config)
    data_obj.getdata()
    quit()
    try:
        data_obj = token(config)
        data_obj.getdata()
    except Exception as e:
        print(f"Error executing 'getdata': {e} / Erreur lors de l'exécution de 'getdata' : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
