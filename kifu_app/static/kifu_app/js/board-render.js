/**
 * 一覧画面（トップ・検索・マイページ）用の小さい盤面プレビューを描画する。
 * コントロールUIを持たないWGo.Playerを使い、指定手数（なければ最終局面）まで進めて表示する。
 */
function renderMiniBoard(containerId, sgf, moveNumber, size) {
  const container = document.getElementById(containerId);
  if (!container || !sgf) return;

  const boardSize = size || 85;
  const player = new WGo.Player({
    sgf: sgf,
    move: 0,
    board: {
      stoneHandler: WGo.Board.drawHandlers.NORMAL,
      width: boardSize,
      height: boardSize,
    },
  });

  if (moveNumber !== null && moveNumber !== undefined) {
    player.goTo(moveNumber);
  } else {
    player.last();
  }

  container.appendChild(player.element);
}
