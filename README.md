
# ♔ Simple Chess

Engine de xadrez em Python com interface visual interativa no terminal. Todas as regras oficiais do xadrez estão implementadas.

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

## Regras implementadas

O jogo implementa **todas as regras oficiais do xadrez**:

### Movimentos das peças

| Peça | Movimento |
|---|---|
| **Peão** | Avança 1 casa (2 casas no primeiro movimento), captura na diagonal |
| **Cavalo** | 8 movimentos em "L" (2 casas numa direção + 1 na perpendicular) |
| **Bispo** | Desliza nas diagonais até a borda ou uma peça |
| **Torre** | Desliza em linha reta (horizontal/vertical) até a borda ou uma peça |
| **Rainha** | Combina Bispo + Torre: 8 direções (diagonal e ortogonal) |
| **Rei** | 1 casa em qualquer direção |

### Movimentos especiais

| Movimento | Notação | Descrição |
|---|---|---|
| **Roque curto** | `O-O` | Rei move 2 casas para a direita, torre salta para o lado |
| **Roque longo** | `O-O-O` | Rei move 2 casas para a esquerda, torre salta para o lado |
| **Promoção de peão** | `e8=Q`, `exd8=R` | Peão que chega na última fileira é substituído por outra peça |
| **En passant** | `cxd4` | Peão captura ao passar um peão inimigo que avançou 2 casas |

### Validação de xeque

- **Xeque detectado automaticamente** — quando o rei é atacado, a casa fica destacada em vermelho com o marcador `!`.
- **Movimentos ilegais rejeitados** — o jogo não permite movimentos que deixam o próprio rei em xeque.
- **Xeque forçado** — quando o rei está em xeque, só são aceitos movimentos que saem do xeque.

### Condições de fim de jogo

| Condição | Descrição |
|---|---|
| **Xeque-mate** | Rei em xeque sem movimentos legais → vitória do oponente |
| **Stalemate** | Rei não em xeque sem movimentos legais → empate |
| **Material insuficiente** | Rei vs Rei, Rei+Bispo vs Rei, Rei+Cavalo vs Rei → empate |
| **Repetição de posição (3x)** | A mesma posição ocorre 3 vezes → empate |
| **Regra dos 50 movimentos** | 50 movimentos sem captura ou movimento de peão → empate |

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

### Formatos de notação

| Formato | Exemplo | Descrição |
|---|---|---|
| **Movimento de peão** | `e4`, `d5`, `c4` | Peão avança para a casa indicada |
| **Movimento de peça** | `Nf3`, `Bc4`, `Qh5` | Letra da peça + destino |
| **Captura** | `exd5`, `Nxf3` | Origem + `x` + destino (**obrigatório**) |
| **Xeque** | `Qxf7+`, `e4+` | Movimento que dá xeque (**sufixo obrigatório**) |
| **Xeque-mate** | `Qxf7#` | Movimento que dá xeque-mate (**sufixo obrigatório**) |
| **Roque curto** | `O-O` | Rei para o lado da torre kingside |
| **Roque longo** | `O-O-O` | Rei para o lado da torre queenside |
| **Promoção** | `e8=Q`, `exd8=R` | Peão promove para a peça indicada |
| **Desambiguação** | `Ndf3`, `Nef3`, `R1d3`, `Rcd3` | Quando duas peças iguais podem ir ao mesmo destino |
| **Ver jogadas** | `?e2` | Destaca as jogadas válidas da peça em e2 |

### Desambiguação de peças

Quando duas peças do mesmo tipo podem ir para a mesma casa, a notação exige um identificador extra:

| Situação | Notação | Por quê? |
|---|---|---|
| Dois cavalos podem ir para e5 | `Nce5` ou `Nge5` | Identifica pela coluna de origem |
| Dois cavalos em colunas diferentes | `Nce5` ou `Nge5` | Identifica pela coluna de origem |
| Dois cavalos na mesma coluna | `N1e5` ou `N3e5` | Identifica pela fileira de origem |
| Duas torres podem ir para d3 | `R1d3` ou `R8d3` | Identifica pela fileira de origem |

> **Importante:** O jogo exige a notação PGN completa. Para capturar, use `exd5` (não `e4`). Para xeque, use `e4+`. Para xeque-mate, use `e4#`. Um painel de referência aparece no rodapé do terminal para consulta rápida.

> **Dica de aprendizado:** Jogar com notação PGN é uma ótima forma de se familiarizar com a linguagem universal do xadrez. À medida que você joga, começa a ler e pensar em termos de `e4`, `Nf3`, `Bc4` — exatamente como partidas reais são anotadas e discutidas.

### Destaque visual

- **Azul opaco** (`·`) — casa vazia onde a peça pode se mover.
- **Vermelho opaco** (`·`) — casa com peça inimiga que pode ser capturada.
- **Dourado** (`★`) — casa da peça selecionada.
- **Vermelho escuro** (`!`) — casa do rei em xeque.

### Comandos

| Comando | Ação |
|---|---|
| `sair` / `q` | Encerra o jogo |
| `?e2` | Visualiza jogadas válidas da peça em e2 (não vai para o histórico) |
| `Escape` | Limpa o texto digitado |
| `Backspace` | Apaga o último caractere |

---

## Referência rápida de notação PGN

Um painel com todos os formatos aparece no lado direito do terminal durante o jogo. Aqui está o resumo:

```
┌─────────────────────┐
│  Notação PGN        │
├─────────────────────┤
│  Peças              │
│  K  Rei             │
│  Q  Rainha          │
│  R  Torre           │
│  B  Bispo           │
│  N  Cavalo          │
│                     │
│  Movimentos         │
│  e4   Avanço peão   │
│  Nf3  Movimento     │
│  exd5 Captura       │
│  e4+  Xeque         │
│  e4#  Xeque-mate    │
│                     │
│  Especiais          │
│  O-O   Roque curto  │
│  O-O-O Roque longo  │
│  e8=Q  Promoção     │
│                     │
│  Comandos           │
│  ?e2  Ver jogadas   │
│  sair  Encerrar     │
└─────────────────────┘
```

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
├── src/
│   ├── simple_chess/    # Engine pura — zero dependência de UI
│   │   ├── board.py     # Tabuleiro 8x8, posicionamento, xeque
│   │   ├── game.py      # Turnos, validação, regras, fim de jogo
│   │   ├── color.py     # Enum WHITE/BLACK
│   │   ├── position.py  # Dataclass imutável (row, col)
│   │   ├── move_parser.py  # Parse de notação PGN
│   │   └── pieces/      # Implementação de cada peça
│   └── chess_view/      # Visualização e CLI (desacoplado)
│       ├── cli.py       # Loop interativo, input, feedback
│       ├── renderer.py  # Protocolo/ABC de renderização
│       ├── rich_view.py # Implementação com Rich
│       └── defaults.py  # Configurações padrão
└── tests/               # Testes unitários da engine
    ├── conftest.py      # Fixtures compartilhadas
    ├── test_board.py    # Tabuleiro, xeque, posicionamento
    ├── test_game.py     # Turnos, regras, fim de jogo
    ├── test_pieces.py   # Movimentos de cada peça
    ├── test_move_parser.py  # Parse de notação PGN
    └── test_position_color.py  # Position e Color
```

- **`simple_chess`** — Engine pura: Board, Game, Piece, Color, Position, MoveParser. Zero dependência de UI.
- **`chess_view`** — Visualização e CLI: tabuleiro fixo, input caractere a caractere, sidebar com histórico.
- **`tests`** — Suíte de testes unitários com ~160 testes cobrindo toda a engine.

---

## Testes

A engine possui testes unitários para todas as regras:

```bash
# Rodar todos os testes
uv run pytest tests/

# Rodar com cobertura de código
uv run pytest tests/ --cov=simple_chess
```

Os testes cobrem:

- **Position e Color** — criação, igualdade, hash, corners
- **Board** — grid, bounds, piece_at, move, capture, has_enemy, find_king, is_check
- **Peças** — movimentos de Pawn, Knight, King, Bishop, Rook, Queen; capturas, bloqueios, bordas
- **Game** — turnos, validação de xeque, roque, promoção, en passant, checkmate, stalemate, material insuficiente, regra dos 50 movimentos, repetição 3x, notação PGN, desambiguação
- **MoveParser** — parse de posições, notação de peão, peças, capturas, roque, promoção, sufixos +/#, desambiguação, notação inválida

---

## Extensibilidade

Para adicionar uma nova visualização (ex: Pygame, terminal puro), basta criar uma classe implementando `chess_view.renderer.Renderer` e trocá-la no CLI — a engine não precisa mudar.

---

## Créditos

- **Engine do jogo** (`simple_chess/`) — desenvolvida manualmente, incluindo lógica de tabuleiro, peças, turnos, parser de notação algébrica e todas as regras oficiais do xadrez.
- **Interface visual** (`chess_view/`) — desenvolvida com auxílio de IA (Junie, pela JetBrains), incluindo renderização com Rich, layout do terminal, input interativo e configurações visuais.