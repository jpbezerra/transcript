# transcript

Ferramenta de linha de comando em Python que baixa a transcrição de um vídeo do YouTube e gera um resumo automático dela usando um agente de IA (Gemini, via o framework [Agno](https://github.com/agno-agi/agno)).

## Sumário

- [Visão geral](#visão-geral)
- [Como funciona](#como-funciona)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Detalhes de implementação](#detalhes-de-implementação)
- [Limitações conhecidas](#limitações-conhecidas)
- [Possíveis melhorias](#possíveis-melhorias)

## Visão geral

O usuário informa a URL de um vídeo do YouTube em um loop interativo de terminal; a aplicação:

1. Extrai o ID do vídeo a partir da URL (via `yt-dlp`).
2. Busca a transcrição do vídeo (oficial ou gerada automaticamente), com preferência por português, usando `youtube-transcript-api`.
3. Envia o texto da transcrição para um agente de IA (Google Gemini, orquestrado pelo Agno), que gera um resumo conciso e informativo.
4. Imprime o resumo no terminal.

O loop se repete até o usuário digitar `sair`.

## Como funciona

```
Usuário informa URL
        │
        ▼
Transcriptor.extract_video_id()      → extrai o ID do vídeo com yt-dlp
        │
        ▼
Transcriptor.get_youtube_transcript() → busca transcrição (pt / pt-BR / en)
        │                                via youtube_transcript_api
        ▼
TranscriptSummarizer.summarize()      → envia o texto para o agente Gemini (Agno)
        │                                e retorna o resumo gerado
        ▼
Resumo impresso no terminal
```

## Estrutura do projeto

```
transcript/
├── app/
│   ├── main.py          # Loop interativo de CLI: orquestra transcrição + resumo
│   ├── transcriptor.py  # Classe Transcriptor: extração de ID e obtenção da transcrição
│   └── agent.py         # Classe TranscriptSummarizer: agente de IA para resumir texto
├── pyproject.toml       # Metadados e dependências do projeto (gerenciado com uv)
├── uv.lock              # Lockfile de dependências (uv)
├── .python-version      # Versão do Python fixada para o projeto
└── README.md
```

## Requisitos

- **Python >= 3.12** (definido em `pyproject.toml` e `.python-version`).
- Gerenciador de pacotes [**uv**](https://docs.astral.sh/uv/) (recomendado, já que o projeto usa `uv.lock`) — ou `pip`, alternativamente.
- Uma **chave de API do Google Gemini** (o agente usa `Gemini(id="gemini-2.5-flash")` por padrão).
- Opcionalmente, uma **chave de API da Groq**, já que o código inclui uma configuração alternativa (comentada) para usar `Groq(id="llama-3.3-70b-versatile")` em vez do Gemini.

### Dependências (`pyproject.toml`)

| Pacote                    | Finalidade                                              |
|---------------------------|----------------------------------------------------------|
| `agno`                    | Framework de orquestração do agente de IA                |
| `google-genai`             | Cliente da API do Google Gemini, usado pelo Agno         |
| `groq`                    | Cliente da API da Groq (modelo alternativo, atualmente não usado por padrão) |
| `dotenv`                  | Carregamento de variáveis de ambiente a partir de `.env` |
| `youtube-transcript-api`  | Obtenção das transcrições (legendas) do YouTube          |
| `yt-dlp`                  | Extração de metadados do vídeo (incluindo o ID)          |

## Instalação

Com `uv` (recomendado):

```bash
git clone git@github.com:jpbezerra/transcript.git
cd transcript
uv sync
```

Ou com `pip`, em um ambiente virtual:

```bash
git clone git@github.com:jpbezerra/transcript.git
cd transcript
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install agno google-genai groq dotenv youtube-transcript-api yt-dlp
```

## Configuração

O agente carrega variáveis de ambiente com `python-dotenv` (`load_dotenv()` em `app/agent.py`). Crie um arquivo `.env` na raiz do projeto com a chave de API necessária para o provedor de modelo utilizado, por exemplo:

```bash
# Necessário para o modelo padrão (Gemini)
GOOGLE_API_KEY=sua_chave_aqui

# Necessário apenas se alternar para o modelo Groq (ver "Detalhes de implementação")
GROQ_API_KEY=sua_chave_aqui
```

> O `.env` já está listado no `.gitignore` do projeto e não deve ser commitado.

## Uso

Execute o script principal a partir da pasta `app/`:

```bash
cd app
python main.py
```

Ou, com `uv`:

```bash
uv run app/main.py
```

O programa entra em um loop interativo:

```
Digite a URL do vídeo do YouTube (ou 'sair' para encerrar): https://www.youtube.com/watch?v=XXXXXXXXXXX
<resumo gerado pelo agente é impresso aqui>
Digite a URL do vídeo do YouTube (ou 'sair' para encerrar): sair
```

Se o vídeo não tiver uma URL válida ou não possuir transcrição disponível, uma mensagem de erro é exibida e o loop continua, pedindo uma nova URL.

## Detalhes de implementação

### `Transcriptor` (`app/transcriptor.py`)

- `extract_video_id()`: usa `yt_dlp.YoutubeDL().extract_info(url, download=False)` para obter metadados do vídeo sem baixá-lo, retornando o campo `id`.
- `get_youtube_transcript(video_id, langs=None)`: busca a transcrição do vídeo com fallback em cascata:
  1. Tenta `api.fetch(video_id, languages=["pt", "pt-BR", "en"])` (idiomas configuráveis via parâmetro `langs`).
  2. Se nenhuma transcrição for encontrada nesses idiomas, lista todas as transcrições disponíveis (`api.list(video_id)`) e tenta encontrar uma **gerada automaticamente** (`find_generated_transcript`) em cada idioma da lista de preferência.
  3. Se ainda assim não encontrar, itera por **todas** as transcrições disponíveis do vídeo, retornando a primeira que tiver texto.
  4. Trata explicitamente os casos de `TranscriptsDisabled` (transcrições desabilitadas no vídeo) e `NoTranscriptFound`, além de erros genéricos, sempre retornando uma mensagem amigável em vez de lançar exceção para o chamador.

### `TranscriptSummarizer` (`app/agent.py`)

- Encapsula um `agno.agent.Agent` configurado com o modelo `Gemini(id="gemini-2.5-flash")` e uma instrução de sistema em português orientando o agente a produzir resumos detalhados e informativos.
- Há uma linha comentada mostrando como trocar para `Groq(id="llama-3.3-70b-versatile")`, permitindo alternar o provedor do modelo apenas descomentando/comentando as linhas correspondentes.
- `summarize(text)`:
  - Retorna string vazia se o texto de entrada for vazio ou só espaços em branco.
  - Monta um prompt em português pedindo um resumo conciso do texto.
  - Chama `self.client.run(prompt)` e extrai `run.content`.
  - Em caso de erro (ex.: falha de API, resposta vazia), aplica um **fallback simples**: retorna as três primeiras frases do texto original, separadas por `.`.
- `create_agent()`: função de fábrica que apenas instancia e retorna um `TranscriptSummarizer`.

### `main.py`

Loop de CLI simples: lê a URL do usuário, instancia `Transcriptor(url)`, extrai o `video_id`, busca a transcrição, gera o resumo via `TranscriptSummarizer` e imprime o resultado. Trata os casos de ID inválido e transcrição indisponível continuando o loop em vez de encerrar o programa.

## Limitações conhecidas

- **`README.md` original vazio** — este arquivo substitui o README anterior, que não tinha conteúdo.
- **Sem tratamento de exceções no `main.py`** para falhas na criação do agente ou erros inesperados de rede/API — qualquer exceção não capturada internamente pelas classes encerraria o programa.
- **Sem testes automatizados** no repositório.
- **Dependência de `yt-dlp` só para extrair o ID do vídeo** — uma alternativa mais leve seria fazer o parsing da URL diretamente (regex), sem precisar de uma chamada de rede via `yt-dlp` apenas para obter o ID.
- **Chave de API obrigatória**: sem uma `GOOGLE_API_KEY` válida no `.env`, o resumo cai no fallback (primeiras frases da transcrição) em vez de sinalizar claramente que a geração via IA falhou.
- O parâmetro `langs` de `get_youtube_transcript` é aceito mas `main.py` sempre usa o padrão (`pt`, `pt-BR`, `en`), não expondo a opção de idioma ao usuário final.

## Possíveis melhorias

- Adicionar um modo não interativo (ex.: `python main.py <url>`) para uso em scripts/automação.
- Persistir a transcrição e o resumo em arquivo (Markdown/JSON) além de imprimir no terminal.
- Expor a escolha do modelo (Gemini/Groq) e do idioma da transcrição via variáveis de ambiente ou argumentos de linha de comando.
- Adicionar testes unitários para `Transcriptor` (com mocks de `yt_dlp` e `youtube_transcript_api`) e para o fallback de `TranscriptSummarizer.summarize`.

---

Dependências principais: [Agno](https://github.com/agno-agi/agno) · [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) · [yt-dlp](https://github.com/yt-dlp/yt-dlp) · [Google Gemini API](https://ai.google.dev/)
