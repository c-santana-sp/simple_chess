"""Implementação Rich — tabuleiro fixo no terminal (estilo htop)."""

import json
import pathlib

from simple_chess.color import Color
from simple_chess.game import Game
from simple_chess.pieces.piece import Piece
from simple_chess.position import Position

from chess_view.defaults import DEFAULT_CONFIG, _build_piece_symbols, _deep_copy, _deep_merge
from chess_view.renderer import Renderer

# Caminho do arquivo de configuração, relativo ao projeto root
_CONFIG_PATH = pathlib.Path(__file__).resolve().parents[2] / "config.json"


def _load_config() -> dict:
    """Carrega as configurações do arquivo config.json.

    Retorna as configurações padrão se o arquivo não existir ou estiver inválido.
    """
    try:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            # Mesclar recursivamente com defaults
            config = _deep_merge(DEFAULT_CONFIG, user_config)
            return config
    except (json.JSONDecodeError, OSError):
        pass
    return _deep_copy(DEFAULT_CONFIG)


class RichView(Renderer):
    """Renderiza o jogo usando Rich com display fixo no terminal.

    Usa `rich.Live` para manter o tabuleiro travado na tela,
    sem rolagem — comportamento similar ao htop/vim.

    O input é capturado caractere por caractere com `termios` + `select`,
    exibindo o texto digitado na linha de comando estilo vim.

    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │  ♔ Xadrez  |  Vez das: Brancas                         │
    ├──────────────────┬──────────────────────────────────────┤
    │                  │  Capturadas:                         │
    │   Tabuleiro 8x8  │                                      │
    │                  │  Histórico:                          │
    │                  │  1. e4  e5                          │
    │                  │  2. d4  d5                          │
    ├──────────────────┴──────────────────────────────────────┤
    │  : Brancas, digite sua jogada:                         │
    └─────────────────────────────────────────────────────────┘
    """

    def __init__(self, config: dict | None = None):
        """Inicializa a visualização Rich.

        Args:
            config: Dicionário de configurações. Se None, carrega do config.json.
        """
        self._config = config if config is not None else _load_config()
        self._piece_symbols = _build_piece_symbols(self._config)
        self._current_input = ""
        self._status_message = ""
        self._selected: Position | None = None
        self._valid_moves: list[Position] | None = None

    # --- Properties de configuração ---

    @property
    def invert_board_on_black_turn(self) -> bool:
        """Se True, inverte o tabuleiro quando é a vez das pretas."""
        return self._config.get("invert_board_on_black_turn", True)

    @property
    def cell_width(self) -> int:
        """Largura em caracteres de cada célula do tabuleiro."""
        return self._config.get("board", {}).get("cell_width", 4)

    @property
    def cell_height(self) -> int:
        """Altura em linhas de cada célula do tabuleiro (1 = normal, 2 = dobro)."""
        return self._config.get("board", {}).get("cell_height", 2)

    @property
    def light_square_color(self) -> str:
        return self._config.get("board", {}).get("light_square_color", "#3b5e3b")

    @property
    def dark_square_color(self) -> str:
        return self._config.get("board", {}).get("dark_square_color", "#2d4a2d")

    @property
    def selected_square_color(self) -> str:
        return self._config.get("board", {}).get("selected_square_color", "#b8860b")

    @property
    def selected_text_color(self) -> str:
        return self._config.get("board", {}).get("selected_text_color", "black")

    @property
    def valid_move_color(self) -> str:
        """Cor de fundo para casas vazias onde a peça pode se mover (azul opaco)."""
        return self._config.get("board", {}).get("valid_move_color", "#2a4a6b")

    @property
    def valid_capture_color(self) -> str:
        """Cor de fundo para casas com peças inimigas que podem ser capturadas (vermelho opaco)."""
        return self._config.get("board", {}).get("valid_capture_color", "#6b2a2a")

    @property
    def piece_text_color(self) -> str:
        return self._config.get("board", {}).get("piece_text_color", "white")

    @property
    def piece_bold(self) -> bool:
        return self._config.get("board", {}).get("piece_bold", True)

    @property
    def selected_marker(self) -> str:
        return self._config.get("markers", {}).get("selected", "★")

    @property
    def valid_move_marker(self) -> str:
        return self._config.get("markers", {}).get("valid_move", "·")

    @property
    def captured_title_color(self) -> str:
        return self._config.get("captured", {}).get("title_color", "yellow")

    @property
    def prompt_color(self) -> str:
        return self._config.get("command_line", {}).get("prompt_color", "dim white")

    @property
    def input_color(self) -> str:
        return self._config.get("command_line", {}).get("input_color", "cyan")

    @property
    def cursor_char(self) -> str:
        return self._config.get("command_line", {}).get("cursor", "█")

    @property
    def title_text(self) -> str:
        return self._config.get("title", {}).get("text", "♔ Xadrez")

    @property
    def title_style(self) -> str:
        return self._config.get("title", {}).get("style", "bold")

    def _piece_symbol(self, piece: Piece | None) -> str:
        if piece is None:
            return " "
        key = (type(piece).__name__, piece.color)
        return self._piece_symbols.get(key, "?")

    def _build_table(
        self,
        game: Game,
        selected: Position | None = None,
        valid_moves: list[Position] | None = None,
    ) -> "Table":
        """Constrói a tabela do tabuleiro 8x8.

        Inverte a visualização quando é a vez das pretas,
        mostrando o tabuleiro do ponto de vista do jogador atual.

        Cada célula ocupa `cell_height` linhas, com a peça centralizada
        verticalmente, para que as casas fiquem mais quadradas.
        """
        from rich.table import Table
        from rich.text import Text as RichText

        cell_w = self.cell_width
        cell_h = self.cell_height
        valid_set = set(valid_moves) if valid_moves else set()
        table = Table(show_header=False, show_edge=False, box=None, padding=(0, 0))

        for _col in range(8):
            table.add_column(width=cell_w, justify="center")

        # Inverter o tabuleiro quando é a vez das pretas (configurável)
        is_black_turn = game.player_turn == Color.BLACK
        should_invert = self.invert_board_on_black_turn and is_black_turn
        row_order = range(7, -1, -1) if should_invert else range(8)
        col_order = range(7, -1, -1) if should_invert else range(8)

        selected_marker = self.selected_marker
        valid_marker = self.valid_move_marker
        light_color = self.light_square_color
        dark_color = self.dark_square_color
        selected_bg = self.selected_square_color
        selected_fg = self.selected_text_color
        valid_move_bg = self.valid_move_color
        valid_capture_bg = self.valid_capture_color
        piece_color = self.piece_text_color
        bold_prefix = "bold " if self.piece_bold else ""

        for row in row_order:
            cells: list[RichText] = []
            for col in col_order:
                pos = Position(row, col)
                piece = game.board.piece_at(pos)
                symbol = self._piece_symbol(piece)

                is_selected = selected == pos
                is_valid = pos in valid_set
                is_light = (row + col) % 2 == 0

                has_piece = symbol.strip()

                # Determinar estilo e texto da célula
                if is_selected:
                    piece_line = f" {selected_marker}{symbol} " if has_piece else f" {selected_marker}  "
                    style = f"{bold_prefix}{selected_fg} on {selected_bg}"
                elif is_valid and has_piece:
                    # Casa com peça inimiga — captura (vermelho opaco)
                    piece_line = f" {symbol}{valid_marker} "
                    style = f"{bold_prefix}{piece_color} on {valid_capture_bg}"
                elif is_valid and not has_piece:
                    # Casa vazia — movimento (azul opaco)
                    piece_line = f"  {valid_marker}  "
                    style = f"{bold_prefix}{piece_color} on {valid_move_bg}"
                else:
                    bg = light_color if is_light else dark_color
                    piece_line = f" {symbol} " if has_piece else "    "
                    style = f"{bold_prefix}{piece_color} on {bg}"

                # Se cell_height > 1, centralizar a peça verticalmente
                if cell_h > 1:
                    # Calcular onde colocar a peça (centralizada verticalmente)
                    empty_line = " " * len(piece_line)
                    lines_above = (cell_h - 1) // 2
                    lines_below = cell_h - 1 - lines_above

                    full_text = RichText(style=style)
                    for _ in range(lines_above):
                        full_text.append(empty_line)
                        full_text.append("\n")
                    full_text.append(piece_line)
                    for _ in range(lines_below):
                        full_text.append("\n")
                        full_text.append(empty_line)
                    cells.append(full_text)
                else:
                    cells.append(RichText(piece_line, style=style))

            row_label = 8 - row
            table.add_row(f"[bold]  {row_label} [/]", *cells)

        # Labels das colunas invertidos quando o tabuleiro está invertido
        col_labels_row = [" [bold]  [/]"]
        col_labels = "hgfedcba" if should_invert else "abcdefgh"
        for label in col_labels:
            col_labels_row.append(f"[bold] {label}   [/]")
        table.add_row(*col_labels_row)

        return table

    def _build_captured_text(self, game: Game) -> "Text":
        """Constrói o texto das peças capturadas em formato horizontal.

        Semelhante ao histórico: quando vazio, exibe um texto padrão em dim.
        Quando há peças, exibe os símbolos separados por espaço.

        Returns:
            RichText com as peças capturadas formatadas horizontalmente.
        """
        from rich.text import Text as RichText

        if game.captured_pieces:
            symbols = " ".join(self._piece_symbol(p) for p in game.captured_pieces)
            content = RichText(symbols, style="white")
        else:
            content = RichText("(nenhuma)", style="dim")

        return content

    def _build_captured_bar(self, game: Game) -> "Panel":
        """Constrói o painel de peças capturadas.

        Returns:
            Panel com as peças capturadas em formato horizontal.
        """
        from rich.panel import Panel
        from rich.text import Text as RichText

        captured_text = self._build_captured_text(game)
        title = RichText("Capturadas", style=f"bold {self.captured_title_color}")
        return Panel(
            captured_text,
            title=title,
            border_style="dim",
            padding=(0, 1),
            expand=True,
        )

    def _build_history_bar(self, game: Game) -> "Panel":
        """Constrói o painel de histórico de jogadas.

        Escreve na horizontal e quebra linha ao atingir a largura do terminal.
        Mantém no máximo 3 linhas, com "..." se truncado.

        Returns:
            Panel com as jogadas em fluxo horizontal.
        """
        from rich.panel import Panel
        from rich.text import Text as RichText

        moves = game.move_history
        if not moves:
            history_text = RichText("(sem jogadas)", style="dim")
        else:
            # Construir tokens: "1.e4", "e5", "2.d4", "d5", ...
            tokens: list[str] = []
            for i in range(0, len(moves), 2):
                move_num = i // 2 + 1
                white_move = moves[i]
                black_move = moves[i + 1] if i + 1 < len(moves) else ""
                tokens.append(f"{move_num}.{white_move}")
                if black_move:
                    tokens.append(black_move)

            # Limitar tokens para no máximo 3 linhas
            max_lines = 3
            chars_per_line = 116  # largura do terminal menos bordas
            tokens_per_line = chars_per_line // 6  # ~6 chars por token
            max_tokens = max_lines * tokens_per_line

            if len(tokens) > max_tokens:
                tokens = tokens[-max_tokens:]

            history_text = RichText()
            if len(tokens) > max_tokens:
                history_text.append("... ", style="dim")
            for idx, token in enumerate(tokens):
                if idx > 0 or (len(tokens) > max_tokens):
                    history_text.append(" ")
                history_text.append(token, style="dim white")

        history_title = RichText("Histórico", style="bold blue")
        return Panel(
            history_text,
            title=history_title,
            border_style="dim",
            padding=(0, 1),
            expand=True,
        )

    def _build_command_line(self, game: Game) -> "Text":
        """Constrói a linha de comando estilo vim."""
        from rich.text import Text

        turn_color = game.player_turn
        turn_text = "Brancas" if turn_color == Color.WHITE else "Pretas"

        cmd = Text()
        cmd.append(": ", style=f"bold {self.prompt_color}")

        if self._current_input:
            # Texto digitado com cor configurável
            cmd.append(self._current_input, style=f"bold {self.input_color}")
            # Cursor piscante (simulado)
            cmd.append(self.cursor_char, style=f"bold {self.input_color} blink")
        else:
            cmd.append(f"{turn_text}, digite sua jogada:", style=f"bold {self.prompt_color}")

        return cmd

    def _build_full_layout(
        self,
        game: Game,
        selected: Position | None = None,
        valid_moves: list[Position] | None = None,
        status_message: str = "",
    ) -> "Group":
        from rich.console import Group
        from rich.panel import Panel
        from rich.text import Text

        # Tabuleiro — centralizado sem borda
        from rich.align import Align
        board_table = self._build_table(game, selected, valid_moves)
        centered_board = Align(board_table, align="center")

        # Turno info
        turn_color = game.player_turn
        turn_text = "Brancas" if turn_color == Color.WHITE else "Pretas"
        title = Text(f"  {self.title_text}  |  Vez das: {turn_text}", style=self.title_style, justify="center")

        # Painéis separados: capturadas + histórico (empilhados verticalmente)
        captured_bar = self._build_captured_bar(game)
        history_bar = self._build_history_bar(game)
        info_row = Group(captured_bar, history_bar)

        # Status line
        if status_message:
            status_text = Text(
                f"  {status_message}  ", style="bold red", justify="center"
            )
        else:
            status_text = Text(
                "  Notação: e4, Cf3, Nf3, e2-e4  |  'sair' para encerrar  ",
                style="dim",
                justify="center",
            )

        # Command line
        cmd_line = self._build_command_line(game)

        # Rodapé: status + command line
        bottom_section = Panel(
            Group(status_text, cmd_line),
            border_style="dim",
            padding=(0, 1),
            expand=True,
        )

        # Linha vazia como margem entre tabuleiro e painéis
        gap = Text("")
        return Group(title, centered_board, gap, info_row, bottom_section)

    def render(
        self,
        game: Game,
        selected: Position | None = None,
        valid_moves: list[Position] | None = None,
        status_message: str = "",
    ) -> None:
        """Atualiza o estado interno para renderização.

        Args:
            game: Estado atual do jogo.
            selected: Casa selecionada pelo jogador.
            valid_moves: Jogadas válidas para a peça selecionada.
            status_message: Mensagem de status a exibir.
        """
        self._selected = selected
        self._valid_moves = valid_moves
        self._status_message = status_message

    def get_renderable(self, game: Game):
        """Retorna o renderable atualizado para o Live display."""
        return self._build_full_layout(
            game,
            self._selected,
            self._valid_moves,
            self._status_message,
        )

    def handle_key(self, key: str) -> tuple[str, bool]:
        """Processa uma tecla digitada e atualiza o input buffer.

        Args:
            key: Caractere lido pelo termios + select.

        Returns:
            Tuple (input_completo, should_execute).
            should_execute é True quando Enter foi pressionado.
        """
        if key == "\n" or key == "\r":
            # Enter — executar comando
            cmd = self._current_input
            self._current_input = ""
            return cmd, True
        elif key == "\x7f" or key == "\b":
            # Backspace
            self._current_input = self._current_input[:-1]
            return "", False
        elif key in ("\x1b",):
            # Escape — limpar input
            self._current_input = ""
            return "", False
        elif key.isprintable() or key == " ":
            # Caractere normal
            self._current_input += key
            return "", False
        else:
            # Ignorar teclas especiais
            return "", False

    @property
    def current_input(self) -> str:
        return self._current_input

    @property
    def status_message(self) -> str:
        return self._status_message

    @status_message.setter
    def status_message(self, value: str):
        self._status_message = value
