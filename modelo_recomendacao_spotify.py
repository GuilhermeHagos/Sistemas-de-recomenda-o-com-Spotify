# %%
# Ideia: após treinar com musicas que eu ouço, mostrar playlist aleatória e pedir pra ele criar uma playlist com as musicas que mais se assemelham com que eu ouço
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import pandas as pd
import seaborn as sns
import matplotlib as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import silhouette_score
from wordcloud import WordCloud
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
    scope = 'user-library-read playlist-modify-private playlist-modify-public'
), requests_timeout=10)


# %%

#Transportando musicas de 'musicas curtidas' para uma playlist publica, de forma a conseguir uma variedade maior das músicas que ouço

def get_liked_songs(sp):
    '''
    Através de autenticator, retorna lista com as musicas dentro de playlist privada 'Musicas curtidas'
    '''
    liked_songs = []
    offset = 0
    limit = 50
    total_tracks = 1
    
    while offset < total_tracks:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        total_tracks = results['total']  # Número total de músicas curtidas
        for item in results['items']:
            track = item['track']
            liked_songs.append(track['id'])  # Armazena o ID da música
        offset += limit  # Atualiza o offset para buscar a próxima página

    return liked_songs

liked_songs = get_liked_songs(sp)

# %%

def add_100_songs_to_playlist(sp,playlist_id,songs_list):
    for i in range(0, len(songs_list),100):
        sp.playlist_add_items(playlist_id=playlist['id'], items=songs_list[i:i + 100])
# %%

playlist_name =' Minhas Musicas curtidas'
playlist_description = 'Playlist criada para projetos pessoais'

#Criando playlist
playlist = sp.user_playlist_create(user = sp.me()['id'], name = playlist_name, public=False, description=playlist_description)

#Adicionando Liked songs em playlist criada

add_100_songs_to_playlist(sp,playlist_id= playlist['id'],songs_list=liked_songs)


print(f"Playlist '{playlist_name}' criada!")

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
        features = sp.audio_features(track_id)[0]
        if features:
            selected_features = {
                #'danceability': features['danceability'],
                'energy': features['energy'],
                #'valence' : features['valence'],
                'tempo' : features['tempo'],
                #'speechiness' : features['speechiness'],
                #'acousticness' : features['acousticness'],
                'instrumentalness' : features['instrumentalness'],
                #'liveness' : features['liveness'],
                'track_name' : item['track']['name'],
                'artist_name': item['track']['artists'][0]['name']
            
            }
            audio_features.append(selected_features)

    return pd.DataFrame(audio_features)
# %%
minha_playlist_id = '63hN35EdANktwTTx6JsqhM'
df = get_audio_features_by_playlist(minha_playlist_id)
df.head(10)

# %%
numeric_columns = df.select_dtypes(include=['float64','int64']).columns
corr = df[numeric_columns].corr()
sns.heatmap(corr, annot=True, cmap="coolwarm")
plt.show()

# %%
train_df, test_df = train_test_split(df,test_size=0.2, random_state=42)

# %%
numeric_columns = train_df.select_dtypes(include=['float64','int64']).columns
x_train = train_df[numeric_columns]
x_test = test_df[numeric_columns]
# %%
## Teste inicial com modelo de ml kmeans
#features selecionadas abaixo, quero testar com todas e variar e ver o que o algoritmo considera mais
features_selected = df[['danceability','energy','valence','tempo']]

# %%

# Normalização é feita para atribuir importância igual entre as features, de forma que não influencie no algoritmo, então a conversão é feita para os valores de 0 a 1
scaler = StandardScaler()
scaled_x_train = scaler.fit_transform(x_train)
scaled_x_test = scaler.transform(x_test)

# %%

# Treinamento de modelo
# Trabalhar com várias hipóteses de número de clusters através de experimentação
kmeans = KMeans(n_clusters=4, random_state=42)
kmeans.fit(scaled_x_train)
# %%
#teste
test_labels = kmeans.predict(scaled_x_test)
# %%
silhouette_avg = silhouette_score(scaled_x_test, test_labels)
print(f"silhouett Score: {silhouette_avg:.2f}")

#%%
test_df['cluster'] = test_labels
print(test_df[['track_name','cluster']].head(10))
# %%

# Predizendo playlists
# A ideia é: dada uma playlist, quais músicas eu posso gostar?

def predict_tracks_by_playlist(playlist_id, model, scaler):
    new_playlist = get_audio_features_by_playlist(playlist_id)
    new_features = new_playlist[['energy','tempo', 'instrumentalness']]
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

#Criando Nuvem de palavras para observar divisões nos clusters e musicas em cada um

df_filtered = test_df[['track_name','cluster']]
df_filtered.head()

# %%
grouped_df = df_filtered.groupby('cluster')['track_name'].apply(lambda x: ' '.join(x)).reset_index()
grouped_df
# %%
#cria nuvem de palavras
def create_wordcloud(text, title):
    # Gerar a nuvem de palavras
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    
    # Mostrar a nuvem de palavras
    plt.figure(figsize=(8, 5))  # Não deve causar erro se plt for o matplotlib.pyplot
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.title(title, fontsize=20)
    plt.axis("off")
    plt.show()
# %%
grouped_df.apply(lambda row: create_wordcloud(row['track_name'], f'Cluster {row["cluster"]}'), axis=1)
# %%
