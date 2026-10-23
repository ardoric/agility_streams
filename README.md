# Agility PT Streams

Site com o índice dos vídeos e ficheiros das provas de agility.

O índice é uma página autónoma com tema verde, pesquisa por nome, data, grau ou
clube e navegação por época e dia. A pesquisa ignora maiúsculas e acentos, abre
as pastas com resultados e repõe a navegação anterior quando é limpa.
A época mais recente e os seus dois dias mais recentes ficam abertos por
predefinição. Os links dos ficheiros usam a base `/videos/` do site.
O aspeto e o comportamento da página são definidos em `generate_index.py`.

Os links MP4 abrem um reprodutor numa janela modal, com controlos de reprodução,
um botão para fechar (ou a tecla Escape) e ações para descarregar ou abrir o
ficheiro diretamente. Cada MP4 tem também um botão de descarga separado na
listagem. Sem JavaScript, o link continua a abrir o vídeo diretamente.
A descarga usa o atributo HTML `download`, destinado a ficheiros no mesmo
domínio, como os servidos em `/videos/`.

## Atualizar o índice

Com a unidade `Z:\` acessível, execute:

```powershell
python .\generate_index.py
```

O script procura pastas de épocas com o formato `AAAA-AA`, ordena épocas, dias,
pastas e ficheiros do mais recente para o mais antigo e substitui
`index.html` de forma segura.

Para usar outros caminhos:

```powershell
python .\generate_index.py --source "Z:\" --output ".\index.html"
```

Para apenas verificar se o índice está atualizado:

```powershell
python .\generate_index.py --check
```
