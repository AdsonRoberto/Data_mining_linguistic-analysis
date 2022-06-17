import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import re, os  

#matplotlib inline
sns.set(style="whitegrid")

#load all files
files_path = '/content/drive/MyDrive/Mineracao/Logs' 
files_list = os.listdir(files_path)                                              # by ADSON -> O método listdir () do Python retorna uma lista contendo os nomes das entradas no diretório fornecido por path.
dfs = []
for log in files_list:
  print(log)
  file_path = files_path + '/' + log
  df = pd.read_csv(file_path, error_bad_lines=False, sep=',')                   # by ADSON -> Linhas com muitos campos (por exemplo, uma linha csv com muitas vírgulas), por padrão, causam o surgimento de uma exceção e nenhum DataFrame será retornado. Se for False, essas “linhas incorretas” serão eliminadas do DataFrame que é retornado.
  dfs.append(df)
df = pd.concat(dfs)

# ordem cronológica                                                             
df['data_hora_mensagem'] = pd.to_datetime(df['data_hora_mensagem'])             # by ADSON -> Usou-se to_datetime para converter a string do log para um formato timestamp do pandas e assim poder ordenar pelo tempo
df = df.sort_values(by='data_hora_mensagem')

tutores = {355074062, 276365414, 395739605}

#remove tutors
df = df[df.apply(lambda x: x['remetente'] not in tutores, axis = 1)]

df.head(3)


#Atributos de alunos:
#Explicitos:

#Cursos
#Turmas
#Gênero
#Cidade, Estado, País
#Implícitos

#Número de mensagens
#Média/Std de mensagens por dia (nos dias que mandou mensagem)
#Média/Std de intervalo de tempo entre as mensagens (nos dias que mandou mensagem)
#Texto das mensagens

students_set = df[df['autor_da_mensagem']=='STUART']['destinatario'].unique()
print('total de alunos:',len(students_set))

active_students_set = df[df['autor_da_mensagem']!='STUART']['remetente'].unique()
print('total de alunos ativos:',len(active_students_set))

df.columns
explicit_variables=['remetente', 'deficiencia', 'cursos_usuario', 'turmas_usuario', 'genero', 'cidade', 'estado', 'pais']
df_students = pd.DataFrame()
for student in active_students_set:
  student_last_row = df[df['remetente']==student].iloc[-1][explicit_variables].to_frame().transpose()
  df_students = pd.concat([df_students, student_last_row])

df_students.reset_index(drop=True, inplace = True)
df_students.dropna(subset=['cursos_usuario'], inplace = True)
df_students

#Variaveis implcitas

students_messages = []
mean_messages_by_day = []
for student in df_students['remetente']:
  messages = df[df['remetente']==student]
  n_messages = len(messages)
  students_messages.append(n_messages)
  frame = '24H'
  timeseries = messages[messages['autor_da_mensagem']!='STUART'].groupby('data_hora_mensagem').count()['remetente']
  timeseries = timeseries.resample(frame).sum()
  mean_messages_by_day.append(timeseries[timeseries.values!=0].mean())


df_students['messages_para_stuart'] = students_messages
df_students['media_mensagens_por_dia_stuart'] = mean_messages_by_day

#Plotar graficos
print(df_students['messages_para_stuart'].describe())
sns.distplot(df_students['messages_para_stuart'])

print(df_students['media_mensagens_por_dia_stuart'].describe())
sns.distplot(df_students['media_mensagens_por_dia_stuart'])

sns.jointplot(data=df_students, x="messages_para_stuart", y="media_mensagens_por_dia_stuart")

plt.figure(figsize=(20,10))
sns.jointplot(data=df_students[df_students['deficiencia']!='Nenhuma'], x="messages_para_stuart", 
              y="media_mensagens_por_dia_stuart", hue = 'deficiencia', height = 10)

#Reducao de dimensionalidade

courses = df_students['cursos_usuario'].unique()
courses = [set(c.split(', ')) for c in courses]
set_courses = set()
for c in courses:
  set_courses = set_courses.union(c)

courses = list(set_courses)

hot_encoded = np.zeros((len(df_students),len(courses)))
for i, courses_student in enumerate(df_students['cursos_usuario']):
  for j, c in enumerate(courses):
    if c in courses_student:
      hot_encoded[i][j] = 1

df_courses_hot_encoded = pd.DataFrame(data = hot_encoded, columns = courses)
df_courses_hot_encoded.reset_index(drop = True,inplace=True)

df_studentes_hot_encoded = pd.concat([df_students.reset_index(drop = True), df_courses_hot_encoded], axis = 1)
deficiencia_hot_encoded = pd.get_dummies(df_studentes_hot_encoded['deficiencia'])
genero_hot_encoded = pd.get_dummies(df_studentes_hot_encoded['genero'])
df_studentes_hot_encoded = pd.concat([df_studentes_hot_encoded, deficiencia_hot_encoded], axis = 1)
df_studentes_hot_encoded = pd.concat([df_studentes_hot_encoded, genero_hot_encoded], axis = 1)
df_studentes_hot_encoded = df_studentes_hot_encoded[df_studentes_hot_encoded.columns[10:]]
df_studentes_hot_encoded.head()

#reducao de dimensionalidade com pca
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
pca.fit(df_studentes_hot_encoded)
print(pca.explained_variance_ratio_)
X = pca.transform(df_studentes_hot_encoded)

df_pca = pd.DataFrame(data=X, columns = ['x', 'y'])
df_pca['deficiencia'] = df_students.reset_index(drop = True)['deficiencia']
plt.figure(figsize=(40,15))
sns.scatterplot(data = df_pca, x = 'x', y ='y', hue = 'deficiencia', s = 100)

#Análise de rede
#Grafo de alunos: existe uma conexão entre os alunos i e j, se i faz o mesmo curso que j e o peso da conexão é quantidade cursos em comum.
#Grafo de cursos: existe uma conexão entre os cursos i e j se há um aluno que faz os cursos i e j e o peso da conexão é a quantidade de cursos que eles fazem juntos.
#Nós com maior centralidade

!pip install pyvis
from pyvis.network import Network

def create_network(dict_nodes_edges, network_file, display_label = True):

  net = Network(width = '1800px', height = '1000px', notebook = True, directed=False)

  # Create connections between nodes
  nodes_pairs = []
  nodes_inserted = set([])
  for i in dict_nodes_edges:
    for j in dict_nodes_edges:
      if (i,j) in nodes_pairs or i==j:
        continue

      i_edges = dict_nodes_edges[i]
      j_edges = dict_nodes_edges[j]

      if i not in nodes_inserted:
        nodes_inserted.add(i)
        if display_label:
          net.add_node(i, label = i, title = str(i_edges), value = len(i_edges))
        else:
          net.add_node(i, label = '', title = i, value = len(i_edges))        

      if j not in nodes_inserted:
        nodes_inserted.add(j)
        if display_label:
          net.add_node(j, label = j, title = str(j_edges), value = len(j_edges))
        else:
          net.add_node(j, label = '', title = j, value = len(j_edges))      
        
      intersect = i_edges.intersection(j_edges)
      if intersect:
        net.add_edge(i, j)

  net.save_graph(network_file)
  net.show(network_file)

list_of_sets_courses = [set(c.split(', ')) for c in df_students['cursos_usuario']]
user_courses = dict(zip(df['remetente'],list_of_sets_courses))
create_network(user_courses, 'users_network.html')

set_courses = set()
for c in list_of_sets_courses:
  set_courses = set_courses.union(c)

def course_in(course, courses_str):
  courses = set(courses_str.split(', '))
  return course in courses


courses_users = {}
for c in set_courses:
  users = df_students[df_students.apply(lambda x: course_in(c, x['cursos_usuario']), axis = 1)]['remetente'].unique()
  courses_users[c] = set(users)

  create_network(courses_users, 'courses_network.html',True)

