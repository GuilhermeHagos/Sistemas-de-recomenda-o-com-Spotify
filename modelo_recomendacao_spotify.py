# %%
# Ideia: após treinar com musicas que eu ouço, mostrar playlist aleatória e pedir pra ele criar uma playlist com as musicas que mais se assemelham com que eu ouço
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# %%
load_dotenv()

#Acesso as variaveis de ambiente
CLIENT_ID= os.getenv('CLIENT_ID')
CLIENT_SECRET=os.getenv('CLIENT_SECRET')
REDIRECT_URI=os.getenv('REDIRECT_URI')

sp = spotipy.Spotify(auth_manager=SpotifyOAuth)(
    client_id = CLIENT_ID,
    client_secret = CLIENT_SECRET,
    redirect_uri = REDIRECT_URI,
    # alterei scope por entender qque o abaixo se adequa as ideias do projeto de contruir playlist através de outras
    scope = 'user-library-modify playlist-modify-public'
)