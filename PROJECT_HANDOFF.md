# igovote プロジェクト引き継ぎメモ

このドキュメントは、claude.ai での設計・実装の議事録です。
Claude Code で開発を継続する際に、このファイルをコンテキストとして読み込んでください。

## プロジェクト概要

囲碁棋譜を仲間にシェアし、コメントをもらったり検索したりできる囲碁SNSアプリ。

## 想定画面（第一段階）

| 画面 | 状態 |
|---|---|
| トップ | 実装済み（最新の公開棋譜一覧を表示） |
| 棋譜作成 | 実装済み |
| 棋譜詳細 | 実装済み（WGo.jsで棋譜再生、着手連動コメント） |
| 検索結果 | 実装済み（タグ検索・キーワード検索） |
| マイページ | 実装済み（自分の投稿一覧） |
| ログイン | 実装済み |
| ユーザー登録 | 実装済み（メール確認なし） |

## 技術スタック

- バックエンド: Django 4.2.29 / Python 3.9.21
- DB: SQLite（開発時点）
- フロントエンド: Django テンプレート（HTML/CSS） + WGo.js（棋譜ビューワ）
- 認証: Django標準のセッション認証（カスタムUserモデル使用）

## DB設計の決定事項

- `User`: Django標準を拡張（avatar, bio を追加）
- `Kifu`: 棋譜本体。`sgf_data` は **SGFをそのまま文字列で保存**（ばらして格納するメリットがないと判断）
- `Kifu.visibility`: 現在は `public` / `private` の2択。**将来グループ単位の公開範囲を追加する予定**なので、設計はその拡張を見込んだ形にしておく
- `Comment`: 棋譜の特定の着手番号（`move_number`）に紐づく。1コメント=1着手（複数着手への同時コメントは不要との回答）
- `CommentLike` / `KifuLike`: いいね機能。コメント・棋譜それぞれに必要
- **将来拡張予定（今は未実装）**: コメントに対する「参考図」機能。投稿者が57手目などの局面に対し、❶②❸のような自分の着手を複数手分付与できる機能（`CommentVariation` のようなテーブルを後で追加する想定）

## 棋譜削除・公開範囲変更

- 投稿者本人のみ棋譜を削除できる
- 公開範囲は投稿後にも変更可能（`kifu_visibility` ビューで実装済み）

## サーバー環境

- ホスト: test.igovote.net （SSHポート 15069、ユーザー okuda）
- 旧 `myapp.service`（FastAPI/uvicorn用に作られたsystemdサービス）は **廃止・使用しない**
- 現在は `nohup python manage.py runserver 0.0.0.0:8000 &` で簡易運用中
- 本番URLは現状 `http://test.igovote.net:8000/`（HTTP、SSL未設定）

## Git / デプロイ運用の方針

- ブランチ運用: 簡易版Git-flow方式を採用（`release/*` `hotfix/*` は省略、将来必要になれば追加）
  - `master`: 本番。直接pushは禁止、PR経由でのみマージ（GitHub側でブランチ保護ルール設定済み）
  - `develop`: 開発統合ブランチ。保護ルールなし、直接pushも可
  - `feature/*`: 個別機能ブランチ。`develop`から分岐し、PRで`develop`にマージ
  - リリース時は `develop` → `master` にPRでマージ
  - 旧 `main` ブランチは `master` にリネーム済み（GitHub上のデフォルトブランチも `master` に変更）
- GitHubリポジトリ作成 → サーバー・Windows双方からpush/pull する運用に移行中
- 将来的に GitHub Actions で自動デプロイ・自動テスト（pytest）・AIコードレビューを組み込む予定（優先度は低め、後回しで合意済み）
- デプロイ方式の草案（`myapp.service` が直った場合や正式運用に切り替える際の参考用）:
  - サーバー側で `git pull` → `migrate` → プロセス再起動、という流れをGitHub Actionsから実行する想定

## 今後のタスク（優先順）

1. ~~Windows開発環境構築~~ → 完了（Python 3.10.9 / Django 4.2.29 / Node v24.16.0 / Git）
2. ~~サーバー上のコードをGit管理化、GitHubにpush~~ → 完了（リポジトリ: https://github.com/KMOkuda/igovote ）
3. ~~Windowsにclone、ローカルでも動作確認~~ → 完了（ポート8000がWindowsで使用できないため、ローカルでは8080番で確認中: `python manage.py runserver 8080`）
4. **Claude Code導入、以後はこちらで実装継続** ← 今ここ
5. ブランチ運用整備（master化・develop作成・保護ルール）→ ローカル/GitHub双方で `master`・`develop` 作成済み。**残作業**: GitHub上のデフォルトブランチを`master`に変更、旧`origin/main`削除、`master`へのブランチ保護ルール設定、サーバー側クローンの追従（手順はこのファイル末尾またはClaude Codeとの作業履歴を参照）
6. UIの仕上げ・残課題の検討（参考図機能、グループ公開範囲など）
7. テスト自動化・CI整備（後回しでOKと合意済み）

## 直近で見つかった不具合・修正履歴

- **棋譜詳細でコメント投稿ができない不具合**：原因は2つ。(1) `script.js` がテンプレートから渡されるSGFデータを使わず、ハードコードされたテスト用SGFを常に表示していた。(2) `SGF_DATA` をDjangoテンプレートで `|safe` のみでJS変数に埋め込んでいたため、SGF内の特殊文字でJS構文エラーが起き、ページ全体のJSが止まっていた。`json_script` テンプレートタグを使う方式に修正し、解消済み。
- **投稿画面のCSSが崩れて見える不具合**：コード自体に問題はなく、ブラウザのキャッシュが古いCSSを保持していたことが原因。キャッシュクリアで解消。コード修正不要だった。
- **検証用に渡したサンプルSGFが不正だった**：同じ座標に二度石を置く矛盾したSGFを渡してしまい、`InvalidMoveError` が発生。座標の重複がないか確認済みの新しいサンプルSGFに置き換えて解消。今後SGFサンプルを作る際は重複チェックスクリプトを通すこと。

## サーバー運用に関する補足

- サーバーは `nohup python manage.py runserver 0.0.0.0:8000 &` で起動する。**仮想環境を有効化（`source .venv/bin/activate`）した状態で実行することを忘れずに**（有効化を忘れてDjangoが見つからないエラーになった経緯あり）。
- サーバーのGitリポジトリはGitHub（`KMOkuda/igovote`）と連携済み。現在は `main` ブランチのみで運用中。今後Git-flow的なブランチ運用（feature/develop/release/master）に移行する予定だが、Claude Codeでの実装と並行して整備する。

## 既存コードの所在（claude.ai 側で作成したファイル）

- `models.py`, `admin.py`, `views.py`, `auth_views.py`, `urls.py`（kifu_app配下）
- `settings.py`, `urls.py`（myproject配下、サーバーには手動反映済み）
- テンプレート9画面 + static一式（`kifu_app_templates.zip` として提供済み、サーバーに反映済み）
- `.gitignore`（Django用、提供済み）
- `deploy.yml`（GitHub Actions用、nohup運用に合わせて修正済み。`.github/workflows/` に配置予定）

## 元のモック（参考）

最初に渡されたHTMLモックは `kifu_detail.html` と `kifu_search.html` の2枚。
WGo.jsとの連動ロジック（`script.js`、着手番号とコメントのアクティブ表示連動）は元のモックの実装を活かして引き継いでいる。
