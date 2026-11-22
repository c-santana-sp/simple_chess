"""CLI interativo — loop principal do jogo com input por texto.

Jogabilidade (notação algébrica):
- "e4" — peão avança para e4
- "Cf3" / "Nf3" — Cavalo para f3
- "Bc4" — Bispo para c4
- "Qh5" / "Dh5" — Rainha para h5
- "Rh1" / "Th1" — Torre para h1
- "Ke2" — Rei para e2
- "exd5" — peão em e captura em d5
- "Cxf3" — Cavalo captura em f3
- "e2-e4" — notação longa (origem-destino)
- "e2 e4" — notação longa com espaço
- Digite 'sair' ou 'q' para encerrar.

O tabuleiro fica fixo na tela (estilo htop) graças ao rich.Live.
O input é capturado caractere por caractere com termios + select,
então o texto digitado é visível na linha de comando.
"""

import fcntl
import os
import select
import sys
import termios
import time

from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.game import Game
from simple_chess.position import Position

from chess_view.rich_view import RichView


def parse_algebraic(notation: str) -> Position | None:
    """Converte notação algébrica (ex: 'e2') para Position.

    'a1' -> Position(7, 0)
    'h8' -> Position(0, 7)
    """
    notation = notation.strip().lower()
    if len(notation) != 2:
        return None

    col_char, row_char = notation
    if col_char not in "abcdefgh" or row_char not in "12345678":
        return None

    col = ord(col_char) - ord("a")
    row = 8 - int(row_char)
    return Position(row, col)


def create_game() -> Game:
    """Cria um jogo novo com tabuleiro configurado."""
    board = Board()
    board.setup_initial_position()
    return Game(board, [Color.WHITE, Color.BLACK])


def _setup_raw_mode() -> tuple[int, list]:
    """Configura o terminal em modo raw para leitura caractere por caractere.

    Returns:
        Tuple (file descriptor, old terminal settings).
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    # Desativar ICANON (cooked mode) e ECHO
    new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, new)
    # Set non-blocking
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    return fd, old


def _restore_terminal(fd: int, old_settings: list) -> None:
    """Restaura o terminal ao estado original."""
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)


def _read_key_nonblocking(fd: int) -> str | None:
    """Tenta ler uma tecla sem bloquear usando select + sys.stdin.read.

    Args:
        fd: File descriptor do stdin em modo raw.

    Returns:
        Caractere lido ou None se nenhuma tecla disponível.
    """
    try:
        ready, _, _ = select.select([fd], [], [], 0)
        if ready:
            data = os.read(fd, 64).decode("utf-8", errors="replace")
            if data:
                return data
    except (OSError, ValueError, UnicodeDecodeError):
        pass
    return None


def main() -> None:
    """Loop principal do jogo.

    Usa rich.Live para display fixo e termios + select para input
    caractere por caractere, exibindo o texto digitado na tela.
    """
    from rich.live import Live
    from rich.console import Console

    game = create_game()
    view = RichView()
    console = Console()

    # Estado do loop
    selected: Position | None = None
    valid_moves: list[Position] | None = None

    # Configurar terminal em modo raw
    fd, old_settings = _setup_raw_mode()

    # Iniciar Live display
    live = Live(
        view.get_renderable(game),
        console=console,
        refresh_per_second=10,
        screen=True,
        transient=False,
    )
    live.start()

    try:
        while True:
            # Tentar ler tecla sem bloquear
            key = _read_key_nonblocking(fd)

            if key is not None:
                cmd, should_execute = view.handle_key(key)

                if should_execute and cmd:
                    raw = cmd.lower()

                    if raw in ("sair", "q", "quit", "exit"):
                        break

                    parts = raw.split()

                    # Tentar notação algébrica primeiro (e4, Cf3, exd5, e2-e4)
                    if len(parts) == 1:
                        success = game.make_move_from_notation(parts[0])
                        if success:
                            selected = None
                            valid_moves = None
                            view.render(game, selected, valid_moves, "")
                            continue

                        # Se falhou, tenta como seleção de origem
                        origin = parse_algebraic(parts[0])
                        if origin is None:
                            view.render(
                                game, None, None,
                                "Jogada não entendida. Use 'e4', 'Cf3', 'e2-e4'.",
                            )
                            continue

                        piece = game.board.piece_at(origin)
                        if piece is None:
                            view.render(game, origin, None, "Nao ha peeca nesta posicao.")
                            continue

                        if piece.color != game.player_turn:
                            turn_name = "Brancas" if game.player_turn == Color.WHITE else "Pretas"
                            view.render(
                                game, origin, None,
                                f"Peça não é sua. Vez das {turn_name}.",
                            )
                            continue

                        # Peça válida — mostrar jogadas possiveis
                        selected = origin
                        valid_moves = piece.valid_moves(origin, game.board)
                        view.render(game, selected, valid_moves, "")
                        continue

                    # Notacao com espaco: "e2 e4"
                    if len(parts) == 2:
                        origin = parse_algebraic(parts[0])
                        end = parse_algebraic(parts[1])

                        if origin is None or end is None:
                            view.render(game, None, None, "Posicao invalida.")
                            continue

                        success = game.make_move(origin, end, raw)
                        if success:
                            selected = None
                            valid_moves = None
                            view.render(game, selected, valid_moves, "")
                        else:
                            view.render(game, None, None, "Jogada invalida.")
                        continue

                    # Input com mais de 2 partes
                    view.render(
                        game, None, None,
                        "Uso: 'e4', 'Cf3', 'e2-e4' ou 'e2 e4'",
                    )
                    continue

            # Atualizar display a cada iteracao
            live.update(view.get_renderable(game))
            time.sleep(0.05)

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        live.stop()
        try:
            _restore_terminal(fd, old_settings)
        except (termios.error, OSError):
            pass  # Terminal já restaurado pelo rich.Live


if __name__ == "__main__":
    main()
