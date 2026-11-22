"""Implementação Rich — tabuleiro fixo no terminal (estilo htop)."""

from simple_chess.color import Color
from simple_chess.game import Game
from simple_chess.pieces.piece import Piece
from simple_chess.position import Position

from chess_view.renderer import Renderer


# Mapeamento de peças para símbolos Unicode
PIECE_SYMBOLS: dict[tuple[str, Color], str] = {
    # Brancas (símbolos preenchidos)
    ("King", Color.WHITE): "♚",
    ("Queen", Color.WHITE): "♛",
    ("Rook", Color.WHITE): "♜",
    ("Bishop", Color.WHITE): "♝",
    ("Knight", Color.WHITE): "♞",
    ("Pawn", Color.WHITE): "♟",
    # Pretas (símbolos não preenchidos)
    ("King", Color.BLACK): "♔",
    ("Queen", Color.BLACK): "♕",
    ("Rook", Color.BLACK): "♖",
    ("Bishop", Color.BLACK): "♗",
    ("Knight", Color.BLACK): "♘",
    ("Pawn", Color.BLACK): "♙",
}


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

    def __init__(self):
        self._current_input = ""
        self._status_message = ""
        self._selected: Position | None = None
        self._valid_moves: list[Position] | None = None

    def _piece_symbol(self, piece: Piece | None) -> str:
        if piece is None:
            return " "
        key = (type(piece).__name__, piece.color)
        return PIECE_SYMBOLS.get(key, "?")

    def _build_table(
        self,
        game: Game,
        selected: Position | None = None,
        valid_moves: list[Position] | None = None,
    ) -> "Table":
        """Constrói a tabela do tabuleiro 8x8."""
        from rich.table import Table
        from rich.text import Text as RichText

        CELL_W = 4
        valid_set = set(valid_moves) if valid_moves else set()
        table = Table(show_header=False, show_edge=False, padding=(0, 1))

        for _col in range(8):
            table.add_column(width=CELL_W, justify="center")

        for row in range(8):
            cells: list[RichText] = []
            for col in range(8):
                pos = Position(row, col)
                piece = game.board.piece_at(pos)
                symbol = self._piece_symbol(piece)

                is_selected = selected == pos
                is_valid = pos in valid_set
                is_light = (row + col) % 2 == 0

                has_piece = symbol.strip()

                if is_selected:
                    display_text = f" ★{symbol} " if has_piece else " ★  "
                    style = "bold black on #b8860b"
                elif is_valid and has_piece:
                    display_text = f" {symbol}· "
                    style = "bold white on #3a7d44"
                elif is_valid and not has_piece:
                    display_text = "  ·  "
                    style = "bold white on #3a7d44"
                else:
                    display_text = f" {symbol} " if has_piece else "    "
                    style = "bold white on #3b5e3b" if is_light else "bold white on #2d4a2d"

                cells.append(RichText(display_text, style=style))

            row_label = 8 - row
            table.add_row(f"[bold]  {row_label} [/]", *cells)

        col_labels_row = [" [bold]  [/]"]
        for label in "abcdefgh":
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
        captured_title = Text("Capturadas:", style="bold yellow")
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
        history_title = Text("Historico:", style="bold cyan")
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
            border_style="dim",
            padding=(0, 1),
            width=20,
            expand=False,
        )

    def _build_command_line(self, game: Game) -> "Text":
        """Constrói a linha de comando estilo vim."""
        from rich.text import Text

        turn_color = game.player_turn
        turn_text = "Brancas" if turn_color == Color.WHITE else "Pretas"

        cmd = Text()
        cmd.append(": ", style="bold dim white")

        if self._current_input:
            # Texto digitado em cyan
            cmd.append(self._current_input, style="bold cyan")
            # Cursor piscante (simulado com underscore)
            cmd.append("█", style="bold cyan blink")
        else:
            cmd.append(f"{turn_text}, digite sua jogada:", style="bold dim white")

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
        title = Text(f"  ♔ Xadrez  |  Vez das: {turn_text}", style="bold", justify="center")

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
