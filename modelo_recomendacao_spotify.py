# %%
# Ideia: após treinar com musicas que eu ouço, mostrar playlist aleatória e pedir pra ele criar uma playlist com as musicas que mais se assemelham com que eu ouço
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# %%
# Carregando arquivo contendo variaveis de ambiente
dotenv_path = 'E:\Programinhas\GitHub_Projects\Sistemas de recomendação com Spotify\Variaveis_ambiente.env'
load_dotenv(dotenv_path=dotenv_path)

# %%
#Acesso as variaveis de ambiente
SPOTIPY_CLIENT_ID= os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET=os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI=os.getenv('SPOTIPY_REDIRECT_URI')


# %%
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id = SPOTIPY_CLIENT_ID,
    client_secret = SPOTIPY_CLIENT_SECRET,
    redirect_uri = SPOTIPY_REDIRECT_URI,
    # alterei scope por entender qque o abaixo se adequa as ideias do projeto de contruir playlist através de outras
    scope = 'user-library-modify playlist-modify-public'
))


# %%

def get_audio_features_by_playlist(playlist_id):
    '''
    Função recebe como parâmetro o ID de uma playlist e retorna Dataframe contendo as features de audio das músicas contidas na playlist
    '''
    ## Buscando todas as músicas de uma playlist ( playlist_id) e associando a results
    results = sp.playlist_tracks(playlist_id)
    # as musicas são então adicionadas a lista tracks
    tracks = results['items']
    # Pelo tamanho da playlist, pode ser que a API do spotify venha paginado
    # então o while results garante que se houver, ele vai adicionar as músicas a playlist
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    # Lista vazia contendo as features das musicas é iniciada e através do sp.audio_features é feito a coleta das características de audio de cada música

    audio_features = []
    for item in tracks:
        track_id = item['track']['id']
        track_name = item['track']['name']
        artist_name = item['track']['artists'][0]['name']
        features = sp.audio_features(track_id)[0]
        if features:
            features['track_name'] = track_name
            features['artist'] = artist_name
            audio_features.append(features)
    return pd.DataFrame(audio_features)
# %%
minha_playlist_id = '1U4UVF4hG7C7UZafH1nITe'
df = get_audio_features_by_playlist(minha_playlist_id)
df.head(10)


# %%
## Teste inicial com modelo de ml kmeans
#features selecionadas abaixo, quero testar com todas e variar e ver o que o algoritmo considera mais
features_selected = df[['danceability','energy','valence','tempo']]

# %%

# Normalização é feita para atribuir importância igual entre as features, de forma que não influencie no algoritmo, então a conversão é feita para os valores de 0 a 1
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features_selected)

# %%

# Treinamento de modelo
# Trabalhar com várias hipóteses de número de clusters através de experimentação
kmeans = KMeans(n_clusters=5)
kmeans.fit(scaled_features)
# %%
#rotulando cluster de cada música
df['cluster'] = kmeans.labels_
# %%
df.head(5)
# %%
# Predizendo playlists
# A ideia é: dada uma playlist, quais músicas eu posso gostar?

def predict_tracks_by_playlist(playlist_id, model, scaler):
    new_playlist = get_audio_features_by_playlist(playlist_id)
    new_features = new_playlist[['danceability','energy','valence','tempo']]
    scaled_new_features = scaler.transform(new_features)
    predict = model.predict(scaled_new_features)

    new_playlist['cluster'] = predict
    return new_playlist


# %%
# Testando predict

nova_playlist = '3hrXi2n3e8PcA3rK6emPa6'
predicted_tracks_df = predict_tracks_by_playlist(nova_playlist, kmeans, scaler)
predicted_tracks_df.head(10)
# %%
