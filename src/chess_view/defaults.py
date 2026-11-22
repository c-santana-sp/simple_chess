"""Configurações padrão da visualização Rich."""

from simple_chess.color import Color


# Configurações padrão — fallback se config.json não existir
DEFAULT_CONFIG = {
    "invert_board_on_black_turn": True,
    "board": {
        "cell_width": 4,
        "light_square_color": "#3b5e3b",
        "dark_square_color": "#2d4a2d",
        "selected_square_color": "#b8860b",
        "selected_text_color": "black",
        "valid_move_color": "#3a7d44",
        "piece_text_color": "white",
        "piece_bold": True,
    },
    "markers": {
        "selected": "★",
        "valid_move": "·",
    },
    "sidebar": {
        "width": 20,
        "border_style": "dim",
        "captured_title_color": "yellow",
        "history_title_color": "cyan",
    },
    "command_line": {
        "prompt_color": "dim white",
        "input_color": "cyan",
        "cursor": "█",
    },
    "title": {
        "text": "♔ Xadrez",
        "style": "bold",
    },
    "piece_symbols": {
        "King_WHITE": "♚",
        "Queen_WHITE": "♛",
        "Rook_WHITE": "♜",
        "Bishop_WHITE": "♝",
        "Knight_WHITE": "♞",
        "Pawn_WHITE": "♟",
        "King_BLACK": "♔",
        "Queen_BLACK": "♕",
        "Rook_BLACK": "♖",
        "Bishop_BLACK": "♗",
        "Knight_BLACK": "♘",
        "Pawn_BLACK": "♙",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Mescla dois dicionários recursivamente."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _deep_copy(d: dict) -> dict:
    """Copia profunda simples de dicionário."""
    result = {}
    for key, value in d.items():
        result[key] = value.copy() if isinstance(value, dict) else value
    return result


def _build_piece_symbols(config: dict) -> dict[tuple[str, Color], str]:
    """Constrói o mapeamento de peças a partir das configurações."""
    symbols_cfg = config.get("piece_symbols", {})
    symbols: dict[tuple[str, Color], str] = {}
    for key, symbol in symbols_cfg.items():
        parts = key.rsplit("_", 1)
        if len(parts) == 2:
            piece_name, color_str = parts
            color = Color.WHITE if color_str == "WHITE" else Color.BLACK
            symbols[(piece_name, color)] = symbol
    return symbols
