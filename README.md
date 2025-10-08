# Discord OAuth2 認証パネル BOT

![Python](https://img.shields.io/badge/Python-3.11+-blue)  
![License](https://img.shields.io/badge/License-MIT-green)

---

## 概要

このBOTは **Discord OAuth2 認証パネル** を簡単に作成できるBOTです。  
ユーザーがDiscordでOAuth認証を行うことで、指定されたロールを自動付与することができます。  

✅ **特徴**  
- 複数スコープ対応（identify, email, guilds など）  
- 認証情報をWebhookで安全に送信  
- 利用規約・ライセンス確認モーダル付き認証ページ  
- 自動でユーザーにロールを付与  
- Webサーバー統合でOAuth2フローを簡単に管理  

---

## 機能

1. **認証パネル作成**  
   `/panel_create` スラッシュコマンドで認証パネルを作成できます。  
   パネル作成時に以下を指定可能：
   - 埋め込みタイトル / 説明
   - 付与するロール
   - OAuthスコープ（複数可）
   - ログ送信用Webhookチャンネル
   - カスタムリダイレクトURL（任意）
   - 埋め込み画像・色のカスタマイズ  

2. **OAuth2 認証フロー**  
   - ユーザーは認証ページで同意チェックを行い、ボタンをクリックして認証  
   - 認証完了後、ロール自動付与 & Webhookにユーザー情報を送信  

3. **情報送信**  
   - OAuthで取得したユーザー情報を `info.txt` にまとめてWebhook送信  

4. **モーダル・規約機能**  
   - 利用規約やライセンス情報をモーダルで表示  
   - 同意チェックを入れないと認証ボタンは有効になりません  

---

## 対応スコープ

- `identify`：ユーザー情報（ID, 名前, アバター）  
- `email`：メールアドレス  
- `connections`：外部連携情報  
- `guilds`：参加サーバー一覧  
- `guilds.join`：サーバーに参加させる  
- `guilds.members.read`：サーバーメンバー情報  

※ 複数スコープは `,` で区切って指定可能  

---

## 環境変数

BOT起動前に以下を設定してください：

```bash
export BOT_TOKEN="あなたのBOTトークン"
export CLIENT_ID="アプリケーションID"
export CLIENT_SECRET="クライアントシークレット"
export BASE_URL="https://your-domain.com"
export PORT=8080
````

※ Windows PowerShell の場合：

```powershell
$env:BOT_TOKEN="あなたのBOTトークン"
```

---

## インストール

1. リポジトリをクローン

```bash
git clone https://github.com/yourusername/discord-oauth-panel.git
cd discord-oauth-panel
```

2. 必要なPythonパッケージをインストール

```bash
pip install -r requirements.txt
```

3. 環境変数を設定
4. BOTを起動

```bash
python bot.py
```

---

## 使用方法

### 認証パネル作成例

```txt
/panel_create
title: サーバー認証
description: Discord OAuth2認証でロール付与
role: @Verified
scope: identify,email,guilds
webhook_channel: #verification-log
use_custom_redirect: false
```

作成後、指定したチャンネルに認証ボタンが表示されます。

---

## 貢献方法

1. リポジトリをFork
2. 新しいブランチで開発

```bash
git checkout -b feature/新機能名
```

3. コードを修正 / 機能追加
4. PR（プルリクエスト）を作成

### コード規約

* Python 3.11+ を使用
* `black` または `autopep8` でフォーマット
* コメントを丁寧に書くこと

---

## ライセンス

MIT License
詳細は [LICENSE](LICENSE) を参照

---

## 注意事項

* 本BOTは **自己責任** で使用してください
* 不正アクセスやスパム目的での使用は禁止します
* OAuthで取得した情報は安全に管理してください

---

## 開発者

ゆっくりーむ (Yukkurim)

