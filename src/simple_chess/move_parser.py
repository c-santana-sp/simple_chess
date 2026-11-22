"""Parser de notação algébrica para movimentos de xadrez.

Suporta:
- Notação curta de peão: "e4", "d5" (peão avança para a casa indicada)
- Notação curta de peças: "Cf3", "Nf3" (Cavalo para f3), "Bc4" (Bispo para c4),
  "Qh5" (Rainha para h5), "Rh1" (Torre para h1), "Ke2" (Rei para e2)
- Capturas: "exd5", "Cxf3", "Nxe5"
- Notação longa: "e2-e4", "g1-f3"
- Notação completa: "e2e4", "g1f3"

A letra da peça é opcional para peões. Para outras peças:
- K/Rei = King
- Q/D = Queen (D de Dama em português)
- R/T = Rook (T de Torre em português)
- B/B = Bishop (B de Bispo)
- N/C = Knight (C de Cavalo em português, N do inglês)
"""

import re
from typing import TYPE_CHECKING

from simple_chess.color import Color
from simple_chess.pieces.piece import Piece
from simple_chess.position import Position

if TYPE_CHECKING:
    from simple_chess.board import Board
    from simple_chess.game import Game


# Mapeamento de letras de peça (inglês + português)
PIECE_LETTER_MAP: dict[str, str] = {
    # King
    "k": "King", "K": "King",
    # Queen (D = Dama em português)
    "q": "Queen", "Q": "Queen", "d": "Queen", "D": "Queen",
    # Rook (T = Torre em português)
    "r": "Rook", "R": "Rook", "t": "Rook", "T": "Rook",
    # Bishop
    "b": "Bishop", "B": "Bishop",
    # Knight (C = Cavalo em português, N = Knight em inglês)
    "n": "Knight", "N": "Knight", "c": "Knight", "C": "Knight",
}


def parse_position(notation: str) -> Position | None:
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


def _find_piece_at(
    board: "Board",
    pos: Position,
    piece_class_name: str,
    color: Color,
) -> Position | None:
    """Encontra a peça do tipo especificado na posição dada.

    Args:
        board: Tabuleiro atual.
        pos: Posição de destino.
        piece_class_name: Nome da classe da peça (ex: "Knight").
        color: Cor da peça que está jogando.

    Returns:
        Position da peça de origem ou None.
    """
    piece = board.piece_at(pos)
    if piece is not None:
        return pos
    return None


def _find_moving_piece(
    board: "Board",
    target_pos: Position,
    piece_class_name: str | None,
    color: Color,
) -> Position | None:
    """Encontra qual peça deve se mover para target_pos.

    Busca todas as peças do jogador atual que podem chegar a target_pos
    e retorna a posição da primeira que encontra.

    Args:
        board: Tabuleiro atual.
        target_pos: Posição de destino.
        piece_class_name: Nome da classe da peça (ex: "Knight").
            Se None, busca peões.
        color: Cor da peça que está jogando.

    Returns:
        Position da peça de origem ou None.
    """
    for row in range(8):
        for col in range(8):
            pos = Position(row, col)
            piece = board.piece_at(pos)
            if piece is None:
                continue
            if piece.color != color:
                continue

            # Se especificou tipo de peça, verificar
            if piece_class_name is not None:
                if type(piece).__name__ != piece_class_name:
                    continue
            else:
                # Notação de peão — só aceitar peões
                from simple_chess.pieces.pawn import Pawn
                if not isinstance(piece, Pawn):
                    continue

            # Verificar se esta peça pode chegar ao destino
            moves = piece.valid_moves(pos, board)
            if moves is not None and target_pos in moves:
                return pos

    return None


def parse_move_notation(
    notation: str,
    game: "Game",
) -> tuple[Position, Position] | None:
    """Parseia uma notação de movimento e retorna (origem, destino).

    Suporta:
    - "e4" -> peão avança para e4
    - "Cf3" / "Nf3" -> Cavalo para f3
    - "Bc4" -> Bispo para c4
    - "Qh5" / "Dh5" -> Rainha para h5
    - "Rh1" / "Th1" -> Torre para h1
    - "Ke2" -> Rei para e2
    - "exd5" -> peão em e captura em d5
    - "Cxf3" / "Nxf3" -> Cavalo captura em f3
    - "e2-e4" -> notação longa
    - "e2e4" -> notação completa

    Args:
        notation: String com a notação do movimento.
        game: Jogo atual para contexto (turno, tabuleiro).

    Returns:
        Tuple (origem, destino) ou None se não conseguir parsear.
    """
    notation = notation.strip().lower()
    if not notation:
        return None

    board = game.board
    color = game.player_turn

    # Notação longa: "e2-e4"
    long_match = re.match(r"^([a-h][1-8])\-([a-h][1-8])$", notation)
    if long_match:
        origin = parse_position(long_match.group(1))
        end = parse_position(long_match.group(2))
        if origin and end:
            return (origin, end)
        return None

    # Notação completa: "e2e4"
    full_match = re.match(r"^([a-h][1-8])([a-h][1-8])$", notation)
    if full_match:
        origin = parse_position(full_match.group(1))
        end = parse_position(full_match.group(2))
        if origin and end:
            return (origin, end)
        return None

    # Notação com captura: "exd5" ou "Cxf3"
    capture_match = re.match(r"^([a-h])x([a-h][1-8])$", notation)
    if capture_match:
        origin_file = capture_match.group(1)
        target = parse_position(capture_match.group(2))
        if target is None:
            return None

        # É peão (só letra de coluna)
        # Encontrar peão na coluna indicada que pode capturar no destino
        for row in range(8):
            pos = Position(row, ord(origin_file) - ord("a"))
            piece = board.piece_at(pos)
            if piece is None:
                continue
            if piece.color != color:
                continue
            from simple_chess.pieces.pawn import Pawn
            if not isinstance(piece, Pawn):
                continue
            moves = piece.valid_moves(pos, board)
            if target in moves:
                return (pos, target)
        return None

    # Notação de peça com captura: "Cxf3" / "Nxf3"
    piece_capture_match = re.match(r"^([a-z])x([a-h][1-8])$", notation)
    if piece_capture_match:
        piece_letter = piece_capture_match.group(1)
        target = parse_position(piece_capture_match.group(2))
        if target is None:
            return None

        piece_class_name = PIECE_LETTER_MAP.get(piece_letter)
        if piece_class_name is None:
            return None

        origin = _find_moving_piece(board, target, piece_class_name, color)
        if origin:
            return (origin, target)
        return None

    # Notação curta de peça: "Cf3" / "Nf3"
    piece_short_match = re.match(r"^([a-z])([a-h][1-8])$", notation)
    if piece_short_match:
        piece_letter = piece_short_match.group(1)
        target = parse_position(piece_short_match.group(2))
        if target is None:
            return None

        piece_class_name = PIECE_LETTER_MAP.get(piece_letter)
        if piece_class_name is None:
            return None

        origin = _find_moving_piece(board, target, piece_class_name, color)
        if origin:
            return (origin, target)
        return None

    # Notação curta de peão: "e4"
    pawn_short_match = re.match(r"^([a-h])([1-8])$", notation)
    if pawn_short_match:
        target = parse_position(pawn_short_match.group(0))
        if target is None:
            return None

        origin = _find_moving_piece(board, target, None, color)
        if origin:
            return (origin, target)
        return None

    return None
