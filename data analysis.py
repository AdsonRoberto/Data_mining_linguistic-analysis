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

