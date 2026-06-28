/**
 * ドットマトリクス風の文字描画
 * 5x7ドットのビットマップフォントで、1文字ずつ<div>のドット集合を組み立てる。
 * オフのドットも小さく描画することで「黒ドット背景」を表現する。
 */
const DOT_FONT = {
  T: ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
  O: ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
  P: ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
  S: ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
  E: ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
  A: ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
  R: ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
  C: ['01111', '10000', '10000', '10000', '10000', '10000', '01111'],
  H: ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
  ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'],
};

function renderDotText(container, text) {
  container.innerHTML = '';
  container.classList.add('dot-text');

  for (const ch of text.toUpperCase()) {
    const bitmap = DOT_FONT[ch] || DOT_FONT[' '];
    const charEl = document.createElement('div');
    charEl.className = 'dot-char';

    bitmap.forEach((row) => {
      const rowEl = document.createElement('div');
      rowEl.className = 'dot-row';
      for (const bit of row) {
        const dotEl = document.createElement('span');
        dotEl.className = bit === '1' ? 'dot dot-on' : 'dot dot-off';
        rowEl.appendChild(dotEl);
      }
      charEl.appendChild(rowEl);
    });

    container.appendChild(charEl);
  }
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.dot-text-container').forEach(function(el) {
    renderDotText(el, el.dataset.text || '');
  });
});
