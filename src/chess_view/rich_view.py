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
    def sidebar_width(self) -> int:
        return self._config.get("sidebar", {}).get("width", 20)

    @property
    def sidebar_border_style(self) -> str:
        return self._config.get("sidebar", {}).get("border_style", "dim")

    @property
    def captured_title_color(self) -> str:
        return self._config.get("sidebar", {}).get("captured_title_color", "yellow")

    @property
    def history_title_color(self) -> str:
        return self._config.get("sidebar", {}).get("history_title_color", "cyan")

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
        """
        from rich.table import Table
        from rich.text import Text as RichText

        cell_w = self.cell_width
        valid_set = set(valid_moves) if valid_moves else set()
        table = Table(show_header=False, show_edge=False, padding=(0, 1))

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

                if is_selected:
                    display_text = f" {selected_marker}{symbol} " if has_piece else f" {selected_marker}  "
                    style = f"{bold_prefix}{selected_fg} on {selected_bg}"
                elif is_valid and has_piece:
                    # Casa com peça inimiga — captura (vermelho opaco)
                    display_text = f" {symbol}{valid_marker} "
                    style = f"{bold_prefix}{piece_color} on {valid_capture_bg}"
                elif is_valid and not has_piece:
                    # Casa vazia — movimento (azul opaco)
                    display_text = f"  {valid_marker}  "
                    style = f"{bold_prefix}{piece_color} on {valid_move_bg}"
                else:
                    bg = light_color if is_light else dark_color
                    display_text = f" {symbol} " if has_piece else "    "
                    style = f"{bold_prefix}{piece_color} on {bg}"

                cells.append(RichText(display_text, style=style))

            row_label = 8 - row
            table.add_row(f"[bold]  {row_label} [/]", *cells)

        # Labels das colunas invertidos quando o tabuleiro está invertido
        col_labels_row = [" [bold]  [/]"]
        col_labels = "hgfedcba" if should_invert else "abcdefgh"
        for label in col_labels:
            col_labels_row.append(f"[bold] {label}   [/]")
        table.add_row(*col_labels_row)

        return table

    def _build_sidebar(self, game: Game) -> "Panel":
        """Constrói o painel lateral com peças capturadas e histórico."""
        from rich.panel import Panel
        from rich.text import Text
        from rich.console import Group

        lines: list[Text] = []

        # --- Peças capturadas ---
        captured_title = Text("Capturadas:", style=f"bold {self.captured_title_color}")
        lines.append(captured_title)

        if game.captured_pieces:
            # Separar por cor
            white_captured = [p for p in game.captured_pieces if p.color == Color.WHITE]
            black_captured = [p for p in game.captured_pieces if p.color == Color.BLACK]

            if white_captured:
                symbols = " ".join(self._piece_symbol(p) for p in white_captured)
                line = Text(f"  Brancas: {symbols}", style="white")
                lines.append(line)
            if black_captured:
                symbols = " ".join(self._piece_symbol(p) for p in black_captured)
                line = Text(f"  Pretas:  {symbols}", style="white")
                lines.append(line)
        else:
            lines.append(Text("  (nenhuma)", style="dim"))

        # Separador
        lines.append(Text(""))

        # --- Histórico de jogadas ---
        history_title = Text("Historico:", style=f"bold {self.history_title_color}")
        lines.append(history_title)

        if game.move_history:
            # Emparelhar jogadas: branca + preta
            moves = game.move_history
            for i in range(0, len(moves), 2):
                move_num = i // 2 + 1
                white_move = moves[i]
                black_move = moves[i + 1] if i + 1 < len(moves) else ""
                if black_move:
                    line = Text(
                        f"  {move_num}. {white_move:<6} {black_move}",
                        style="dim white",
                    )
                else:
                    line = Text(
                        f"  {move_num}. {white_move}",
                        style="dim white",
                    )
                lines.append(line)
        else:
            lines.append(Text("  (sem jogadas)", style="dim"))

        content = Group(*lines)
        return Panel(
            content,
            border_style=self.sidebar_border_style,
            padding=(0, 1),
            width=self.sidebar_width,
            expand=False,
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
        """Constrói o layout completo: tabuleiro + sidebar + command line."""
        from rich.console import Group
        from rich.panel import Panel
        from rich.text import Text

        # Tabuleiro — usar a tabela diretamente sem Panel para evitar corte
        board_table = self._build_table(game, selected, valid_moves)

        # Sidebar
        sidebar = self._build_sidebar(game)

        # Montar linha principal: tabuleiro + sidebar
        from rich.columns import Columns
        main_row = Columns(
            [board_table, sidebar],
            equal=False,
        )

        # Turno info
        turn_color = game.player_turn
        turn_text = "Brancas" if turn_color == Color.WHITE else "Pretas"
        title = Text(f"  {self.title_text}  |  Vez das: {turn_text}", style=self.title_style, justify="center")

        # Status line
        if status_message:
            status_text = Text(
                f"  {status_message}  ", style="bold red", justify="center"
            )
        else:
            status_text = Text(
                "  Notacao: e4, Cf3, Nf3, e2-e4  |  'sair' para encerrar  ",
                style="dim",
                justify="center",
            )

        # Command line
        cmd_line = self._build_command_line(game)

        return Group(title, main_row, status_text, cmd_line)

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
