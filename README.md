
# Simple Chess

Engine de xadrez em Python com interface visual no terminal.

## Estrutura do projeto

- **`simple_chess`** — Engine pura (Board, Game, Piece, Color, Position). Zero dependência de visualização.
- **`chess_view`** — Pacote de visualização e CLI, totalmente desacoplado da engine.

## Como rodar

### Pré-requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)

### Iniciar o jogo

```bash
uv run chess_view
```

### Jogabilidade

Suporta vários formatos de notação:

- **Notação curta** (recomendado): `e4`, `d5`, `c4` — peão avança para a casa
- **Notação de peças**: `Cf3` / `Nf3` (Cavalo), `Bc4` (Bispo), `Qh5` / `Dh5` (Rainha/Dama), `Rh1` / `Th1` (Torre), `Ke2` (Rei)
- **Capturas**: `exd5`, `Cxf3`
- **Notação longa**: `e2-e4`, `g1-f3`
- **Notação completa**: `e2e4`
- **Selecionar peça**: digite apenas a origem (`e2`) para ver as jogadas válidas destacadas
- Digite `sair` ou `q` para encerrar

O tabuleiro fica fixo na tela (estilo `htop`), sem rolagem, e seu texto digitado aparece no painel.

> **Nota:** Apenas o peão (Pawn) tem lógica de movimento implementada no momento. As outras peças estão como desafio para implementar.

## Extensibilidade

Para adicionar uma nova visualização (ex: Pygame), basta criar uma classe implementando `chess_view.renderer.Renderer` e trocá-la no CLI — a engine não precisa mudar.