var player; // グローバルで定義

/**
 * 1. 【最強版】手数を取得するための共通関数
 * WGoが生成したHTML（input.wgo-player-mn-value）から直接数字を読み取ります。
 * これにより、表示と内部データの乖離を完全に防ぎます。
 */
function getCurrentMove() {
    // 画面上の「手数入力欄」を直接参照
    const moveInput = document.querySelector(".wgo-player-mn-value");
    if (moveInput) {
        return parseInt(moveInput.value) || 0;
    }

    // バックアップ：HTMLがまだ生成されていない場合などはオブジェクトから取得
    if (player) {
        if (player.path && typeof player.path.m === 'number') return player.path.m;
        if (player.player && player.player.kifuReader) return player.player.kifuReader.path.m;
    }
    return 0;
}

/**
 * 2. 入力フォームの表示切替
 */
window.toggleInput = function(show) {
    const header = document.getElementById("header");
    const closeBtn = document.getElementById("close-btn");
    const fab = document.getElementById("fab-message");
    const inputField = document.getElementById("comment-input");
    const body = document.body;
    const tabs = document.getElementById("tabs");
    const bottom = document.getElementById("bottom");
    const nav = document.getElementById("nav");
    const inputArea = document.getElementById("input-area");


    if (show) {
        // 表示されるタイミングで最新の手数を取得
        const currentMove = getCurrentMove(); 
        
        header.style.display = "none";
        tabs.style.display = "none";
        bottom.style.display = "none";

        inputArea.style.display = "block";
        closeBtn.style.display = "flex";
        fab.style.display = "none";
        nav.style.display = "none";
        body.classList.add("is-typing");
        
        // 取得した手数を即座に反映
        inputField.value = `@ ${currentMove} `;
        
        setTimeout(() => {
            inputField.focus();
            // カーソルを末尾へ移動
            inputField.setSelectionRange(inputField.value.length, inputField.value.length);
        }, 100);
    } else {
        header.style.display = "flex";
        inputArea.style.display = "none";
        closeBtn.style.display = "none";
        fab.style.display = "flex";
        nav.style.display = "flex";
        tabs.style.display = "flex";
        bottom.style.display = "flex";
        body.classList.remove("is-typing");
    }
};

/**
 * 3. 初期化と連動設定
 */
document.addEventListener("DOMContentLoaded", function() {
    const playerElement = document.getElementById("wgo-player");
    const inputField = document.getElementById("comment-input");

    if (playerElement) {
        // プレイヤーの初期化（テンプレートから渡されたSGF_DATAを優先使用）
        const sgfToLoad = (typeof SGF_DATA !== "undefined" && SGF_DATA)
            ? SGF_DATA
            : "(;GM[1]FF[4]SZ[19];B[pd];W[dp];B[pp];W[dd];B[pj];W[nc];B[qf];W[pb];B[qc];W[ld])";

        player = new WGo.BasicPlayer(playerElement, {
            sgf: sgfToLoad,
            move: 0,
            board: { stoneHandler: WGo.Board.drawHandlers.NORMAL }
        });

        // 【連動 A】盤を動かした時に、コメントリストと入力欄の数字を同期
        player.addEventListener("update", function(e) {
            // イベントから直接、またはHTML表示から手数を特定
            const m = getCurrentMove();
            
            // コメント強調（data-move属性と一致するものをハイライト）
            document.querySelectorAll('.comment').forEach(c => {
                c.classList.toggle('active-move', parseInt(c.getAttribute('data-move')) === m);
            });

            // コメント入力中であれば、先頭の「@ 数字」部分を盤に合わせてリアルタイム更新
            if (document.body.classList.contains("is-typing") && inputField) {
                const currentText = inputField.value;
                const newText = currentText.replace(/^@ \d+ /, `@ ${m} `);
                if (currentText !== newText) {
                    inputField.value = newText;
                }
            }
        });
    }

    // 【連動 B】コメント入力欄の「@ 数字」を書き換えた時、盤をその手数へ飛ばす
    if (inputField) {
        inputField.addEventListener("input", function(e) {
            const match = e.target.value.match(/^@ (\d+) /);
            if (match && player) {
                const targetMove = parseInt(match[1]);
                const currentMove = getCurrentMove();

                // 現在の表示手数が入力された数字と異なる場合のみ移動命令を出す
                if (currentMove !== targetMove) {
                    if (typeof player.goTo === "function") {
                        player.goTo(targetMove);
                    } else if (player.player && player.player.goTo) {
                        player.player.goTo(targetMove);
                    }
                }
            }
        });
    }

    // タブ切替
    window.switchTab = function(index) {
        const tabs = document.querySelectorAll(".tab");
        const contents = document.querySelectorAll(".tab-content");
        tabs.forEach((t, i) => {
            t.classList.toggle("active", i === index);
            contents[i].classList.toggle("active", i === index);
        });
        const fab = document.getElementById("fab-message");
        if (fab) fab.style.display = (index === 0) ? "flex" : "none";
    };

    // コメント初期ソート
    const container = document.getElementById('comment-area');
    if (container) {
        const comments = Array.from(container.getElementsByClassName('comment'));
        comments.sort((a, b) => (parseInt(a.getAttribute('data-move')) || 0) - (parseInt(b.getAttribute('data-move')) || 0));
        comments.forEach(c => container.appendChild(c));
    }

    // すべてのチップに対して、クリックイベントを強制的に再設定する
    document.querySelectorAll('.move-chip').forEach(chip => {
        chip.addEventListener('click', function() {
            // テキストから数字を抽出（"@ 10" から "10" を取る）
            const num = this.innerText.replace(/[^0-9]/g, '');
            window.goToMove(num);
        });
    });
});

/**
 * チップをクリックした時の動作
 * 入力欄の数字を書き換えて、既存の連動ロジックをキックする
 */
window.goToMove = function(moveNum) {
    const inputField = document.getElementById("comment-input");
    const inputFieldDisplay = getComputedStyle(inputField).display;

    if (!inputField) return;

    // 2. 手動で input イベントを発生させて、
    //    既に正常に動いている「入力欄 → 碁盤」の連動ロジックを再利用する
    const event = new Event('input', { bubbles: true });
    inputField.dispatchEvent(event);

    if (inputFieldDisplay === 'none') return;

    // 1. 入力欄の数字だけをスマートに書き換える
    const currentText = inputField.value;
    const newPrefix = `@ ${moveNum} `;
    
    if (currentText.match(/^@ \d+ /)) {
        inputField.value = currentText.replace(/^@ \d+ /, newPrefix);
    } else {
        inputField.value = newPrefix + currentText;
    }
    
    // 盤の縮小（toggleInput）は呼び出さない
};


const textarea = document.getElementById("comment-input");
const inputArea = document.getElementById("input-area");

textarea.addEventListener("input", function () {  
  const inputField = document.getElementById("input-area");
  console.log(inputField.style.display);
  if (inputField.style.display === 'none') return;

  this.style.height = "40px"; // いったんリセット
  this.style.height = this.scrollHeight + "px"; // 内容に合わせる
});