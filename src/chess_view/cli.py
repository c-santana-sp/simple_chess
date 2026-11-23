"""CLI interativo — loop principal do jogo com input por texto.

Jogabilidade (notação algébrica padrão internacional PGN):
- "e4" — peão avança para e4
- "Nf3" — Cavalo para f3
- "Bc4" — Bispo para c4
- "Qh5" — Rainha para h5
- "Rh1" — Torre para h1
- "Ke2" — Rei para e2
- "exd5" — peão em e captura em d5
- "Nxf3" — Cavalo captura em f3
- "O-O" — roque curto
- "O-O-O" — roque longo
- "e8=Q" — promoção de peão
- "?e2" — visualizar jogadas válidas da peça em e2 (não vai para o histórico)
- "help" ou "h" — exibir painel de ajuda (pressione 'q' para voltar)
- Digite 'sair' para encerrar.

O tabuleiro fica fixo na tela (estilo htop) graças ao rich.Live.
O input é capturado caractere por caractere com termios + select,
então o texto digitado é visível na linha de comando.
"""

import fcntl
import os
import select
import signal
import sys
import termios
import time

from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.game import Game
from simple_chess.position import Position

from chess_view.rich_view import RichView


# Flag global para detectar quando o terminal volta do background
_terminal_resumed = True


def _sigcont_handler(signum: int, frame) -> None:
    """Handler para SIGCONT — quando o processo volta do background.

    O terminal pode estar em estado inconsistente após ser suspenso.
    """
    global _terminal_resumed
    _terminal_resumed = True


def _sigwinch_handler(signum: int, frame) -> None:
    """Handler para SIGWINCH — quando o terminal é redimensionado.

    O rich.Live precisa ser notificado para ajustar o layout.
    """
    pass  # O rich.Live já trata redimensionamento internamente


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
    # Manter ISIG para que Ctrl+C gere SIGINT e o jogo possa ser encerrado
    new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
    # Desativar IEXTEN para evitar comportamento estranho com teclas especiais
    new[3] = new[3] & ~termios.IEXTEN
    termios.tcsetattr(fd, termios.TCSANOW, new)
    # Set non-blocking
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    return fd, old


def _restore_terminal(fd: int, old_settings: list) -> None:
    """Restaura o terminal ao estado original."""
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except termios.error:
        pass  # Terminal já foi restaurado
    try:
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
    except (OSError, IOError):
        pass  # FD já fechado


def _reset_terminal_state(fd: int) -> None:
    """Reseta o estado do terminal para evitar travamento quando perde foco.

    O rich.Live com screen=True pode deixar o terminal em estado inconsistente
    quando a janela perde foco. Esta função tenta restaurar o estado.
    """
    try:
        # Limpar buffer de input
        termios.tcflush(fd, termios.TCIFLUSH)
    except termios.error:
        pass


def _read_key_nonblocking(fd: int) -> str | None:
    """Tenta ler uma tecla sem bloquear usando select + os.read.

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
    except (OSError, ValueError, UnicodeDecodeError, select.error):
        # select.error pode ocorrer quando o terminal perde foco
        # ou entra em estado inconsistente
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

    # Iniciar Live display — sem screen=True para evitar conflito com termios
    # O screen=True usa alternate screen buffer que conflita com o raw mode
    # quando o terminal perde foco (GNOME Terminal, etc.)
    live = Live(
        view.get_renderable(game),
        console=console,
        refresh_per_second=10,
        screen=False,
        transient=False,
    )
    live.start()

    # Contador para detectar terminal travado (sem input por muito tempo)
    stuck_counter = 0
    MAX_STUCK_ITERATIONS = 500  # ~50 segundos sem input → resetar terminal

    # Registrar handlers de sinal para evitar travamento
    old_sigcont = signal.signal(signal.SIGCONT, _sigcont_handler)
    old_sigwinch = signal.signal(signal.SIGWINCH, _sigwinch_handler)

    # Flag para sair do loop principal
    should_exit = False

    try:
        while not should_exit:
            # Detectar terminal travado e tentar recuperar
            if stuck_counter > MAX_STUCK_ITERATIONS:
                _reset_terminal_state(fd)
                stuck_counter = 0

            # Tentar ler tecla sem bloquear
            key = _read_key_nonblocking(fd)

            if key is not None:
                # Resetar contador de terminal travado quando há input
                stuck_counter = 0
                # Processar cada caractere individualmente
                # os.read() pode retornar múltiplos caracteres de uma vez
                for ch in key:
                    cmd, should_execute = view.handle_key(ch)

                    if not should_execute:
                        continue

                    if not cmd:
                        continue

                    raw = cmd.lower()

                    if raw in ("sair", "quit", "exit"):
                        should_exit = True
                        break

                    # Comando de ajuda: "help" ou "h" — ativa o painel de ajuda
                    if raw in ("help", "h"):
                        view._help_mode = True
                        view._current_input = ""
                        break  # sair do for, continuar o while

                    parts = raw.split()

                    # Comando de ajuda: "?e2" — visualizar jogadas válidas
                    if len(parts) == 1 and parts[0].startswith("?"):
                        house = parts[0][1:]  # remover o "?"
                        origin = parse_algebraic(house)
                        if origin is None:
                            view.render(
                                game, None, None,
                                f"'{house}' não é uma posição válida. Use '?e2'.",
                            )
                            break

                        piece = game.board.piece_at(origin)
                        if piece is None:
                            view.render(game, origin, None, "Não há peça nesta posição.")
                            break

                        if piece.color != game.player_turn:
                            turn_name = "Brancas" if game.player_turn == Color.WHITE else "Pretas"
                            view.render(
                                game, origin, None,
                                f"Peça não é sua. Vez das {turn_name}.",
                            )
                            break

                        # Mostrar movimentos válidos — não vai para o histórico
                        valid = piece.valid_moves(origin, game.board)
                        view.render(game, origin, valid, "")
                        break

                    # Notação PGN padrão: "e4", "Nf3", "exd5", "O-O", "e8=Q"
                    if len(parts) == 1:
                        notation = parts[0]
                        success = game.make_move_from_notation(notation)
                        if success:
                            selected = None
                            valid_moves = None

                            # Verificar se o jogo terminou
                            if game.is_game_over():
                                result = game.game_result()
                                view.render(game, selected, valid_moves, result or "")
                                # Aguardar brevemente para o jogador ver o resultado
                                time.sleep(1.5)
                                should_exit = True
                                break

                            view.render(game, selected, valid_moves, "")
                            break

                        # Movimento rejeitado — dar feedback inteligente
                        if game.board.is_check(game.player_turn):
                            view.render(
                                game, None, None,
                                "Rei em xeque! Saia do xeque. Use '+' no final: Qxf7+",
                            )
                        else:
                            # Tentar detectar o erro comum
                            msg = _get_helpful_error(notation, game)
                            view.render(game, None, None, msg)
                        break

                    # Input com mais de 1 parte (sem o "?")
                    view.render(
                        game, None, None,
                        "Uso: 'e4', 'Nf3', 'exd5', 'O-O', '?e2', 'help'.",
                    )
                    break

            # Incrementar contador de iterações sem input
            stuck_counter += 1

            # Atualizar display a cada iteracao
            try:
                live.update(view.get_renderable(game))
            except Exception:
                # Ignorar erros de renderização (ex: terminal redimensionado,
                # suspenso, ou em estado inconsistente) para não crashar o jogo
                pass

            # Reduzir frequência de atualização para economizar CPU
            # e evitar conflitos com rich.Live.refresh()
            time.sleep(0.1)

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        # Restaurar handlers de sinal
        try:
            signal.signal(signal.SIGCONT, old_sigcont)
            signal.signal(signal.SIGWINCH, old_sigwinch)
        except (OSError, ValueError):
            pass

        try:
            live.stop()
        except Exception:
            pass  # Live pode já estar parado
        try:
            _restore_terminal(fd, old_settings)
        except (termios.error, OSError):
            pass  # Terminal já restaurado pelo rich.Live


if __name__ == "__main__":
    main()


def _get_helpful_error(notation: str, game: "Game") -> str:
    """Gera uma mensagem de erro útil baseada na notação digitada.

    Detecta erros comuns:
    - Esqueceu o 'x' na captura
    - Esqueceu o '+' no xeque
    - Desambiguação necessária
    - Notação inválida
    """
    from simple_chess.move_parser import parse_move_notation, _find_moving_piece, PIECE_LETTER_MAP, parse_position
    from simple_chess.position import Position
    from simple_chess.color import Color

    notation_lower = notation.lower()

    # Tentar parsear para ver se o movimento em si é válido
    result = parse_move_notation(notation_lower, game)
    if result is None:
        # Notação não reconhecida — verificar erros comuns

        # Verificar se é notação de peça sem desambiguação
        # Ex: "Nf3" quando dois cavalos podem ir para f3
        import re
        piece_match = re.match(r"^([kqrnb])([a-h][1-8])$", notation_lower)
        if piece_match:
            piece_letter = piece_match.group(1)
            target_str = piece_match.group(2)
            target = parse_position(target_str)
            if target is not None:
                piece_class_name = PIECE_LETTER_MAP.get(piece_letter)
                if piece_class_name is not None:
                    # Contar quantas peças podem ir para o destino
                    candidates = []
                    for row in range(8):
                        for col in range(8):
                            pos = Position(row, col)
                            piece = game.board.piece_at(pos)
                            if piece is None or piece.color != game.player_turn:
                                continue
                            if type(piece).__name__ != piece_class_name:
                                continue
                            moves = piece.valid_moves(pos, game.board)
                            if moves is not None and target in moves:
                                candidates.append(pos)
                    if len(candidates) > 1:
                        # Múltiplos candidatos — desambiguação necessária
                        cols = [chr(ord("a") + c.col) for c in candidates]
                        if len(set(cols)) == len(cols):
                            # Colunas diferentes — usar coluna
                            hints = [f"{piece_letter.upper()}{cols[i]}{target_str}" for i in range(len(candidates))]
                            return f"Desambiguação! Use: {', '.join(hints)}"
                        else:
                            # Mesma coluna — usar fileira
                            ranks = [str(8 - c.row) for c in candidates]
                            hints = [f"{piece_letter.upper()}{ranks[i]}{target_str}" for i in range(len(candidates))]
                            return f"Desambiguação! Use: {', '.join(hints)}"

                # Verificar se é captura sem 'x'
                piece_at_target = game.board.piece_at(target)
                if piece_at_target is not None:
                    return f"Captura! Use 'x': {piece_letter.upper()}x{target_str}"

        # Verificar se é notação de peça com captura sem desambiguação
        piece_capture_match = re.match(r"^([kqrnb])x([a-h][1-8])$", notation_lower)
        if piece_capture_match:
            piece_letter = piece_capture_match.group(1)
            target_str = piece_capture_match.group(2)
            target = parse_position(target_str)
            if target is not None:
                piece_class_name = PIECE_LETTER_MAP.get(piece_letter)
                if piece_class_name is not None:
                    candidates = []
                    for row in range(8):
                        for col in range(8):
                            pos = Position(row, col)
                            piece = game.board.piece_at(pos)
                            if piece is None or piece.color != game.player_turn:
                                continue
                            if type(piece).__name__ != piece_class_name:
                                continue
                            moves = piece.valid_moves(pos, game.board)
                            if moves is not None and target in moves:
                                candidates.append(pos)
                    if len(candidates) > 1:
                        cols = [chr(ord("a") + c.col) for c in candidates]
                        if len(set(cols)) == len(cols):
                            hints = [f"{piece_letter.upper()}{cols[i]}x{target_str}" for i in range(len(candidates))]
                            return f"Desambiguação! Use: {', '.join(hints)}"
                        else:
                            ranks = [str(8 - c.row) for c in candidates]
                            hints = [f"{piece_letter.upper()}{ranks[i]}x{target_str}" for i in range(len(candidates))]
                            return f"Desambiguação! Use: {', '.join(hints)}"

        # Verificar se é notação de peão
        pawn_match = re.match(r"^([a-h])([1-8])$", notation_lower)
        if pawn_match:
            target_str = pawn_match.group(0)
            target = parse_position(target_str)
            if target is not None:
                piece = game.board.piece_at(target)
                if piece is not None:
                    return f"Captura! Use 'x': {notation_lower[0]}x{notation_lower[1:]}"

        return f"'{notation}' não é uma jogada válida. Consulte a notação abaixo."

    # Parse funcionou — verificar se é problema de sufixo
    origin, end, user_suffix = result

    # Simular o movimento para ver se dá xeque
    enemy_color = Color.BLACK if game.player_turn == Color.WHITE else Color.WHITE

    original_grid = game.board.grid
    game.board.grid = [row[:] for row in original_grid]
    piece = game.board.piece_at(origin)
    game.board.place(origin, None)
    game.board.place(end, piece)
    gives_check = game.board.is_check(enemy_color)
    game.board.grid = original_grid

    if gives_check and user_suffix not in ("+", "#"):
        clean_notation = notation[0].upper() + notation[1:] if notation else notation
        return f"Xeque! Adicione '+' no final: {clean_notation}+"

    return f"'{notation}' não é uma jogada válida. Consulte a notação abaixo."
