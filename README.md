
# ♔ Simple Chess

Engine de xadrez em Python com interface visual interativa no terminal.

O tabuleiro fica fixo na tela (estilo `htop`), sem rolagem, com peças Unicode coloridas, histórico de jogadas e destaque das casas válidas.

---

## Requisitos

| Requisito | Versão | Onde baixar |
|---|---|---|
| **Python** | 3.13+ | [python.org](https://www.python.org/downloads/) |
| **uv** | última versão | [Documentação oficial](https://docs.astral.sh/uv/getting-started/installation/) |

> **Nota:** O `uv` também pode instalar o Python automaticamente para você. Se não tiver Python instalado, basta instalar o `uv` e rodar `uv python install 3.13`.

---

## Instalando o uv

Se você ainda não tem o `uv` instalado, siga as instruções para seu sistema operacional. Para mais detalhes, consulte a [documentação oficial de instalação](https://docs.astral.sh/uv/getting-started/installation/).

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Após instalar, reabra o PowerShell para que o `uv` fique disponível no PATH.

**Alternativas no Windows:**

- **WinGet:** `winget install --id=astral-sh.uv`
- **Scoop:** `scoop install uv`
- **pip:** `pip install uv`

### Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Após instalar, reabra o terminal ou rode `source ~/.bashrc` (ou `source ~/.zshrc`) para que o `uv` fique disponível.

**Alternativas no Linux:**

- **pip:** `pip install uv`
- **Cargo (Rust):** `cargo install uv`

### macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Alternativas no macOS:**

- **Homebrew:** `brew install uv`
- **MacPorts:** `sudo port install uv`
- **pip:** `pip install uv`

---

### Verificar instalação

```bash
uv --version
```

Se exibir a versão, está pronto para continuar.

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/c-santana-sp/simple_chess.git
cd simple_chess
```

### 2. Instale as dependências

O `uv` cria automaticamente um ambiente virtual e instala tudo:

```bash
uv sync
```

Isso instala a única dependência externa: **Rich** (biblioteca de formatação de terminal).

> **Sem uv?** Use `pip install rich` após criar um venv manualmente (`python -m venv .venv && source .venv/bin/activate` no Linux/macOS ou `.venv\Scripts\activate` no Windows).

---

## Como rodar

```bash
uv run chess_view
```

O jogo abre diretamente no terminal, com o tabuleiro visível e aguardando seu primeiro comando.

> **Sem uv?** Ative o venv e rode `python -m chess_view.cli`.

---

## Jogabilidade

### Notação algébrica padrão internacional (PGN)

O jogo usa exclusivamente a notação oficial usada em torneios de xadrez. As letras das peças são em inglês:

| Peça | Letra | Exemplo |
|---|---|---|
| King (Rei) | `K` | `Ke2` |
| Queen (Rainha) | `Q` | `Qh5` |
| Rook (Torre) | `R` | `Rh1` |
| Bishop (Bispo) | `B` | `Bc4` |
| Knight (Cavalo) | `N` | `Nf3` |
| Peão | (sem letra) | `e4` |

| Formato | Exemplo | Descrição |
|---|---|---|
| **Movimento de peão** | `e4`, `d5`, `c4` | Peão avança para a casa indicada |
| **Movimento de peça** | `Nf3`, `Bc4`, `Qh5` | Letra da peça + destino |
| **Captura** | `exd5`, `Nxf3` | Origem + `x` + destino (**obrigatório**) |
| **Xeque** | `Qxf7+`, `e4+` | Movimento que dá xeque (**sufixo obrigatório**) |
| **Xeque-mate** | `Qxf7#` | Movimento que dá xeque-mate (**sufixo obrigatório**) |
| **Roque curto** | `O-O` | Rei para o lado da torre kingside |
| **Roque longo** | `O-O-O` | Rei para o lado da torre queenside |
| **Promoção** | `e8=Q` | Peão promove para Rainha |
| **Ver jogadas** | `?e2` | Destaca as jogadas válidas da peça em e2 |

> **Importante:** O jogo exige a notação PGN completa. Para capturar, use `exd5` (não `e4`). Para xeque, use `e4+`. Para xeque-mate, use `e4#`. Um painel de referência aparece no rodapé do terminal para consulta rápida.

> **Dica de aprendizado:** Jogar com notação PGN é uma ótima forma de se familiarizar com a linguagem universal do xadrez. À medida que você joga, começa a ler e pensar em termos de `e4`, `Nf3`, `Bc4` — exatamente como partidas reais são anotadas e discutidas.

### Destaque visual

- **Azul opaco** (`·`) — casa vazia onde a peça pode se mover.
- **Vermelho opaco** (`·`) — casa com peça inimiga que pode ser capturada.
- **Dourado** (`★`) — casa da peça selecionada.

### Comandos

| Comando | Ação |
|---|---|
| `sair` / `q` | Encerra o jogo |
| `?e2` | Visualiza jogadas válidas da peça em e2 (não vai para o histórico) |
| `Escape` | Limpa o texto digitado |
| `Backspace` | Apaga o último caractere |

---

## Configuração visual

Edite `config.json` na raiz do projeto para personalizar a aparência:

| Configuração | Descrição | Exemplo |
|---|---|---|
| `invert_board_on_black_turn` | Inverte o tabuleiro quando é vez das pretas | `true` / `false` |
| `board.light_square_color` | Cor das casas claras | `"#3b5e3b"` |
| `board.dark_square_color` | Cor das casas escuras | `"#2d4a2d"` |
| `board.cell_width` | Largura de cada célula | `4` |
| `board.piece_bold` | Peças em negrito | `true` / `false` |
| `markers.selected` | Símbolo da casa selecionada | `"★"` |
| `markers.valid_move` | Símbolo das jogadas válidas | `"·"` |
| `title.text` | Título do painel | `"♔ Xadrez"` |
| `piece_symbols.*` | Símbolos Unicode das peças | `"♚"`, `"♔"`, etc. |

Todas as opções têm valor padrão — o arquivo `config.json` precisa conter apenas o que deseja alterar.

---

## Estrutura do projeto

```
simple_chess/
├── config.json          # Configuração visual (opcional)
├── pyproject.toml       # Dependências e entry point
└── src/
    ├── simple_chess/    # Engine pura — zero dependência de UI
    │   ├── board.py
    │   ├── game.py
    │   ├── color.py
    │   ├── position.py
    │   ├── move_parser.py
    │   └── pieces/
    └── chess_view/      # Visualização e CLI (desacoplado)
        ├── cli.py
        ├── renderer.py  # Protocolo/ABC de renderização
        ├── rich_view.py # Implementação com Rich
        └── defaults.py  # Configurações padrão
```

- **`simple_chess`** — Engine pura: Board, Game, Piece, Color, Position, MoveParser.
- **`chess_view`** — Visualização e CLI: tabuleiro fixo, input caractere a caractere, sidebar com histórico.

---

## Extensibilidade

Para adicionar uma nova visualização (ex: Pygame, terminal puro), basta criar uma classe implementando `chess_view.renderer.Renderer` e trocá-la no CLI — a engine não precisa mudar.

---

## Créditos

- **Engine do jogo** (`simple_chess/`) — desenvolvida manualmente, incluindo lógica de tabuleiro, peças, turnos e parser de notação algébrica.
- **Interface visual** (`chess_view/`) — desenvolvida com auxílio de IA (Junie, pela JetBrains), incluindo renderização com Rich, layout do terminal, input interativo e configurações visuais.

---

> **Nota:** Todas as peças básicas têm lógica de movimento implementada (Pawn, Knight, King, Bishop, Rook, Queen). A validação de xeque também funciona — movimentos que deixam o rei em xeque são rejeitados. Movimentos especiais (roque completo, promoção, en passant) e detecção de fim de jogo (xeque-mate, stalemate) estão pendentes.