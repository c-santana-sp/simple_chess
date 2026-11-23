"""Parser de notação algébrica padrão internacional (PGN).

Suporta apenas a notação oficial usada em torneios:
- Notação curta de peão: "e4", "d5" (peão avança para a casa indicada)
- Notação curta de peças: "Nf3" (Cavalo para f3), "Bc4" (Bispo para c4),
  "Qh5" (Rainha para h5), "Rh1" (Torre para h1), "Ke2" (Rei para e2)
- Capturas: "exd5" (peão em e captura em d5), "Nxf3" (Cavalo captura em f3)
- Roque: "O-O" (curto), "O-O-O" (longo)
- Promoção: "e8=Q" (peão promove para Rainha)
- Sufixos informativos: "+" (xeque), "#" (xeque-mate)

Letras de peça (padrão internacional):
- K = King (Rei)
- Q = Queen (Rainha)
- R = Rook (Torre)
- B = Bishop (Bispo)
- N = Knight (Cavalo)
"""

import re
from typing import TYPE_CHECKING

from simple_chess.color import Color
from simple_chess.pieces.piece import Piece
from simple_chess.position import Position

if TYPE_CHECKING:
    from simple_chess.board import Board
    from simple_chess.game import Game


# Mapeamento de letras de peça (padrão internacional PGN)
PIECE_LETTER_MAP: dict[str, str] = {
    "K": "King", "k": "King",
    "Q": "Queen", "q": "Queen",
    "R": "Rook", "r": "Rook",
    "B": "Bishop", "b": "Bishop",
    "N": "Knight", "n": "Knight",
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
    disambig_file: str | None = None,
    disambig_rank: str | None = None,
) -> Position | None:
    """Encontra qual peça deve se mover para target_pos.

    Busca todas as peças do jogador atual que podem chegar a target_pos.
    Se múltiplas peças podem chegar, usa a desambiguação (coluna e/ou fileira)
    para distinguir. Se apenas uma peça pode chegar, retorna ela.

    Args:
        board: Tabuleiro atual.
        target_pos: Posição de destino.
        piece_class_name: Nome da classe da peça (ex: "Knight").
            Se None, busca peões.
        color: Cor da peça que está jogando.
        disambig_file: Coluna de desambiguação (ex: "d" em Ndf3).
        disambig_rank: Fileira de desambiguação (ex: "1" em R1d3).

    Returns:
        Position da peça de origem ou None.
    """
    candidates: list[Position] = []

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
                candidates.append(pos)

    # Se não há candidatos, retornar None
    if not candidates:
        return None

    # Se há desambiguação, filtrar
    if disambig_file is not None or disambig_rank is not None:
        filtered: list[Position] = []
        for pos in candidates:
            # Verificar coluna de desambiguação
            if disambig_file is not None:
                col_letter = chr(ord("a") + pos.col)
                if col_letter != disambig_file:
                    continue
            # Verificar fileira de desambiguação
            if disambig_rank is not None:
                rank = str(8 - pos.row)
                if rank != disambig_rank:
                    continue
            filtered.append(pos)
        if filtered:
            return filtered[0]
        return None

    # Sem desambiguação — se há exatamente 1 candidato, retorna
    if len(candidates) == 1:
        return candidates[0]

    # Múltiplos candidatos e sem desambiguação — rejeitar
    # O jogador precisa usar desambiguação (Ndf3, Nef3, R1d3, Rcd3)
    return None


def parse_move_notation(
    notation: str,
    game: "Game",
) -> tuple[Position, Position, str] | None:
    """Parseia uma notação PGN e retorna (origem, destino, sufixo).

    Suporta apenas notação algébrica padrão internacional:
    - "e4" -> peão avança para e4
    - "Nf3" -> Cavalo para f3
    - "Bc4" -> Bispo para c4
    - "Qh5" -> Rainha para h5
    - "Rh1" -> Torre para h1
    - "Ke2" -> Rei para e2
    - "exd5" -> peão em e captura em d5
    - "Nxf3" -> Cavalo captura em f3
    - "O-O" -> roque curto
    - "O-O-O" -> roque longo
    - "e8=Q" -> promoção de peão
    - Sufixos "+" (xeque) e "#" (xeque-mate) são obrigatórios quando aplicável

    Args:
        notation: String com a notação do movimento.
        game: Jogo atual para contexto (turno, tabuleiro).

    Returns:
        Tuple (origem, destino, sufixo) ou None se não conseguir parsear.
        O sufixo é "+" ou "#" se o jogador digitou, ou "" se não digitou.
    """
    notation = notation.strip()
    if not notation:
        return None

    # Extrair sufixo informativo "+" e "#"
    suffix = ""
    if notation.endswith("#"):
        suffix = "#"
    elif notation.endswith("+"):
        suffix = "+"
    clean = notation[:len(notation) - len(suffix)] if suffix else notation
    clean = clean.strip()
    if not clean:
        return None

    board = game.board
    color = game.player_turn

    # Roque curto: "O-O"
    if clean.upper() == "O-O":
        result = _parse_castling(board, color, kingside=True)
        return result + (suffix,) if result else None

    # Roque longo: "O-O-O"
    if clean.upper() == "O-O-O":
        result = _parse_castling(board, color, kingside=False)
        return result + (suffix,) if result else None

    # Promoção de peão com captura: "exd8=Q"
    capture_promotion_match = re.match(r"^([a-h])x([a-h][1-8])=([KQRNBkqrnb])$", clean)
    if capture_promotion_match:
        origin_file = capture_promotion_match.group(1)
        target = parse_position(capture_promotion_match.group(2))
        if target is None:
            return None
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
                return (pos, target, suffix)
        return None

    # Promoção de peão: "e8=Q"
    promotion_match = re.match(r"^([a-h][1-8])=([KQRNBkqrnb])$", clean)
    if promotion_match:
        target = parse_position(promotion_match.group(1))
        if target is None:
            return None
        # Encontrar peão que pode chegar ao destino
        origin = _find_moving_piece(board, target, None, color)
        if origin:
            return (origin, target, suffix)
        return None

    # Notação com captura de peão: "exd5"
    capture_match = re.match(r"^([a-h])x([a-h][1-8])$", clean)
    if capture_match:
        origin_file = capture_match.group(1)
        target = parse_position(capture_match.group(2))
        if target is None:
            return None

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
                return (pos, target, suffix)
        return None

    # Notação de peça com captura e desambiguação: "Nxf3", "Nfxd5", "N1xd5", "Nfxd5"
    # Desambiguação pode ser coluna (a-h), fileira (1-8), ou ambos
    piece_capture_match = re.match(
        r"^([KQRBNkqrnb])([a-h]?[1-8]?)x([a-h][1-8])$", clean
    )
    if piece_capture_match:
        piece_letter = piece_capture_match.group(1)
        disambig = piece_capture_match.group(2)
        target = parse_position(piece_capture_match.group(3))
        if target is None:
            return None

        piece_class_name = PIECE_LETTER_MAP.get(piece_letter)
        if piece_class_name is None:
            return None

        # Extrair desambiguação
        disambig_file = None
        disambig_rank = None
        if disambig:
            if disambig[0].isalpha():
                disambig_file = disambig[0]
            if len(disambig) > 1 and disambig[-1].isdigit():
                disambig_rank = disambig[-1]
            elif len(disambig) == 1 and disambig[0].isdigit():
                disambig_rank = disambig[0]

        origin = _find_moving_piece(
            board, target, piece_class_name, color, disambig_file, disambig_rank
        )
        if origin:
            return (origin, target, suffix)
        return None

    # Notação curta de peça com desambiguação: "Nf3", "Ndf3", "N1f3", "N1df3"
    # Só aceita se NÃO é captura (captura exige "Nxf3")
    piece_short_match = re.match(
        r"^([KQRBNkqrnb])([a-h]?[1-8]?)([a-h][1-8])$", clean
    )
    if piece_short_match:
        piece_letter = piece_short_match.group(1)
        disambig = piece_short_match.group(2)
        target = parse_position(piece_short_match.group(3))
        if target is None:
            return None

        piece_class_name = PIECE_LETTER_MAP.get(piece_letter)
        if piece_class_name is None:
            return None

        # Verificar se há peça no destino — se sim, exige notação de captura
        piece_at_target = board.piece_at(target)
        if piece_at_target is not None:
            # Há peça no destino — não aceitar "Nf3", exige "Nxf3"
            return None

        # Extrair desambiguação
        disambig_file = None
        disambig_rank = None
        if disambig:
            if disambig[0].isalpha():
                disambig_file = disambig[0]
            if len(disambig) > 1 and disambig[-1].isdigit():
                disambig_rank = disambig[-1]
            elif len(disambig) == 1 and disambig[0].isdigit():
                disambig_rank = disambig[0]

        origin = _find_moving_piece(
            board, target, piece_class_name, color, disambig_file, disambig_rank
        )
        if origin:
            return (origin, target, suffix)
        return None

    # Notação curta de peão: "e4"
    # Só aceita se NÃO é captura (captura exige "exd5")
    pawn_short_match = re.match(r"^([a-h])([1-8])$", clean)
    if pawn_short_match:
        target = parse_position(pawn_short_match.group(0))
        if target is None:
            return None

        # Verificar se há peça no destino — se sim, exige notação de captura
        piece_at_target = board.piece_at(target)
        if piece_at_target is not None:
            # Há peça no destino — não aceitar "e4", exige "exd5"
            return None

        origin = _find_moving_piece(board, target, None, color)
        if origin:
            return (origin, target, suffix)
        return None

    return None


def _parse_castling(
    board: "Board", color: Color, kingside: bool
) -> tuple[Position, Position] | None:
    """Parseia movimento de roque.

    Args:
        board: Tabuleiro atual.
        color: Cor da peça que está jogando.
        kingside: True para roque curto (O-O), False para roque longo (O-O-O).

    Returns:
        Tuple (origem do rei, destino do rei) ou None.
    """
    # Encontrar o rei
    from simple_chess.pieces.king import King
    king_pos = board.find_king(color)
    if king_pos is None:
        return None

    # Rei deve estar na posição inicial
    if color == Color.WHITE:
        if king_pos.row != 7 or king_pos.col != 4:
            return None
        if kingside:
            return (Position(7, 4), Position(7, 6))
        else:
            return (Position(7, 4), Position(7, 2))
    else:  # BLACK
        if king_pos.row != 0 or king_pos.col != 4:
            return None
        if kingside:
            return (Position(0, 4), Position(0, 6))
        else:
            return (Position(0, 4), Position(0, 2))
