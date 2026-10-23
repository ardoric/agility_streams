# Agility PT Streams

Site com o índice dos vídeos e ficheiros das provas de agility.

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
